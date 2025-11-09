import argparse
import json
from pathlib import Path

import cv2 as cv
import numpy as np


def crop_image(image_path: str, output_dir: Path, debug: bool = False) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    input_path = Path(image_path)
    out_path = output_dir / f"{input_path.stem}_cropped{input_path.suffix}"

    img = cv.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    img_h, img_w = img.shape[:2]

    if debug:
        debug_dir = out_path / "debug"
        debug_dir.mkdir(exist_ok=True)
        cv.imwrite(str(debug_dir / f"{input_path.stem}_00_original.jpg"), img)

    # Convert to grayscale and blur to suppress texture
    g = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    g_blur = cv.medianBlur(g, 5)

    if debug:
        cv.imwrite(str(debug_dir / f"{input_path.stem}_01_grayscale.jpg"), g)
        cv.imwrite(str(debug_dir / f"{input_path.stem}_02_blurred.jpg"), g_blur)

    # Threshold to separate content from dark borders/rulers
    _, binary = cv.threshold(g_blur, 60, 255, cv.THRESH_BINARY)

    # Fill holes and join fragmented content
    binary = cv.morphologyEx(binary, cv.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=2)

    if debug:
        cv.imwrite(str(debug_dir / f"{input_path.stem}_03_thresholded.jpg"), binary)
        cv.imwrite(str(debug_dir / f"{input_path.stem}_04_morphology.jpg"), binary)

    # Find the largest connected component
    num_labels, labels, stats, _ = cv.connectedComponentsWithStats(binary, connectivity=8)
    if num_labels <= 1:
        raise RuntimeError("No foreground found")

    # Get largest component (skip label 0 = background)
    min_area = 0.2 * img_h * img_w
    candidates = [i for i in range(1, num_labels) if stats[i, cv.CC_STAT_AREA] >= min_area]
    best = (
        max(candidates, key=lambda i: stats[i, cv.CC_STAT_AREA])
        if candidates
        else 1 + np.argmax(stats[1:, cv.CC_STAT_AREA])
    )

    x = stats[best, cv.CC_STAT_LEFT]
    y = stats[best, cv.CC_STAT_TOP]
    w = stats[best, cv.CC_STAT_WIDTH]
    h = stats[best, cv.CC_STAT_HEIGHT]

    # Remove 2px rim from edges
    pad = 2
    x0 = max(0, x + pad)
    y0 = max(0, y + pad)
    x1 = min(img_w, x + w - pad)
    y1 = min(img_h, y + h - pad)

    if debug:
        img_with_bbox = img.copy()
        cv.rectangle(img_with_bbox, (x0, y0), (x1, y1), (0, 255, 0), 3)
        cv.imwrite(str(debug_dir / f"{input_path.stem}_05_bbox.jpg"), img_with_bbox)

    crop = img[y0:y1, x0:x1]

    if debug:
        cv.imwrite(str(debug_dir / f"{input_path.stem}_06_final_crop.jpg"), crop)
        print(f"Debug images saved to {debug_dir}")

    cv.imwrite(str(out_path), crop)
    print(f"Cropped: {out_path}")

    return crop, (x0, y0, x1, y1)


def crop_main_image(coco_json_path: str, output_dir: str | None, debug: bool = False):
    annotations_path = Path(coco_json_path)
    if not annotations_path.exists():
        raise FileNotFoundError(f"COCO JSON file not found: {coco_json_path}")

    out_path = Path(output_dir) if output_dir else annotations_path.parent.parent / "scales_cropped_out"
    out_path.mkdir(parents=True, exist_ok=True)

    # Load COCO annotations
    with annotations_path.open(mode="r") as f:
        coco_data = json.load(f)
    print(f"Loaded annotations from {annotations_path}")

    # Get the base directory from the COCO JSON path
    base_dir = annotations_path.parent

    # Track transformed data
    transformed_images = []
    transformed_annotations = []

    print(f"Found {len(coco_data['images'])} images to process")
    for image_info in coco_data["images"]:
        image_file_name = image_info["file_name"]
        image_file_path = base_dir / image_file_name

        if not image_file_path.exists():
            print(f"Warning: Image not found: {image_file_path}, skipping...")
            continue

        crop, (x0, y0, x1, y1) = crop_image(image_path=str(image_file_path), output_dir=out_path, debug=debug)

        # Transform annotations
        image_id = image_info["id"]

        # Update image info
        cropped_height, cropped_width = crop.shape[:2]
        transformed_img = image_info.copy()
        transformed_img["file_name"] = f"{image_file_path.stem}_cropped{image_file_path.suffix}"
        transformed_img["width"] = int(cropped_width)
        transformed_img["height"] = int(cropped_height)
        transformed_images.append(transformed_img)

        # Transform bounding boxes
        for ann in coco_data["annotations"]:
            if ann["image_id"] == image_id:
                bbox = ann["bbox"]
                old_x, old_y, width, height = bbox

                # Transform to cropped coordinates
                new_x = old_x - x0
                new_y = old_y - y0

                # Check if bbox is still within the cropped image
                if new_x + width > 0 and new_y + height > 0 and new_x < cropped_width and new_y < cropped_height:
                    # Clip to image boundaries
                    clipped_x = max(0, new_x)
                    clipped_y = max(0, new_y)
                    clipped_width = min(new_x + width, cropped_width) - clipped_x
                    clipped_height = min(new_y + height, cropped_height) - clipped_y

                    transformed_ann = ann.copy()
                    # Convert to Python native types for JSON serialization
                    transformed_ann["bbox"] = [
                        float(clipped_x),
                        float(clipped_y),
                        float(clipped_width),
                        float(clipped_height),
                    ]
                    transformed_ann["area"] = float(clipped_width * clipped_height)
                    transformed_annotations.append(transformed_ann)

    # Save transformed annotations
    if transformed_images:
        output_coco = {
            "info": coco_data.get("info", {}),
            "licenses": coco_data.get("licenses", []),
            "categories": coco_data["categories"],
            "images": transformed_images,
            "annotations": transformed_annotations,
        }
        output_annotations_path = out_path / "_annotations.coco.json"
        with open(output_annotations_path, "w") as f:
            json.dump(output_coco, f, indent=4)
        print(f"Saved transformed annotations to {output_annotations_path}")


def cli():
    parser = argparse.ArgumentParser(description="Crop images to largest content region")
    parser.add_argument(
        "--coco-json-path", default="data/defect_detect/originals/_annotations.coco.json", help="Path to COCO JSON file"
    )
    parser.add_argument("--output-dir", help="Directory to save cropped images")
    parser.add_argument("--debug", action="store_true", help="Save intermediate debug images")

    args = parser.parse_args()
    crop_main_image(coco_json_path=args.coco_json_path, output_dir=args.output_dir, debug=args.debug)


if __name__ == "__main__":
    cli()
