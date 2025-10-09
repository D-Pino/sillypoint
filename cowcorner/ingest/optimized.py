import argparse

import pandas as pd
from cowcorner.common import SessionLocal
from sqlalchemy import select

from cowcorner.database.models import Delivery as DeliveryDB
from cowcorner.database.models import Game as GameDB
from cowcorner.database.models import Player as PlayerDB
from utils import get_deliveries_to_ingest, validate_delivery_batch


DEFAULT_NUM_DELIVERIES = 20_000
DEFAULT_BATCH_SIZE = 1000


def ingest_delivery_batch(delivery_batch: pd.DataFrame) -> int:
    # Validate the raw delivery data
    valid_deliveries = validate_delivery_batch(delivery_batch=delivery_batch)
    print(f"Found {len(valid_deliveries)} valid deliveries")

    if len(valid_deliveries) == 0:
        return 0

    # Look-up for the valid deliveries
    valid_delivery_map = {d.source_id: d for d in valid_deliveries}
    # Filter out the invalid deliveries from our raw data
    delivery_batch = delivery_batch[delivery_batch["id"].isin(valid_delivery_map.keys())]

    # Add deliveries and related models to our database
    with SessionLocal() as session:
        # TODO: dismissedPlayer
        # TODO: teams
        # TODO: grounds

        # Get list of players referenced in this batch of deliveries
        player_names = pd.unique(values=pd.concat(objs=[delivery_batch["bowler"], delivery_batch["batsman"]]))
        print(f"Found {len(player_names)} players in total in this delivery batch")

        # Get list of these players that we already have in the database
        stmt = select(PlayerDB).where(PlayerDB.name.in_(player_names))
        existing_players = {p.name: p for p in session.scalars(statement=stmt)}

        # Get list of the new players to be added, and add them to the db
        players_to_add = [PlayerDB(name=name) for name in set(player_names) - set(existing_players.keys())]
        session.add_all(instances=players_to_add)
        print(f"Added {len(players_to_add)} new players to database")

        # We keep this lookup of players so that we can get players later on when adding deliveries,
        # without having to make extra unnecessary calls to the database
        player_lookup: dict[str, PlayerDB] = {**existing_players, **{p.name: p for p in players_to_add}}

        # For handling adding of games, we repeat a similar pattern to players
        game_data = delivery_batch.drop_duplicates("fixtureId")[["fixtureId", "matchDate", "competition", "format"]]
        game_ids = game_data["fixtureId"].to_list()
        print(f"Found {len(game_ids)} games in total in this delivery batch")

        stmt = select(GameDB).where(GameDB.source_id.in_(game_ids))
        existing_games = {g.source_id: g for g in session.scalars(statement=stmt)}

        games_to_add = [
            GameDB(
                source_id=game.fixtureId,
                game_date=game.matchDate.date() if not pd.isna(obj=game.matchDate) else None,
                competition=game.competition,
                game_format=game.format,
            )
            for game in game_data.itertuples()
            if game.fixtureId in set(game_ids) - set(existing_games.keys())
        ]
        session.add_all(instances=games_to_add)
        print(f"Added {len(games_to_add)} new games to database")

        game_lookup: dict[str, GameDB] = {**existing_games, **{g.source_id: g for g in games_to_add}}

        # TODO: handle duplicates here, either check like above or set on_conflict_do_nothing
        deliveries_to_add = [
            DeliveryDB(
                bowler=player_lookup[delivery_raw.bowler],
                batsman=player_lookup[delivery_raw.batsman],
                game=game_lookup[delivery_raw.fixtureId],
                **valid_delivery_map[delivery_raw.id].model_dump(),
            )
            for delivery_raw in delivery_batch.itertuples(index=False)
        ]
        session.add_all(instances=deliveries_to_add)
    ingested_count = len(deliveries_to_add)
    print(f"Ingested {ingested_count} deliveries")
    return ingested_count


def ingest(num_deliveries: int, batch_size: int):
    deliveries_to_ingest = get_deliveries_to_ingest(num_deliveries=num_deliveries)
    num_deliveries_found = len(deliveries_to_ingest)
    print(f"Found {num_deliveries_found} deliveries to ingest")

    ingest_count = 0
    num_batches = (num_deliveries_found - 1) // batch_size + 1
    for batch_idx in range(0, num_deliveries_found, batch_size):
        batch = deliveries_to_ingest.iloc[batch_idx : batch_idx + batch_size]
        batch_number = (batch_idx // batch_size) + 1

        ingest_count += ingest_delivery_batch(delivery_batch=batch)

        print(f"Processing batch {batch_number}/{num_batches} ({len(batch)} deliveries)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run moderate ingestion approach with batching")
    parser.add_argument(
        "--num-deliveries",
        type=int,
        default=DEFAULT_NUM_DELIVERIES,
        help=f"Number of deliveries to ingest (default: {DEFAULT_NUM_DELIVERIES})",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Batch size for processing deliveries (default: {DEFAULT_BATCH_SIZE})",
    )
    args = parser.parse_args()
    ingest(num_deliveries=args.num_deliveries, batch_size=args.batch_size)
