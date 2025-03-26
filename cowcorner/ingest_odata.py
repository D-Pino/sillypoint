import os
from datetime import datetime

import duckdb
import pandas as pd
from database.models import Delivery
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATA_DIR = f"{os.getenv('REPO_ROOT')}/common/data"


def get_db_url():
    return f"postgresql://{os.getenv('ODATA_DB_USER')}:{os.getenv('ODATA_DB_PASSWORD')}@localhost:{os.getenv('ODATA_DB_PORT')}/{os.getenv('ODATA_DB_NAME')}"


def get_deliveries_to_ingest(num_deliveries: int = 20_000) -> pd.DataFrame:
    """I don't have a real source of data, so this function gets deliveries from a
    local csv I have with ~20M deliveries, does some randomization to mock a real data source,
    and returns that.

    There's no good reason to use duckdb for this, I just wanted to try it out"""

    odata_raw: duckdb.DuckDBPyRelation = duckdb.read_csv(
        f"{DATA_DIR}/odata_full.csv",
        ignore_errors=True,  # necessary, this data is not clean
    )
    return duckdb.sql(
        f"SELECT * FROM odata_raw ORDER BY random() LIMIT {num_deliveries}"
    ).df()


def ingest_delivery(db_sess: Session, delivery: pd.Series):
    deliveries = db_sess.query(Delivery).all()
    print(f"{len(deliveries)} deliveries in db: {deliveries[0].delivered_at}")

    new_delivery = Delivery(
        competition=delivery["competition"],
        innings=int(delivery["inns"]),
        over=int(delivery["over"]),
        ball=int(delivery["ball"]),
        fielder=delivery["fielder"],
        batsman_hand=str(delivery["batsmanHand"]).title(),
        bowler_hand=str(delivery["bowlerHand"]).title(),
        bowling_style=delivery["bowlerType"],
        is_wicket=delivery["is_wicket"],
        dismissal_type=delivery["dismissalType"],
        line=delivery["line"],
        length=delivery["length"],
        variation=delivery["variation"],
        foot=delivery["foot"],
        shot=delivery["shot"],
        shot_type=delivery["shot_type"],
        control=delivery["control"],
        shot_angle=float(delivery["shot_angle"]),
        shot_magnitude=float(delivery["shot_magnitude"]),
        fielding_position=delivery["fielding_position"],
        fielding_action=delivery["fielder_action"],
        runs=int(delivery["runs"]),
        runs_scored=int(delivery["runs_scored"]),
        runs_conceded=int(delivery["runs_conceded"]),
        extras=int(delivery["extras"]),
        commentary=delivery["commentary"],
        delivered_at=datetime.fromisoformat(str(delivery["timestamp"])),
        zone=delivery["zone"],
        area=delivery["area"],
        len_var=delivery["len/var"],
        year=int(delivery["year"]),
        elevation=delivery["elevation"],
    )
    db_sess.add(new_delivery)
    db_sess.commit()


def main():
    # Get a db connection
    engine = create_engine(get_db_url())
    Session = sessionmaker(bind=engine)
    session = Session()
    deliveries = get_deliveries_to_ingest()
    # print(type(deliveries.loc[0]["timestamp"]))
    ingest_delivery(db_sess=session, delivery=deliveries.iloc[0])


if __name__ == "__main__":
    main()
