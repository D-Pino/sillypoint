import argparse
from pathlib import Path

import fiftyone as fo
import fiftyone.types as fot
from wonderwords import RandomWord


def main(
    coco_json_path: str,
    images_dir: str | None,
    dataset_name: str,
    address: str,
    port: int,
) -> None:
    images_dir = images_dir or str(Path(coco_json_path).parent)

    random_word = RandomWord().word()
    dataset_name = f"{dataset_name} ({random_word})"

    dataset = fo.Dataset.from_dir(
        dataset_type=fot.COCODetectionDataset,
        data_path=images_dir,
        labels_path=coco_json_path,
        name=dataset_name,
        include_id=True,
        include_annotation_id=True,
    )

    session = fo.launch_app(dataset, address=address, port=port)
    session.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View COCO annotations in FiftyOne")
    parser.add_argument(
        "--coco-json-path",
        type=str,
        default="data/defect_detect/scales_cropped_out/_annotations.coco.json",
        help="Path to COCO JSON annotations file",
    )
    parser.add_argument(
        "--images-dir",
        type=str,
        default=None,
        help="Directory containing images (defaults to directory of the COCO JSON)",
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
        coco_json_path=args.coco_json_path,
        dataset_name=args.dataset_name,
        address=args.address,
        port=args.port,
    )
