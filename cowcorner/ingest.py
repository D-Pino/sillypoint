"""
This code isn't as modular or as cleanly organized as it could be, namely:

 - I could separate data retrieval, validation, and database persistence to different functions
 - I could have individual functions to validate and ingest a single delivery, game, player, etc


This is an intentional decision taken in the interest of optimizing performance. By working
with the data in batches, we gain a lot of speed in validation and (more importantly) in database
inserts.

Another tradeoff made here is that I check the database for existing entities and only insert what
isn't already there. Technically, it would be quicker to naively insert all data and let the
database handle ignoring duplicates with on_conflict_do_nothing. In my opinion, doing it the "smart"
way is better for visibility and understanding the system.

Both these decisions (on code organization and on smart vs naive inserts) could go either way, and
the alternatives for each are valid.

"""

import argparse
import os
from typing import Any

import duckdb
import pandas as pd
from cowcorner.common import SessionLocal
from pydantic import TypeAdapter, ValidationError
from sqlalchemy import select

from database.models import Delivery as DeliveryDB
from database.models import Game as GameDB
from database.models import Player as PlayerDB
from validation.models import Delivery as DeliveryVal

DATA_DIR = f"{os.getenv('REPO_ROOT')}/common/data"


def get_deliveries_to_ingest(num_deliveries: int) -> pd.DataFrame:
    """I don't have a real source of data, so this function gets random deliveries from a
    local csv I have with ~2M deliveries and returns that.

    There's no good reason to use duckdb for this, I just wanted to try it out"""

    odata_raw: duckdb.DuckDBPyRelation = duckdb.read_csv(  # noqa: F841
        f"{DATA_DIR}/odata_full.csv",
        ignore_errors=True,  # necessary because this data is not clean
    )
    return duckdb.sql(f"SELECT * FROM odata_raw ORDER BY random() LIMIT {num_deliveries}").df()


def validate_delivery_batch(delivery_batch: pd.DataFrame) -> list[DeliveryVal]:
    # We validate by batch because it's faster than iterating. If this batch validation
    # fails, we fall back to iterating and validating one-by-one so we can salvage the
    # good deliveries in the batch
    delivery_list_model = TypeAdapter(list[DeliveryVal])
    deliveries = delivery_batch.to_dict("records")
    try:
        return delivery_list_model.validate_python(deliveries)
    except ValidationError as e:
        print(f"Batch validation failed: {e} Will validate deliveries one-by-one")
        return validate_deliveries(deliveries)


def validate_deliveries(deliveries: list[dict[str, Any]]) -> list[DeliveryVal]:
    valid_deliveries = []
    for delivery in deliveries:
        try:
            valid_deliveries.append(DeliveryVal.model_validate(delivery))
        except ValidationError:
            print(f"Delivery failed validation: {delivery}")
    print(f"{len(valid_deliveries)} deliveries out of {len(deliveries)} passed validation")
    return valid_deliveries


def ingest_delivery_batch(delivery_batch: pd.DataFrame) -> int:
    # Validate the raw delivery data
    valid_deliveries = validate_delivery_batch(delivery_batch=delivery_batch)
    print(f"Found {len(valid_deliveries)} valid deliveries")

    if len(valid_deliveries) == 0:
        return

    # Validated deliveries are useful later to build our db models
    valid_delivery_map = {d.source_id: d for d in valid_deliveries}
    # Filter out the invalid deliveries from our raw data
    delivery_batch = delivery_batch[delivery_batch["id"].isin(valid_delivery_map.keys())]

    # Add deliveries and related models to our database.
    # We technically iterate over the deliveries twice, which in theory is inefficient, but this
    # allows us to batch our db inserts, which ends up impacting efficiency much more than df iteration
    with SessionLocal() as session:
        with session.begin():
            # TODO: dismissedPlayer
            # TODO: teams
            # TODO: grounds

            # Get list of players referenced in this batch of deliveries
            player_names = pd.unique(pd.concat([delivery_batch["bowler"], delivery_batch["batsman"]]))
            print(f"Found {len(player_names)} players in total in this delivery batch")

            # Get list of these players that we already have in the database
            stmt = select(PlayerDB).where(PlayerDB.name.in_(player_names))
            existing_players = {p.name: p for p in session.scalars(stmt)}

            # Get list of the new players to be added, and add them to the db
            players_to_add = [PlayerDB(name=name) for name in set(player_names) - set(existing_players.keys())]
            session.add_all(players_to_add)
            print(f"Added {len(players_to_add)} new players to database")

            # We keep this lookup of players so that we can get players later on when adding deliveries,
            # without having to make extra unnecessary calls to the database
            player_lookup = {**existing_players, **{p.name: p for p in players_to_add}}

            # For handling adding of games, we repeat a similar pattern to players'
            game_data = delivery_batch.drop_duplicates("fixtureId")[["fixtureId", "matchDate", "competition", "format"]]
            game_ids = game_data["fixtureId"].to_list()
            print(f"Found {len(game_ids)} games in total in this delivery batch")

            stmt = select(GameDB).where(GameDB.source_id.in_(game_ids))
            existing_games = {g.source_id: g for g in session.scalars(stmt)}

            games_to_add = [
                GameDB(
                    source_id=game.fixtureId,
                    game_date=game.matchDate.date() if not pd.isna(game.matchDate) else None,
                    competition=game.competition,
                    game_format=game.format,
                )
                for game in game_data.itertuples()
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
    ingested_count = len(deliveries_to_add)
    print(f"Ingested {ingested_count} deliveries")
    return ingested_count


def main():
    parser = argparse.ArgumentParser(description="Run ingestion")
    parser.add_argument(
        "--num-deliveries",
        type=int,
        default=20_000,
        help="Total number of deliveries to fetch (default: 20,000)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of deliveries to process per batch (default: 1,000)",
    )
    args = parser.parse_args()
    delivery_batch: pd.DataFrame = get_deliveries_to_ingest(args.num_deliveries)
    print(f"Found {len(delivery_batch)} deliveries to ingest")

    total_ingested = 0
    num_batchs = (len(delivery_batch) - 1) // args.batch_size + 1

    for batch_idx in range(0, len(delivery_batch), args.batch_size):
        batch = delivery_batch.iloc[batch_idx : batch_idx + args.batch_size]
        batch_number = (batch_idx // args.batch_size) + 1

        total_ingested += ingest_delivery_batch(batch)

        print(f"\nProcessing batch {batch_number}/{num_batchs} ({len(batch)} deliveries)")


if __name__ == "__main__":
    main()
