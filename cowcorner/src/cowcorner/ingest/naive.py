from typing import Any
import argparse

import pandas as pd
from cowcorner.common import SessionLocal, get_or_create
from pydantic import ValidationError

from cowcorner.database.models import Delivery as DeliveryDB
from cowcorner.database.models import Game as GameDB
from cowcorner.database.models import Player as PlayerDB
from cowcorner.validation.models import Delivery as DeliveryVal
from utils import get_deliveries_to_ingest


DEFAULT_NUM_DELIVERIES = 20_000


def validate_delivery(delivery: dict[str, Any]) -> DeliveryVal | None:
    try:
        return DeliveryVal.model_validate(obj=delivery)
    except ValidationError as e:
        print(f"Delivery failed validation: {delivery} - {e}")
        return None


def ingest_delivery(delivery_data: dict[str, Any]) -> bool:
    # Validate delivery according to Pydantic model
    if (validated_delivery := validate_delivery(delivery=delivery_data)) is None:
        return False

    with SessionLocal.begin() as session:
        bowler, _ = get_or_create(model=PlayerDB, session=session, name=delivery_data["bowler"])
        batsman, _ = get_or_create(model=PlayerDB, session=session, name=delivery_data["batsman"])

        game, _ = get_or_create(
            model=GameDB,
            session=session,
            source_id=delivery_data["fixtureId"],
            game_date=delivery_data["matchDate"].date() if not pd.isna(obj=delivery_data["matchDate"]) else None,
            competition=delivery_data["competition"],
            game_format=delivery_data["format"],
        )

        # Create delivery
        delivery_db = DeliveryDB(
            bowler=bowler,
            batsman=batsman,
            game=game,
            **validated_delivery.model_dump(),
        )
        session.add(instance=delivery_db)

    return True


def ingest(num_deliveries: int):
    deliveries_to_ingest = get_deliveries_to_ingest(num_deliveries=num_deliveries)
    num_deliveries_found = len(deliveries_to_ingest)
    print(f"Found {num_deliveries_found} deliveries to ingest")

    ingest_count = 0
    for i, delivery in deliveries_to_ingest.iterrows():
        delivery_dict = delivery.to_dict()
        if ingest_delivery(delivery_data=delivery_dict):
            ingest_count += 1

        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/{num_deliveries_found} deliveries")

    print(f"Successfully ingested {ingest_count}/{num_deliveries_found} deliveries")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run naive ingestion approach")
    parser.add_argument(
        "--num-deliveries",
        type=int,
        default=DEFAULT_NUM_DELIVERIES,
        help=f"Number of deliveries to ingest (default: {DEFAULT_NUM_DELIVERIES})",
    )
    args = parser.parse_args()
    ingest(num_deliveries=args.num_deliveries)
