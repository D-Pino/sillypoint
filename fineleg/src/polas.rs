use anyhow::Result;
use las::Reader;
use polars::{df, prelude::DataFrame};

pub fn load_las_file(path: &str) -> Result<DataFrame> {
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
