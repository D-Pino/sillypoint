import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import pydeck
import streamlit as st
import streamlit.components.v1 as components

from run_depth_inference import depth_map_to_point_cloud, get_depth

DATA_DIR = f"{os.getenv('REPO_ROOT', Path(__file__).parent)}/common/data"


# TODO: Reevaluate streamlit overall, not loving the pointcloud options
def streamlit_viz():
    # TODO: Add button to upload image

    im_path = Path(DATA_DIR) / "images/stock_woman.jpg"
    st.image(str(im_path), caption="Original")

    depth_map, focal_length = get_depth(im_path)
    pointcloud_df = depth_map_to_point_cloud(depth_map, focal_length)

    target = [pointcloud_df.x.mean(), pointcloud_df.y.mean(), pointcloud_df.z.mean()]

    point_cloud_layer = pydeck.Layer(
        "PointCloudLayer",
        data=pointcloud_df.to_dict(),
        get_position=["x", "y", "z"],
        get_color=[255, 255, 255],
        get_normal=[0, 0, 15],
        auto_highlight=True,
        pickable=True,
        point_size=3,
    )

    view_state = pydeck.ViewState(target=target, controller=True, rotation_x=15, rotation_orbit=30, zoom=5.3)
    view = pydeck.View(type="OrbitView", controller=True)

    deck = pydeck.Deck(point_cloud_layer, initial_view_state=view_state, views=[view])
    deck_html_str = deck.to_html(as_string=True, css_background_color="#add8e6")
    components.html(deck_html_str, height=800)


def plotly_viz(pointcloud_df: pd.DataFrame) -> None:
    fig = px.scatter_3d(pointcloud_df, x="x", y="y", z="z", title="Point Cloud Visualization")
    fig.update_traces(marker=dict(size=1))
    fig.show()


def main() -> None:
    im_path = Path(DATA_DIR) / "images/stock_deer.jpg"
    depth_map, focal_length = get_depth(im_path)
    pointcloud_df = depth_map_to_point_cloud(depth_map, focal_length)
    plotly_viz(pointcloud_df)


if __name__ == "__main__":
    main()
