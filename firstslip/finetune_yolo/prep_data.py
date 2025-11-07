import argparse
import json
import shutil
from pathlib import Path

import yaml
from ultralytics.data.converter import convert_coco


def prepare_data(data_dir: str, cls91to80: bool = False) -> Path:
    """
    Prepare YOLO-friendly assets from a COCO-style dataset.

    Args:
        data_dir: Root directory containing images/, annotations/, and annotations_coco.json.
        cls91to80: Whether to remap MS COCO 91 classes down to 80 during conversion.

    Returns:
        Path to the generated dataset.yaml file.
    """

    dataset_dir = Path(data_dir).expanduser().resolve()
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")

    annotations_dir = dataset_dir / "annotations"
    if not annotations_dir.exists():
        raise FileNotFoundError(f"Expected COCO annotations directory at {annotations_dir}")

    # Convert COCO annotations to YOLO labels into a temporary working directory.
    temp_dir = dataset_dir / "temp_labels"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    convert_coco(labels_dir=str(annotations_dir), save_dir=str(temp_dir), cls91to80=cls91to80)

    # Move the YOLO labels produced by the converter into dataset/labels/{split}
    for split in ("train", "val", "test"):
        temp_labels = temp_dir / "labels" / split
        if not temp_labels.exists():
            continue
        target_labels = dataset_dir / "labels" / split
        target_labels.parent.mkdir(parents=True, exist_ok=True)
        if target_labels.exists():
            shutil.rmtree(target_labels)
        shutil.move(src=str(temp_labels), dst=str(target_labels))

    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    # Build dataset.yaml by inspecting the COCO categories.
    coco_json = dataset_dir / "annotations_coco.json"
    if not coco_json.exists():
        raise FileNotFoundError(f"Expected COCO summary JSON at {coco_json}")

    with coco_json.open() as source:
        coco_data = json.load(source)
    class_names = [cat["name"] for cat in coco_data.get("categories", [])]
    if not class_names:
        raise ValueError("No categories found in annotations_coco.json")

    yaml_data = {
        "path": str(dataset_dir),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "nc": len(class_names),
        "names": class_names,
    }

    yaml_path = dataset_dir / "dataset.yaml"
    with yaml_path.open("w") as handle:
        yaml.dump(data=yaml_data, stream=handle, default_flow_style=False)

    print(f"Prepared YOLO dataset YAML at {yaml_path}")
    return yaml_path


def cli() -> None:
    parser = argparse.ArgumentParser(description="Prepare YOLO training assets from a COCO dataset")
    parser.add_argument("--data-dir", required=True, help="Dataset root containing images/ and annotations/")
    parser.add_argument(
        "--cls91to80",
        action="store_true",
        help="Map MS COCO's 91 classes down to 80 during label conversion",
    )
    args = parser.parse_args()
    prepare_data(data_dir=args.data_dir, cls91to80=args.cls91to80)


if __name__ == "__main__":
    cli()
