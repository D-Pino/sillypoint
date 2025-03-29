import os

import duckdb
import pandas as pd
from database.models import Delivery as DeliveryDB
from database.models import Player as PlayerDB
from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from validation.models import Delivery as DeliveryVal
from validation.models import Player as PlayerVal

from cowcorner.common import get_db_url

DATA_DIR = f"{os.getenv('REPO_ROOT')}/common/data"


def get_deliveries_to_ingest(num_deliveries: int = 20) -> pd.DataFrame:
    """I don't have a real source of data, so this function gets random deliveries from a
    local csv I have with ~20M deliveries and returns that.

    There's no good reason to use duckdb for this, I just wanted to try it out"""

    odata_raw: duckdb.DuckDBPyRelation = duckdb.read_csv(  # noqa: F841
        f"{DATA_DIR}/odata_full.csv",
        ignore_errors=True,  # necessary because this data is not clean
    )
    return duckdb.sql(
        f"SELECT * FROM odata_raw ORDER BY random() LIMIT {num_deliveries}"
    ).df()


def ingest_delivery(db_sess: Session, delivery: pd.Series):
    pass


def main():
    # Get data to be ingested
    deliveries: pd.DataFrame = get_deliveries_to_ingest()
    # Set up db connection
    engine = create_engine(get_db_url())
    Session = sessionmaker(bind=engine)
    with Session() as session:
        for _, delivery in deliveries.iterrows():
            try:
                for player_type in ("bowler", "batsman"):
                    player_name = delivery[player_type]
                    stmt = select(PlayerDB).where(PlayerDB.name == player_name)
                    player_found = session.execute(stmt).one_or_none()
                    if player_found is None:
                        print(
                            f"Player '{player_name}' doesn't exist yet, will be created"
                        )
                        validated_player = PlayerVal(name=player_name)
                        player = PlayerDB(**validated_player.model_dump())
                        session.add(player)
                        print("added")
                session.commit()
                batsman = session.execute(
                    select(PlayerDB).where(PlayerDB.name == delivery["batsman"])
                ).scalar_one()
                bowler = session.execute(
                    select(PlayerDB).where(PlayerDB.name == delivery["bowler"])
                ).scalar_one()
                validated_delivery = DeliveryVal(**delivery.to_dict())
                delivery = DeliveryDB(
                    bowler=bowler, batsman=batsman, **validated_delivery.model_dump()
                )
                session.add(delivery)
            except ValidationError as e:
                print(e)
            session.commit()
    print("Done")


if __name__ == "__main__":
    main()
