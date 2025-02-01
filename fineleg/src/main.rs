use anyhow::Result;
use fineleg::polas::load_las_file;

fn main() -> Result<()> {
    let pointcloud = load_las_file("../common/data/pointclouds/2554_1137.las")?;
    println!("{pointcloud}");
    Ok(())
}
