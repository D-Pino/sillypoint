import os
from pathlib import Path

import depth_pro
import numpy as np
import pandas as pd
import torch
from depth_pro.depth_pro import DepthProConfig

DATA_DIR = f"{os.getenv('REPO_ROOT', Path(__file__).parent)}/common/data"

# Same as default but with different file location for checkpoints
checkpoints_dir = Path(__file__).parent / "checkpoints"
MODEL_CONFIG = DepthProConfig(
    patch_encoder_preset="dinov2l16_384",
    image_encoder_preset="dinov2l16_384",
    checkpoint_uri=str(checkpoints_dir / "depth_pro.pt"),
    decoder_features=256,
    use_fov_head=True,
    fov_encoder_preset="dinov2l16_384",
)


def get_depth(im_path: str | Path) -> tuple[pd.DataFrame, float]:
    """Run inference on the specified image and return a tuple of the depth map and the focal length"""

    # Let's use some basic caching to make dev less painful
    output_dir = im_path.parent.parent / "pointclouds"
    depth_map_output_path = output_dir / f"{Path(im_path).stem}_depth.npy"
    focal_length_output_path = output_dir / f"{Path(im_path).stem}_fx.txt"
    if depth_map_output_path.exists() and focal_length_output_path.exists():
        depth = pd.DataFrame(data=np.load(file=depth_map_output_path))
        with open(file=focal_length_output_path, mode="r") as f:
            focal_length = float(f.read())
        return depth, focal_length

    # Load model and preprocessing transform
    model, transform = depth_pro.create_model_and_transforms(
        config=MODEL_CONFIG,
        device=torch.device("cuda"),
    )
    model.eval()

    # Load and preprocess an image.
    image, _, f_px = depth_pro.load_rgb(path=im_path)
    image = transform(inputs=image)

    # Run inference.
    prediction = model.infer(image=image, f_px=f_px)
    depth = pd.DataFrame(data=prediction["depth"].cpu().numpy())
    focal_length = prediction["focallength_px"].item()

    # Save the depth map and focal length for caching purposes
    output_dir.mkdir(parents=True, exist_ok=True)
    np.save(file=depth_map_output_path, arr=depth)
    with focal_length_output_path.open(mode="w") as f:
        f.write(str(focal_length))

    return (depth, focal_length)


def depth_map_to_point_cloud(depth_map: pd.DataFrame, focal_length: float) -> pd.DataFrame:
    # We assume square pixels, ie fx=fy
    fx = fy = focal_length

    height, width = depth_map.shape
    # We assume the principal point is at the center of the image
    cx = width / 2
    cy = height / 2

    z = depth_map.to_numpy()
    u, v = np.indices((height, width))

    # Got these formulae for the pinhole camera model from the internet
    x = (u - cx) * (z / fx)
    y = (v - cy) * (z / fy)

    return pd.DataFrame(data={"x": x.flatten(), "y": y.flatten(), "z": z.flatten()})


# TODO: Add CLI args to this
def main() -> None:
    im_path = Path(DATA_DIR) / "images/stock_woman.jpg"
    depth, focal_length = get_depth(im_path=im_path)
    pointcloud_df = depth_map_to_point_cloud(depth_map=depth, focal_length=focal_length)
    print(pointcloud_df.head())


if __name__ == "__main__":
    main()
