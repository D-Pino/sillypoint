import os
from typing import Any

import duckdb
import pandas as pd
from database.models import Delivery as DeliveryDB
from database.models import Game as GameDB
from database.models import Player as PlayerDB
from pydantic import TypeAdapter, ValidationError
from sqlalchemy import select
from validation.models import Delivery as DeliveryVal

from cowcorner.common import SessionLocal

DATA_DIR = f"{os.getenv('REPO_ROOT')}/common/data"


def get_deliveries_to_ingest(num_deliveries: int = 20_000) -> pd.DataFrame:
    """I don't have a real source of data, so this function gets random deliveries from a
    local csv I have with ~2M deliveries and returns that.

    There's no good reason to use duckdb for this, I just wanted to try it out"""

    odata_raw: duckdb.DuckDBPyRelation = duckdb.read_csv(  # noqa: F841
        f"{DATA_DIR}/odata_full.csv",
        ignore_errors=True,  # necessary because this data is not clean
    )
    return duckdb.sql(
        f"SELECT * FROM odata_raw ORDER BY random() LIMIT {num_deliveries}"
    ).df()


def validate_delivery_batch(delivery_batch: pd.DataFrame) -> list[DeliveryVal]:
    # We validate by batch because it's faster than iterating. If this batch validation
    # fails, we fall back to iterating and validating one-by-one so we can salvage the
    # good deliveries in the batch
    delivery_list_model = TypeAdapter(list[DeliveryVal])
    deliveries = delivery_batch.to_dict("records")
    try:
        return delivery_list_model.validate_python(deliveries)
    except ValidationError as e:
        print(f"Batch validation failed! Will validate deliveries one-by-one: {e}")
        return validate_deliveries(deliveries)


def validate_deliveries(deliveries: list[dict[str, Any]]) -> list[DeliveryVal]:
    valid_deliveries = []
    for delivery in deliveries:
        try:
            valid_deliveries.append(DeliveryVal.model_validate(delivery))
        except ValidationError:
            print(f"Delivery failed validation: {delivery}")
    print(
        f"{len(valid_deliveries)} deliveries out of {len(deliveries)} passed validation"
    )
    return valid_deliveries


def ingest_delivery_batch(delivery_batch: pd.DataFrame):
    # Validate the raw delivery data
    valid_deliveries = validate_delivery_batch(delivery_batch=delivery_batch)
    print(f"Found {len(valid_deliveries)} valid deliveries")

    # Validated deliveries are useful later to build our db models
    valid_delivery_map = {d.source_id: d for d in valid_deliveries}
    # Filter out invalid deliveries from our data
    delivery_batch = delivery_batch[
        delivery_batch["id"].isin(valid_delivery_map.keys())
    ]

    # Add deliveries and related models to our database.
    # We technically iterate over the dataframe twice, which in theory is inefficient, but this
    # allows us to batch our db inserts, which ends up impacting efficiency much more than df iteration
    with SessionLocal() as session:
        # TODO: dismissedPlayer
        # TODO: teams
        # TODO: grounds

        # Get list of players referenced in this batch of deliveries
        # NB: could also upsert with on_conflict_do_nothing, but I like this approach because of the increased visibility
        player_names = pd.unique(
            pd.concat([delivery_batch["bowler"], delivery_batch["batsman"]])
        )
        print(f"Found {len(player_names)} players in total in this delivery batch")

        # Get list of these players that we already have in the database
        stmt = select(PlayerDB).where(PlayerDB.name.in_(player_names))
        existing_players = {p.name: p for p in session.scalars(stmt)}

        # Get list of the new players to be added, and add them to the db
        players_to_add = [
            PlayerDB(name=name)
            for name in set(player_names) - set(existing_players.keys())
        ]
        session.add_all(players_to_add)
        print(f"Added {len(players_to_add)} new players to database")

        # We keep this lookup of players so that we can get players later on when adding deliveries,
        # without having to make extra unnecessary calls to the database
        player_lookup = {**existing_players, **{p.name: p for p in players_to_add}}

        # For handling adding of games, we repeat the exact same pattern from players
        game_batch = delivery_batch.drop_duplicates("fixtureId")[
            ["fixtureId", "matchDate", "competition", "format"]
        ]
        game_ids = game_batch["fixtureId"].to_list()
        print(f"Found {len(game_ids)} games in total in this delivery batch")

        stmt = select(GameDB).where(GameDB.source_id.in_(game_ids))
        existing_games = {g.source_id: g for g in session.scalars(stmt)}

        games_to_add = [
            GameDB(
                source_id=game.fixtureId,
                game_date=game.matchDate.date()
                if not pd.isna(game.matchDate)
                else None,
                competition=game.competition,
                game_format=game.format,
            )
            for game in game_batch.itertuples()
            if game.fixtureId in set(game_ids) - set(existing_games.keys())
        ]
        session.add_all(games_to_add)
        print(f"Added {len(games_to_add)} new games to database")

        game_lookup = {**existing_games, **{g.source_id: g for g in games_to_add}}

        # TODO: handle duplicates here, either check like above or set on_conflict_do_nothing
        deliveries_to_add = [
            DeliveryDB(
                bowler=player_lookup[delivery_raw.bowler],
                batsman=player_lookup[delivery_raw.batsman],
                game=game_lookup[delivery_raw.fixtureId],
                **valid_delivery_map[delivery_raw.id].model_dump(),
            )
            for delivery_raw in delivery_batch.itertuples()
        ]
        session.add_all(deliveries_to_add)

        session.commit()
    print(f"Ingested {len(deliveries_to_add)} deliveries")


def main():
    # Get data to be ingested
    delivery_batch: pd.DataFrame = get_deliveries_to_ingest()
    print(f"Found {len(delivery_batch)} deliveries to ingest")
    # Ingest batch
    # TODO: chunking
    ingest_delivery_batch(delivery_batch=delivery_batch)


if __name__ == "__main__":
    main()
