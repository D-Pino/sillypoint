import os
from typing import Any
import duckdb
import pandas as pd
from pydantic import TypeAdapter, ValidationError

from cowcorner.validation.models import Delivery as DeliveryVal

DATA_DIR = f"{os.getenv('REPO_ROOT')}/common/data"
DEFAULT_NUM_DELIVERIES = 20_000
DEFAULT_BATCH_SIZE = 1_000


def validate_delivery_batch(delivery_batch: pd.DataFrame) -> list[DeliveryVal]:
    """Batch validation with fallback to individual validation."""
    delivery_list_model = TypeAdapter(type=list[DeliveryVal])
    deliveries = delivery_batch.to_dict(orient="records")
    try:
        return delivery_list_model.validate_python(deliveries)
    except ValidationError as e:
        print(f"Batch validation failed: {e}\nWill validate deliveries one-by-one")
        return validate_deliveries(deliveries=deliveries)


def validate_deliveries(deliveries: list[dict[str, Any]]) -> list[DeliveryVal]:
    """Individual validation for deliveries."""
    valid_deliveries = []
    for delivery in deliveries:
        try:
            valid_deliveries.append(DeliveryVal.model_validate(obj=delivery))
        except ValidationError as e:
            print(f"Delivery failed validation: {delivery} - {e}")
    print(f"{len(valid_deliveries)} deliveries out of {len(deliveries)} passed validation")
    return valid_deliveries


def get_deliveries_to_ingest(num_deliveries: int) -> pd.DataFrame:
    """I don't have a real source of data, so this function gets random deliveries from a
    local csv I have with ~2M deliveries and returns that.

    There's no good reason to use duckdb for this, I just wanted to try it out"""

    odata_raw: duckdb.DuckDBPyRelation = duckdb.read_csv(  # noqa: F841
        path_or_buffer=f"{DATA_DIR}/odata_full.csv",
        ignore_errors=True,  # necessary because this data is not clean
    )
    return duckdb.sql(query=f"SELECT * FROM odata_raw ORDER BY random() LIMIT {num_deliveries}").df()
