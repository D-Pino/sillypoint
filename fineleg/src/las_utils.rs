use anyhow::Result;
use las::Reader;
use polars::{df, prelude::DataFrame};
use rerun::{RecordingStream, Vec3D};

pub fn load_las_to_df(path: &str) -> Result<DataFrame> {
    let mut reader = Reader::from_path(path)?;

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

pub fn render_las_in_rerun(rec: RecordingStream, entity_path: &str, path: &str) -> Result<()> {
    let mut reader = Reader::from_path(path)?;
    let points: Vec<Vec3D> = reader
        .points()
        .filter_map(Result::ok)
        .map(|p| Vec3D::new(p.x as f32, p.y as f32, p.z as f32))
        .collect();
    rec.log(
        entity_path,
        &rerun::Points3D::new(points).with_radii([0.08]),
    );

    Ok(())
}
