use anyhow::Result;
use las::Reader;
use polars::{df, prelude::DataFrame};

pub fn load_las() -> Result<DataFrame> {
    let mut reader = Reader::from_path("../common/data/2554_1137.las")?;

    // TODO: Surely this is horribly inefficient right. Find out how to do this
    let mut x_values = Vec::new();
    let mut y_values = Vec::new();
    let mut z_values = Vec::new();

    for point in reader.points().map(|p| p.unwrap()) {
        x_values.push(point.x);
        y_values.push(point.y);
        z_values.push(point.z);
    }

    Ok(df!(
        "x" => x_values,
        "y" => y_values,
        "z" => z_values
    )?)
}
