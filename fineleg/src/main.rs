use anyhow::Result;
use fineleg::las_utils::{load_las_to_df, render_las_in_rerun};

fn main() -> Result<()> {
    let pointcloud = load_las_to_df("../common/data/pointclouds/2555_1137.las")?;
    println!("{:?}", pointcloud);


    let rec = rerun::RecordingStreamBuilder::new("pointcloud").spawn()?;
    render_las_in_rerun(rec, "points", "../common/data/pointclouds/2555_1137.las")?;

    Ok(())
}
