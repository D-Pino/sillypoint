from pathlib import Path
import depth_pro
from depth_pro.depth_pro import DepthProConfig
import torch
import numpy as np
import numpy.typing as nptyping
import streamlit as st
# import pydeck
# import pandas as pd
# import streamlit.components.v1 as components


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


def get_depth(im_path: str | Path) -> tuple[nptyping.NDArray, nptyping.NDArray]:
    """Run inference on the specified image and return a tuple of the image and depth"""
    im_np_path = Path(f"{Path(im_path).stem}.npy")
    depth_path = Path(f"{Path(im_path).stem}_depth.npy")
    if im_np_path.exists() and depth_path.exists():
        image = np.load(im_np_path)
        depth = np.load(depth_path)
        return image, depth

    # Load model and preprocessing transform
    model, transform = depth_pro.create_model_and_transforms(
        config=MODEL_CONFIG,
        device=torch.device("cuda"),
    )
    model.eval()

    # Load and preprocess an image.
    image, _, f_px = depth_pro.load_rgb(im_path)
    image = transform(image)

    # Run inference.
    prediction = model.infer(image, f_px=f_px)
    depth = prediction["depth"]

    image_np = np.transpose(image.cpu().numpy(), (1, 2, 0))
    depth_np = depth.cpu().numpy()
    np.save(im_np_path, image_np)
    np.save(depth_path, depth_np)
    return (image_np, depth_np)


def depth_to_point_cloud_simple(depth_image: nptyping.NDArray):
    raise NotImplementedError("This function is not implemented yet")


def main() -> None:
    im_path = Path(__file__).parent / "horses.jpg"
    st.image(str(im_path), caption="Original")
    image, depth = get_depth(im_path)
    st.image(image, caption="From numpy", clamp=True)
   
   
    # pointcloud = depth_to_point_cloud_simple(depth)
    # pointcloud_df = pd.DataFrame(pointcloud, columns=["x", "y", "z"])
    # target = [pointcloud_df.x.mean(), pointcloud_df.y.mean(), pointcloud_df.z.mean()]
    # point_cloud_layer = pydeck.Layer(
    #     "PointCloudLayer",
    #     data=pointcloud_df,
    #     get_position=["x", "y", "z"],
    #     get_color=[255, 255, 255],
    #     get_normal=[0, 0, 15],
    #     auto_highlight=True,
    #     pickable=True,
    #     point_size=3,
    # )

    # view_state = pydeck.ViewState(target=target, controller=True, rotation_x=15, rotation_orbit=30, zoom=5.3)
    # view = pydeck.View(type="OrbitView", controller=True)

    # deck = pydeck.Deck(point_cloud_layer, initial_view_state=view_state, views=[view])
    # deck_html_str = deck.to_html(as_string=True, css_background_color="#add8e6")
    # components.html(deck_html_str, height=600)


if __name__ == "__main__":
    main()
