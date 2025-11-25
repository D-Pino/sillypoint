import argparse

from cowcorner.ingest.optimized import ingest

DEFAULT_NUM_DELIVERIES = 20_000
DEFAULT_BATCH_SIZE = 1000

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
