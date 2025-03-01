use crate::viz::render_pointcloud_in_rerun;
use anyhow::Result;
use polars::{df, prelude::DataFrame};
use rerun::RecordingStream;

pub fn load_las_to_df(path: &str) -> Result<DataFrame> {
    let mut reader = las::Reader::from_path(path)?;

    let (x, y, z) = reader.points().filter_map(Result::ok).fold(
        (vec![], vec![], vec![]),
        |(mut x, mut y, mut z), point| {
            x.push(point.x);
            y.push(point.y);
            z.push(point.z);
            (x, y, z)
        },
    );

    Ok((df!["x" => x, "y" => y, "z" => z])?)
}

pub fn render_las_in_rerun(
    rec: RecordingStream,
    entity_path: &str,
    path: &str,
    point_radius: Option<f32>,
) -> Result<()> {
    render_pointcloud_in_rerun(rec, entity_path, load_las_to_df(path)?, point_radius)?;
    Ok(())
}
