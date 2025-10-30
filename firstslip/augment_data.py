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
        return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    elif angle == 180:
        return cv2.rotate(img, cv2.ROTATE_180)
    elif angle == 270:
        return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    else:
        raise ValueError(f"Angle must be 0, 90, 180, or 270, got {angle}")


def augment_image(img: np.ndarray, angle: int, flip_h: bool, flip_v: bool) -> np.ndarray:
    augmented = rotate_image(img, angle)
    if flip_h:
        augmented = cv2.flip(augmented, 1)
    if flip_v:
        augmented = cv2.flip(augmented, 0)
    return augmented


def get_augmentation_suffix(angle: int, flip_h: bool, flip_v: bool) -> str:
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
        # 90 degrees clockwise: new image is (height, width)
        return y, img_width - x - w, h, w
    elif angle == 180:
        return img_width - x - w, img_height - y - h, w, h
    elif angle == 270:
        # 270 degrees clockwise (90 counter-clockwise): new image is (height, width)
        return img_height - y - h, x, h, w
    else:
        raise ValueError(f"Angle must be 0, 90, 180, or 270, got {angle}")


def transform_bbox_flip(
    bbox: tuple[float, float, float, float], flip_h: bool, flip_v: bool, img_width: int, img_height: int
) -> tuple[float, float, float, float]:
    x, y, w, h = bbox

    if flip_h:
        x = img_width - x - w
    if flip_v:
        y = img_height - y - h

    return x, y, w, h


def main(coco_json_filename: str = "result.json", image_path_override: str | None = None) -> None:
    coco_json_path = Path(coco_json_filename)
    with coco_json_path.open() as f:
        coco_data = json.load(f)

    output_dir = Path(__file__).parent / "data" / "defect_detect"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create combined COCO data structure with original data
    combined_coco = {
        "images": [],
        "categories": copy.deepcopy(coco_data["categories"]),
        "annotations": copy.deepcopy(coco_data["annotations"]),
        "info": copy.deepcopy(coco_data.get("info", {})),
    }

    # Define all unique augmentations
    augmentation_configs = [
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
        image_path = (
            coco_json_path.parent / image_file_name if image_path_override is None else Path(image_path_override)
        )
        if not image_path.exists():
            raise FileNotFoundError(f"No image at {image_path}")
        img = cv2.imread(str(image_path))
        img_height, img_width = img.shape[:2]

        # Copy original image to new output directory
        original_new_output_path = output_dir / f"{image_path.stem}.jpg"
        cv2.imwrite(str(original_new_output_path), img)

        # Add original image info with new file name
        original_image_info = copy.deepcopy(image_info)
        original_image_info["file_name"] = f"{image_path.stem}.jpg"
        combined_coco["images"].append(original_image_info)

        # for ann in coco_data["annotations"]:
        #     if ann["image_id"] != image_info["id"]:
        #         continue
        #
        #     category_name = categories_map[ann["category_id"]]
        #     ann_id = ann["id"]
        #
        #     x, y, w, h = map(int, ann["bbox"])
        #     cropped = img[y : y + h, x : x + w]
        #
        #     # Apply all augmentation combinations to the cropped bbox
        #     for angle in angles:
        #         for flip_h, flip_v in flip_options:
        #             augmented = augment_image(cropped, angle, flip_h, flip_v)
        #             suffix = get_augmentation_suffix(angle, flip_h, flip_v)
        #             output_path = output_dir / f"{category_name}_{ann_id}_{suffix}.jpg"
        #             cv2.imwrite(str(output_path), augmented)

        # Apply all augmentation combinations to the main image
        for angle, flip_h, flip_v in augmentation_configs:
            suffix = get_augmentation_suffix(angle, flip_h, flip_v)

            # Save augmented image
            augmented = augment_image(img, angle, flip_h, flip_v)
            output_path = output_dir / f"{image_path.stem}_{suffix}.jpg"
            cv2.imwrite(str(output_path), augmented)

            # Calculate img dimensions after augmentation
            if angle in [90, 270]:
                new_width, new_height = img_height, img_width
            else:
                new_width, new_height = img_width, img_height

            # Add image info to combined COCO
            augmented_image_info = {
                "id": image_id_counter,
                "license": 1,
                "file_name": f"{image_path.stem}_{suffix}.jpg",
                "height": new_height,
                "width": new_width,
            }
            combined_coco["images"].append(augmented_image_info)

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
    json_output_path = output_dir / "annotations_coco.json"
    with json_output_path.open("w") as f:
        json.dump(combined_coco, f, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Augment images and generate COCO JSON files")
    parser.add_argument("--coco-json-path", help="Path to COCO-style JSON file")
    parser.add_argument(
        "--image-path",
        help="Override the image path from COCO file with a local image. Only works if it's a single image (for testing).",
    )
    args = parser.parse_args()
    main(coco_json_filename=args.coco_json_path, image_path_override=args.image_path)
