from pathlib import Path

import cv2 as cv
import numpy as np


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}


def crop_image(
    image_path: str, output_dir: Path, debug: bool = False
) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    input_path = Path(image_path)
    out_path = output_dir / f"{input_path.stem}_cropped{input_path.suffix}"

    img = cv.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    h, w = img.shape[:2]

    if debug:
        debug_dir = input_path.parent / "debug"
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
    min_area = 0.2 * h * w
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
    x1 = min(w, x + w - pad)
    y1 = min(h, y + h - pad)

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


def crop_main_image(image_dir: str, output_dir: str, debug: bool = False):
    dir_path = Path(image_dir)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {image_dir}")
    if not dir_path.is_dir():
        raise ValueError(f"Not a directory: {image_dir}")

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    image_files = [f for f in dir_path.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS]
    if not image_files:
        print(f"No image files found in {image_dir}")
        return

    print(f"Found {len(image_files)} images to process")
    for image_file in sorted(image_files):
        try:
            crop, bbox = crop_image(image_path=str(image_file), output_dir=out_path, debug=debug)
        except Exception as e:
            print(f"Error processing {image_file.name}: {e}")


def cli():
    import argparse

    parser = argparse.ArgumentParser(description="Crop images to largest content region")
    parser.add_argument(
        "--image-dir",
        default="data/defect_detect/originals",
        help="Directory containing images to crop (default: data/defect_detect/originals)",
    )
    parser.add_argument(
        "--output-dir",
        default="data/defect_detect/scales_cropped_out",
        help="Directory to save cropped images (default: data/defect_detect/scales_cropped_out)",
    )
    parser.add_argument("--debug", action="store_true", help="Save intermediate debug images")

    args = parser.parse_args()
    crop_main_image(image_dir=args.image_dir, output_dir=args.output_dir, debug=args.debug)


if __name__ == "__main__":
    cli()
