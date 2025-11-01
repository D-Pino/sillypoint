import argparse
from pathlib import Path

import cv2
import numpy as np


def get_image_dimensions(im_path: str | Path) -> tuple[int, int]:
    im_data = cv2.imread(filename=str(im_path))
    return im_data.shape[:2]


def resize_image(im_path: str | Path, target_dimensions: tuple[int, int] = (640, 640)) -> Path:
    height, width = get_image_dimensions(im_path=im_path)
    target_width, target_height = target_dimensions
    scale = min(target_width / width, target_height / height)
    new_width, new_height = int(width * scale), int(height * scale)

    im_data = cv2.imread(filename=str(im_path))
    resized_img = cv2.resize(src=im_data, dsize=(new_width, new_height), interpolation=cv2.INTER_AREA)

    padded = np.zeros((target_height, target_width, 3), dtype=np.uint8)

    pad_top = (target_height - new_height) // 2
    pad_left = (target_width - new_width) // 2

    padded[pad_top : pad_top + new_height, pad_left : pad_left + new_width] = resized_img

    output_path = Path(f"{Path(im_path).stem}_{target_dimensions[0]}x{target_dimensions[1]}{Path(im_path).suffix}")
    cv2.imwrite(filename=str(output_path), img=padded)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Resize and pad an image to target dimensions")
    parser.add_argument("im_path", type=str, help="Path to the input image")
    parser.add_argument("-w", "--width", type=int, required=True, help="Target width for resized image")
    parser.add_argument("-h", "--height", type=int, required=True, help="Target height for resized image")

    args = parser.parse_args()
    output = resize_image(im_path=args.im_path, target_dimensions=(args.width, args.height))
    print(f"Saved resize to {output}")


if __name__ == "__main__":
    main()
