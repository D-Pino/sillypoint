use anyhow::Result;
use fineleg::pointcloud_utils::{center_pointcloud, load_las_to_df, voxel_downsample};
use fineleg::viz::{render_pointcloud_in_plotly, render_pointcloud_in_rerun};

fn main() -> Result<()> {
    // This pointcloud has about 21M points, yikes
    let pointcloud = load_las_to_df("../common/data/pointclouds/2555_1137.las")?;

    // Let's downsample so my machine survives rendering
    let pointcloud_downsampled_r = pointcloud.sample_n_literal(350_000, false, false, None)?;
    // let pointcloud_downsampled_v = voxel_downsample(pointcloud, 100_000)?;
    let centered = center_pointcloud(pointcloud_downsampled_r)?;
    render_pointcloud_in_plotly(centered)?;

    // let rec = rerun::RecordingStreamBuilder::new("switzerland").spawn()?;
    // render_pointcloud_in_rerun(rec, "points", pointcloud_downsampled, None)?;

    Ok(())
}
