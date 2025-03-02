use anyhow::Result;
use fineleg::pointcloud_utils::{center_pointcloud, load_las_to_df, voxel_downsample};
use fineleg::viz::{render_pointcloud_in_plotly, render_pointcloud_in_rerun};

fn main() -> Result<()> {
    // This pointcloud has about 21M points, yikes
    let pointcloud = load_las_to_df("../common/data/pointclouds/2555_1137.las")?;
    println!("Full pointcloud: {:?}", pointcloud);

    // Let's downsample so my machine survives rendering
    // let pointcloud_downsampled = pointcloud.sample_n_literal(350_000, false, false, None)?;
    let pointcloud_downsampled = voxel_downsample(pointcloud, 1_000_000)?;
    println!("Downsampled pointcloud: {:?}", pointcloud_downsampled);

    // let centered = center_pointcloud(pointcloud_downsampled)?;
    // render_pointcloud_in_plotly(pointcloud_downsampled.clone())?;

    let rec = rerun::RecordingStreamBuilder::new("switzerland").spawn()?;
    render_pointcloud_in_rerun(rec, "points", pointcloud_downsampled, None)?;

    Ok(())
}
