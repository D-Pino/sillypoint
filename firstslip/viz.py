import argparse

import fiftyone as fo
import fiftyone.types as fot
from wonderwords import RandomWord


def main(
    images_dir: str,
    coco_json_path: str,
    dataset_name: str,
    address: str,
    port: int,
) -> None:
    random_word = RandomWord().word()
    dataset_name = f"{dataset_name} ({random_word})"

    dataset = fo.Dataset.from_dir(
        dataset_type=fot.COCODetectionDataset,
        data_path=images_dir,
        labels_path=coco_json_path,
        name=dataset_name,
        label_field="ground_truth",
        include_id=True,
        include_annotation_id=True,
    )

    # dataset.untag_samples()  # optional reset
    # dataset.tag_samples("train")  # example project tag
    # # label-level
    # dataset.untag_labels("ground_truth")
    # dataset.tag_labels("ground_truth", "gt")  # tag all boxes as "gt"

    # # 3) Optional: save a reusable view recipe
    # view = dataset.filter_labels("ground_truth", fo.ViewField("label").is_not_none())
    # dataset.save_view("my-default", view)  # cheap, stores only the filter rules

    session = fo.launch_app(dataset, address=address, port=port)
    session.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View COCO annotations in FiftyOne")
    parser.add_argument(
        "--images-dir",
        type=str,
        default="data/defect_detect/scales_cropped_out",
        help="Directory containing images",
    )
    parser.add_argument(
        "--coco-json-path",
        type=str,
        default="data/defect_detect/scales_cropped_out/_annotations.coco.json",
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
        coco_json_path=args.coco_json_path,
        dataset_name=args.dataset_name,
        address=args.address,
        port=args.port,
    )
