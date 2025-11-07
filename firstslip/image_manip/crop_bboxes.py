import argparse
import json
import re
from pathlib import Path

import cv2


def clean_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", Path(name).stem).strip("_")


def crop_bboxes(coco_json_filename: str, output_dir: str | None) -> None:
    coco_json_path = Path(coco_json_filename)
    with coco_json_path.open(mode="r") as f:
        coco_data = json.load(f)

    out_path = Path(output_dir) if output_dir else coco_json_path.parent.parent / "bboxes_cropped"
    out_path.mkdir(parents=True, exist_ok=True)

    categories_map = {cat["id"]: cat["name"] for cat in coco_data["categories"]}
    for image_info in coco_data["images"]:
        image_path = coco_json_path.parent / image_info.get("file_name")
        if not image_path.exists():
            print(f"Warning: No image at {image_path}, skipping...")
            continue

        img = cv2.imread(filename=str(image_path))

        cleaned_image_name = clean_name(image_info.get("file_name"))

        # Track class counts for this image
        class_counts = {}

        for ann in coco_data["annotations"]:
            if ann["image_id"] != image_info["id"]:
                continue

            category_name = categories_map[ann["category_id"]]
            cleaned_category_name = clean_name(category_name)

            # Get and increment the count for this class
            class_idx = class_counts.get(cleaned_category_name, 0)
            class_counts[cleaned_category_name] = class_idx + 1

            x, y, w, h = map(int, ann["bbox"])

            # Add padding while staying within image bounds
            pad = 3
            img_height, img_width = img.shape[:2]
            y_start = max(0, y - pad)
            y_end = min(img_height, y + h + pad)
            x_start = max(0, x - pad)
            x_end = min(img_width, x + w + pad)

            cropped = img[y_start:y_end, x_start:x_end]

            if cropped.size == 0:
                print(f"Warning: Empty crop for annotation {ann['id']}, skipping...")
                continue

            output_path = out_path / f"{cleaned_image_name}_{cleaned_category_name}_{class_idx}.jpg"
            cv2.imwrite(filename=str(output_path), img=cropped)

    print(f"Cropped bounding boxes saved to {out_path}")


def cli():
    parser = argparse.ArgumentParser(description="Crop bounding boxes from images using COCO annotations")
    parser.add_argument(
        "--coco-json-path",
        default="data/defect_detect/scales_cropped_out/annotations_coco.json",
        help="Path to COCO-style JSON file",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to save cropped bounding boxes (default: 'bboxes_cropped' folder in same directory as COCO file)",
    )
    args = parser.parse_args()
    crop_bboxes(coco_json_filename=args.coco_json_path, output_dir=args.output_dir)


if __name__ == "__main__":
    cli()
