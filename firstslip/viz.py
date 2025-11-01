import argparse

import fiftyone as fo
import fiftyone.types as fot


def main(
    images_dir: str,
    coco_json: str,
    dataset_name: str,
    address: str,
    port: int,
) -> None:
    if fo.dataset_exists(name=dataset_name):
        fo.delete_dataset(name=dataset_name)

    dataset = fo.Dataset.from_dir(
        data_path=images_dir,
        labels_path=coco_json,
        dataset_type=fot.COCODetectionDataset,
        name=dataset_name,
        include_id=True,
    )

    session = fo.launch_app(dataset, address=address, port=port)
    session.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View COCO annotations in FiftyOne")
    parser.add_argument(
        "--images-dir",
        type=str,
        default="data/defect_detect/augmented",
        help="Directory containing images",
    )
    parser.add_argument(
        "--coco-json",
        type=str,
        default="data/defect_detect/augmented/annotations_coco.json",
        help="Path to COCO JSON annotations file",
    )
    parser.add_argument(
        "--dataset-name",
        type=str,
        default="Defect Detect",
        help="Name for the FiftyOne dataset",
    )
    parser.add_argument(
        "--address",
        type=str,
        default="0.0.0.0",
        help="Address to launch FiftyOne app on",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5151,
        help="Port to launch FiftyOne app on",
    )
    args = parser.parse_args()

    main(
        images_dir=args.images_dir,
        coco_json=args.coco_json,
        dataset_name=args.dataset_name,
        address=args.address,
        port=args.port,
    )
