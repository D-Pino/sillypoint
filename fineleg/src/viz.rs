use anyhow::Result;
use polars::prelude::DataFrame;
use rerun::{RecordingStream, Vec3D};

pub fn render_pointcloud_in_rerun(
    rec: RecordingStream,
    entity_path: &str,
    pointcloud: DataFrame,
    point_radius: Option<f32>,
) -> Result<()> {
    let points: Vec<Vec3D> = pointcloud
        .column("x")?
        .f32()?
        .into_iter()
        .zip(pointcloud.column("y")?.f32()?)
        .zip(pointcloud.column("z")?.f32()?)
        .map(|((x, y), z)| Vec3D::new(x.unwrap(), y.unwrap(), z.unwrap()))
        .collect();
    let rerun_pointcloud = rerun::Points3D::new(points).with_radii([point_radius.unwrap_or(1.0)]);
    rec.log(entity_path, &rerun_pointcloud)?;
    Ok(())
}
