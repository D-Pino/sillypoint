import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add grandparent directory to Python path so we can import cowcorner
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
from cowcorner.common import SessionLocal
from sqlalchemy import text, select
from uuid_extensions import uuid7

from cowcorner.database.models import Game as GameDB
from cowcorner.database.models import Player as PlayerDB
from cowcorner.validation.models import Delivery as DeliveryVal
from utils import get_deliveries_to_ingest, validate_delivery_batch


DEFAULT_NUM_DELIVERIES = 20_000
DEFAULT_BATCH_SIZE = 1000




def prepare_delivery_data(
    delivery_batch: pd.DataFrame,
    valid_delivery_map: dict[str, DeliveryVal],
    player_lookup: dict[str, int],
    game_lookup: dict[str, int],
) -> list[dict]:
    now = datetime.now(timezone.utc)
    
    delivery_records = []
    for row in delivery_batch.itertuples(index=False):
        source_id = row.id
        if source_id not in valid_delivery_map:
            continue
            
        valid_delivery = valid_delivery_map[source_id]
        
        delivery_record = {
            "id": uuid7(),
            "bowler_id": player_lookup[row.bowler],
            "batsman_id": player_lookup[row.batsman], 
            "game_id": game_lookup[int(row.fixtureId)],
            "source_id": valid_delivery.source_id,
            "ball": valid_delivery.ball,
            "runs": valid_delivery.runs,
            "extras": valid_delivery.extras,
            "is_wicket": valid_delivery.is_wicket,
            "dismissal_type": valid_delivery.dismissal_type,
            "innings": valid_delivery.innings,
            "over": valid_delivery.over,
            "_created_at": now,
            "_updated_at": now,
        }
        delivery_records.append(delivery_record)
    
    return delivery_records


def ingest_delivery_batch(delivery_batch: pd.DataFrame) -> int:
    # Validate deliveries
    valid_deliveries = validate_delivery_batch(delivery_batch=delivery_batch)
    print(f"Found {len(valid_deliveries)} valid deliveries")

    if len(valid_deliveries) == 0:
        return 0

    valid_delivery_map = {d.source_id: d for d in valid_deliveries}
    delivery_batch = delivery_batch[delivery_batch["id"].isin(valid_delivery_map.keys())]

    with SessionLocal() as session:
        # Check for existing entities first to avoid redundant data preparation
        player_names = pd.unique(pd.concat([delivery_batch["bowler"], delivery_batch["batsman"]])).astype(str).tolist()
        stmt = select(PlayerDB.id, PlayerDB.name).where(PlayerDB.name.in_(player_names))
        existing_players = {name: id for id, name in session.execute(stmt)}
        
        game_source_ids = delivery_batch["fixtureId"].unique().astype(int).tolist()
        stmt = select(GameDB.id, GameDB.source_id).where(GameDB.source_id.in_(game_source_ids))
        existing_games = {source_id: id for id, source_id in session.execute(stmt)}

        # Only prepare data for new entities
        new_player_names = set(player_names) - set(existing_players.keys())
        new_game_ids = set(game_source_ids) - set(existing_games.keys())
        
        players_data = []
        if new_player_names:
            now = datetime.now(timezone.utc)
            players_data = [{"id": uuid7(), "name": str(name), "_created_at": now, "_updated_at": now} for name in new_player_names]

        games_data = []
        if new_game_ids:
            game_data = delivery_batch[delivery_batch["fixtureId"].isin(new_game_ids)].drop_duplicates("fixtureId")[["fixtureId", "matchDate", "competition", "format"]]
            game_data["processed_date"] = game_data["matchDate"].apply(lambda x: x.date() if not pd.isna(x) else None)
            now = datetime.now(timezone.utc)
            games_data = [
                {
                    "id": uuid7(),
                    "source_id": int(row.fixtureId),
                    "game_date": row.processed_date,
                    "competition": str(row.competition),
                    "game_format": str(row.format),
                    "_created_at": now,
                    "_updated_at": now,
                }
                for row in game_data[["fixtureId", "processed_date", "competition", "format"]].itertuples(index=False)
            ]

        # Raw SQL for bulk inserts with ON CONFLICT DO NOTHING
        if players_data:
            player_sql = """
            INSERT INTO players (id, name, _created_at, _updated_at) 
            VALUES (:id, :name, :_created_at, :_updated_at) 
            ON CONFLICT (name) DO NOTHING
            """
            print(f"Adding {len(players_data)} new players")
            session.execute(text(player_sql), players_data)
            
            # Update lookup with new players using the IDs we already generated
            new_players = {p["name"]: p["id"] for p in players_data}
            existing_players.update(new_players)

        if games_data:
            game_sql = """
            INSERT INTO games (id, source_id, game_date, competition, game_format, _created_at, _updated_at)
            VALUES (:id, :source_id, :game_date, :competition, :game_format, :_created_at, :_updated_at)
            ON CONFLICT (source_id) DO NOTHING
            """
            print(f"Adding {len(games_data)} new games")
            session.execute(text(game_sql), games_data)
            
            # Update lookup with new games using the IDs we already generated
            new_games = {g["source_id"]: g["id"] for g in games_data}
            existing_games.update(new_games)

        # Prepare and insert deliveries using existing lookups
        delivery_records = prepare_delivery_data(delivery_batch, valid_delivery_map, existing_players, existing_games)

        if delivery_records:
            delivery_sql = """
            INSERT INTO deliveries (
                id, bowler_id, batsman_id, game_id, source_id, ball, 
                runs, extras, is_wicket, dismissal_type, innings, over, _created_at, _updated_at
            )
            VALUES (
                :id, :bowler_id, :batsman_id, :game_id, :source_id, :ball,
                :runs, :extras, :is_wicket, :dismissal_type, :innings, :over, :_created_at, :_updated_at
            )
            ON CONFLICT (source_id) DO NOTHING
            """
            print(f"Adding {len(delivery_records)} deliveries")
            session.execute(text(delivery_sql), delivery_records)

    ingested_count = len(delivery_records) if 'delivery_records' in locals() else 0
    print(f"Ingested {ingested_count} deliveries using optimized approach")
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

        print(f"Processing batch {batch_number}/{num_batches} ({len(batch)} deliveries)")

        ingest_count += ingest_delivery_batch(delivery_batch=batch)

    print(f"Successfully ingested {ingest_count}/{num_deliveries_found} deliveries")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run optimized ingestion approach")
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
