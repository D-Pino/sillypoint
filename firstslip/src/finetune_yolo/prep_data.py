import argparse
import json
import shutil
from pathlib import Path

import yaml
from ultralytics.data.converter import convert_coco


def prep_data(data_dir: str) -> Path:
    dataset_dir = Path(data_dir)
    annotations_dir = dataset_dir / "annotations"

    # Need to do this bizarre dance with the folders cause convert_coco is really not very ergonomic
    temp_dir = dataset_dir / "temp_dir"
    convert_coco(labels_dir=str(annotations_dir), save_dir=str(temp_dir), cls91to80=False)
    src_labels_dir = temp_dir / "labels"
    dst_labels_dir = dataset_dir / "labels"
    if dst_labels_dir.exists():
        shutil.rmtree(str(dst_labels_dir))
    shutil.move(str(src_labels_dir), str(dst_labels_dir))
    shutil.rmtree(temp_dir)

    # Need to get class names to create the dataset.yaml for yolo finetuning
    original_coco_json_path = dataset_dir / "annotations_coco.json"
    with original_coco_json_path.open("r") as f:
        coco_data = json.load(f)
    categories = coco_data.get("categories", [])

    # Have to hack this in here cause Sean can't export data properly
    categories.pop(0)

    class_names = [cat["name"] for cat in sorted(categories, key=lambda x: x["id"])]

    # Create dataset.yaml
    yaml_data = {
        "path": str(dataset_dir.absolute()),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "nc": len(class_names),
        "names": class_names,
    }
    yaml_path = dataset_dir / "dataset.yaml"
    with yaml_path.open("w") as handle:
        yaml.dump(data=yaml_data, stream=handle, default_flow_style=False)

    return yaml_path


def cli() -> None:
    parser = argparse.ArgumentParser(description="Prepare YOLO training assets from a COCO dataset")
    parser.add_argument("--data-dir", required=True, help="Dataset root containing images/ and annotations/")
    args = parser.parse_args()
    prep_data(data_dir=args.data_dir)


if __name__ == "__main__":
    cli()
