import argparse
import copy
import json
from pathlib import Path

import cv2
import numpy as np


def rotate_image(img: np.ndarray, angle: int) -> np.ndarray:
    if angle == 0:
        return img
    elif angle == 90:
        return cv2.rotate(src=img, rotateCode=cv2.ROTATE_90_CLOCKWISE)
    elif angle == 180:
        return cv2.rotate(src=img, rotateCode=cv2.ROTATE_180)
    elif angle == 270:
        return cv2.rotate(src=img, rotateCode=cv2.ROTATE_90_COUNTERCLOCKWISE)
    else:
        raise ValueError(f"Angle must be 0, 90, 180, or 270, got {angle}")


def transform_image(img: np.ndarray, angle: int, flip_h: bool, flip_v: bool) -> np.ndarray:
    transformed = rotate_image(img, angle)
    if flip_h:
        transformed = cv2.flip(src=transformed, flipCode=1)
    if flip_v:
        transformed = cv2.flip(src=transformed, flipCode=0)
    return transformed


def get_transformation_suffix(angle: int, flip_h: bool, flip_v: bool) -> str:
    parts = []

    if angle == 0 and not flip_h and not flip_v:
        return ""

    if angle != 0:
        parts.append(f"rot{angle}")

    if flip_h and flip_v:
        parts.append("fliphv")
    elif flip_h:
        parts.append("fliph")
    elif flip_v:
        parts.append("flipv")

    return "_".join(parts) if parts else "unknown"


def transform_bbox_rotate(
    bbox: tuple[float, float, float, float], angle: int, img_width: int, img_height: int
) -> tuple[float, float, float, float]:
    x, y, w, h = bbox

    if angle == 0:
        return x, y, w, h
    elif angle == 90:
        return img_height - (y + h), x, h, w
    elif angle == 180:
        return img_width - (x + w), img_height - (y + h), w, h
    elif angle == 270:
        return y, img_width - (x + w), h, w
    else:
        raise ValueError(f"Angle must be 0, 90, 180, or 270, got {angle}")


def transform_bbox_flip(
    bbox: tuple[float, float, float, float], flip_h: bool, flip_v: bool, img_width: int, img_height: int
) -> tuple[float, float, float, float]:
    x, y, w, h = bbox

    if flip_h:
        x = img_width - (x + w)
    if flip_v:
        y = img_height - (y + h)

    return x, y, w, h


def transform_dataset(coco_json_filename: str, output_dir: str | None) -> None:
    coco_json_path = Path(coco_json_filename)
    with coco_json_path.open(mode="r") as f:
        coco_data = json.load(f)

    out_path = Path(output_dir) if output_dir else coco_json_path.parent.parent / "transformed"
    out_path.mkdir(parents=True, exist_ok=True)

    # Get the base directory from the COCO JSON path
    base_dir = coco_json_path.parent

    # Create combined COCO data structure with original data
    combined_coco = {
        "images": [],
        "categories": copy.deepcopy(coco_data["categories"]),
        "annotations": copy.deepcopy(coco_data["annotations"]),
        "info": copy.deepcopy(coco_data.get("info", {})),
    }

    # Define all unique transformations
    transformation_configs = [
        # (0, False, False),  # original
        (90, False, False),  # rot90
        (180, False, False),  # rot180
        (270, False, False),  # rot270
        (0, True, False),  # flip_h
        (0, False, True),  # flip_v
        (90, True, False),  # diagonal flip 1
        (90, False, True),  # diagonal flip 2
    ]

    # Start counters after original data
    annotation_id_counter = max(ann["id"] for ann in coco_data["annotations"]) + 1 if coco_data["annotations"] else 0
    image_id_counter = max(img["id"] for img in coco_data["images"]) + 1 if coco_data["images"] else 0

    for image_info in coco_data["images"]:
        image_file_name = image_info.get("file_name")
        image_path = base_dir / image_file_name

        if not image_path.exists():
            print(f"Warning: No image at {image_path}, skipping...")
            continue

        img = cv2.imread(filename=str(image_path))
        img_height, img_width = img.shape[:2]

        # Copy original image to new output directory
        original_new_output_path = out_path / f"{image_path.stem}.jpg"
        cv2.imwrite(filename=str(original_new_output_path), img=img)

        # Add original image info with new file name
        original_image_info = copy.deepcopy(image_info)
        original_image_info["file_name"] = f"{image_path.stem}.jpg"
        combined_coco["images"].append(original_image_info)

        # Apply all transformation combinations to the main image
        for angle, flip_h, flip_v in transformation_configs:
            suffix = get_transformation_suffix(angle, flip_h, flip_v)

            # Save transformed image
            transformed = transform_image(img=img, angle=angle, flip_h=flip_h, flip_v=flip_v)
            output_path = out_path / f"{image_path.stem}_{suffix}.jpg"
            cv2.imwrite(filename=str(output_path), img=transformed)

            # Calculate img dimensions after transformation
            if angle in [90, 270]:
                new_width, new_height = img_height, img_width
            else:
                new_width, new_height = img_width, img_height

            # Add image info to combined COCO
            transformed_image_info = {
                "id": image_id_counter,
                "license": 1,
                "file_name": f"{image_path.stem}_{suffix}.jpg",
                "height": new_height,
                "width": new_width,
            }
            combined_coco["images"].append(transformed_image_info)

            # Transform and add annotations
            for ann in coco_data["annotations"]:
                if ann["image_id"] != image_info["id"]:
                    continue

                # First apply rotation
                transformed_bbox = transform_bbox_rotate(ann["bbox"], angle, img_width, img_height)

                # Then apply flips (using dimensions after rotation)
                transformed_bbox = transform_bbox_flip(transformed_bbox, flip_h, flip_v, new_width, new_height)

                new_annotation = {
                    "id": annotation_id_counter,
                    "image_id": image_id_counter,
                    "category_id": ann["category_id"],
                    "bbox": list(transformed_bbox),
                    "area": transformed_bbox[2] * transformed_bbox[3],
                    "segmentation": ann.get("segmentation", []),
                    "iscrowd": ann.get("iscrowd", 0),
                    "ignore": ann.get("ignore", 0),
                }
                combined_coco["annotations"].append(new_annotation)
                annotation_id_counter += 1

            image_id_counter += 1

    # Sort images and annotations by ID for cleaner output
    combined_coco["images"].sort(key=lambda x: x["id"])
    combined_coco["annotations"].sort(key=lambda x: x["id"])

    # Save combined COCO JSON
    json_output_path = out_path / "annotations_coco.json"
    with json_output_path.open("w") as f:
        json.dump(combined_coco, f, indent=2)


def cli():
    parser = argparse.ArgumentParser(description="Transform images to extend dataset")
    parser.add_argument(
        "--coco-json-path",
        default="data/defect_detect/scales_cropped_out/annotations_coco.json",
        help="Path to COCO-style JSON file",
    )
    parser.add_argument("--output-dir", help="Directory to save transformed images and annotations")
    args = parser.parse_args()
    transform_dataset(coco_json_filename=args.coco_json_path, output_dir=args.output_dir)


if __name__ == "__main__":
    cli()
