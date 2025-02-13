import cv2
from pathlib import Path
import click
import numpy as np

def get_image_dimensions(im_path: str | Path) -> tuple[int, int] | None:
    im_data = cv2.imread(str(im_path))
    return im_data.shape[:2]

def resize_image(im_path: str | Path, target_dimensions: tuple[int, int] = (640, 640)) -> Path:
    height, width = get_image_dimensions(im_path)
    target_width, target_height = target_dimensions
    scale = min(target_width / width, target_height / height)
    new_width, new_height = int(width * scale), int (height * scale)


    im_data = cv2.imread(str(im_path))
    resized_img = cv2.resize(im_data, (new_width, new_height), interpolation=cv2.INTER_AREA)

    padded = np.zeros((target_height, target_width, 3), dtype=np.uint8)

    pad_top = (target_height - new_height) // 2
    pad_left = (target_width - new_width) // 2

    padded[pad_top:pad_top+new_height, pad_left:pad_left+new_width] = resized_img

    output_path = Path(f"{Path(im_path).stem}_{target_dimensions[0]}x{target_dimensions[1]}{Path(im_path).suffix}")
    cv2.imwrite(str(output_path), padded)
    return output_path

@click.command()
@click.argument("im_path", type=click.Path(exists=True))
@click.option("--width", "-w", type=int, required=True, help="Target width for resized image")
@click.option("--height", "-h", type=int, required=True, help="Target height for resized image")
def main(im_path: str | Path, width: int, height: int) -> None:
    output = resize_image(im_path, (width, height))
    print(f"Saved resize to {output}")

if __name__ == "__main__":
    main()
