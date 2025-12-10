import argparse
from pathlib import Path

import cv2


def blur(input_dir: str, ksize: int = 5) -> None:
    in_path = Path(input_dir)
    out_path = in_path.parent / f"{in_path.name}_blurred_{ksize}"
    out_path.mkdir(parents=True, exist_ok=True)

    count = 0
    for img_path in in_path.glob("*.jpg"):
        img = cv2.imread(filename=str(img_path))
        if img is None:
            continue
        blurred = cv2.GaussianBlur(src=img, ksize=(ksize, ksize), sigmaX=0)
        cv2.imwrite(filename=str(out_path / img_path.name), img=blurred)
        count += 1

    print(f"Blurred {count} images -> {out_path}")


def cli() -> None:
    parser = argparse.ArgumentParser(description="Apply Gaussian blur to jpg images in a folder")
    parser.add_argument("--input-dir", required=True, help="Directory containing images to blur")
    parser.add_argument("--ksize", type=int, default=5, help="Blur kernel size (odd number)")
    args = parser.parse_args()
    blur(input_dir=args.input_dir, ksize=args.ksize)


if __name__ == "__main__":
    cli()
