use anyhow::Result;
use polars::df;
use polars::prelude::*;

pub fn voxel_downsample(
    pointcloud: &DataFrame,
    num_voxels_in_grid: usize,
) -> PolarsResult<DataFrame> {
    let num_voxels_per_axis = (num_voxels_in_grid as f64).cbrt().round();

    // We take a reference for API ergonomics, but we must clone locally because lazy() consumes the DataFrame.
    // The clone is cheap (reference counted), and this prevents the caller from having to clone.
    // TODO: Beware division by zero in here
    pointcloud
        .clone()
        .lazy()
        // Remove outliers so the voxel grid isn't skewed by a few points
        .filter(
            col("x")
                .gt(col("x").quantile(lit(0.05), QuantileMethod::Nearest))
                .and(col("x").lt(col("x").quantile(lit(0.95), QuantileMethod::Nearest)))
                .and(col("y").gt(col("y").quantile(lit(0.05), QuantileMethod::Nearest)))
                .and(col("y").lt(col("y").quantile(lit(0.95), QuantileMethod::Nearest)))
                .and(col("z").gt(col("z").quantile(lit(0.05), QuantileMethod::Nearest)))
                .and(col("z").lt(col("z").quantile(lit(0.95), QuantileMethod::Nearest))),
        )
        // Calculate size of voxels along each axis, essentially creating the voxel grid
        .with_columns([
            ((col("x").max() - col("x").min()) / lit(num_voxels_per_axis)).alias("voxel_size_x"),
            ((col("y").max() - col("y").min()) / lit(num_voxels_per_axis)).alias("voxel_size_y"),
            ((col("z").max() - col("z").min()) / lit(num_voxels_per_axis)).alias("voxel_size_z"),
        ])
        // Calculate the index of the voxel that each point should belong to
        .with_columns([
            ((col("x") - col("x").min()) / col("voxel_size_x"))
                .floor()
                .cast(DataType::Int64)
                .alias("voxel_idx_x"),
            ((col("y") - col("y").min()) / col("voxel_size_y"))
                .floor()
                .cast(DataType::Int64)
                .alias("voxel_idx_y"),
            ((col("z") - col("z").min()) / col("voxel_size_z"))
                .floor()
                .cast(DataType::Int64)
                .alias("voxel_idx_z"),
        ])
        // Group points by voxel
        .group_by(["voxel_idx_x", "voxel_idx_y", "voxel_idx_z"])
        // Calculate the voxel values by taking the mean of the points in the voxel
        .agg([
            col("x").mean().alias("x_voxel_value"),
            col("y").mean().alias("y_voxel_value"),
            col("z").mean().alias("z_voxel_value"),
            col("r").mean().alias("r_voxel_value"),
            col("g").mean().alias("g_voxel_value"),
            col("b").mean().alias("b_voxel_value"),
        ])
        // Select/rename columns we care about, cast rgb back to u8
        .select([
            col("x_voxel_value").alias("x"),
            col("y_voxel_value").alias("y"),
            col("z_voxel_value").alias("z"),
            col("r_voxel_value").cast(DataType::UInt8).alias("r"),
            col("g_voxel_value").cast(DataType::UInt8).alias("g"),
            col("b_voxel_value").cast(DataType::UInt8).alias("b"),
        ])
        .collect()
}

pub fn center_pointcloud(pointcloud: DataFrame) -> PolarsResult<DataFrame> {
    pointcloud
        .lazy()
        .with_columns([
            (col("x") - col("x").mean()).alias("x"),
            (col("y") - col("y").mean()).alias("y"),
            (col("z") - col("z").mean()).alias("z"),
        ])
        .collect()
}

pub fn load_las_to_df(path: &str, max_points: Option<usize>) -> Result<DataFrame> {
    let mut reader = las::Reader::from_path(path)?;
    let points = reader.points().take(max_points.unwrap_or(usize::MAX));

    let (x, y, z, r, g, b) = points.filter_map(Result::ok).fold(
        (vec![], vec![], vec![], vec![], vec![], vec![]),
        |(mut x, mut y, mut z, mut r, mut g, mut b), point| {
            x.push(point.x as f32);
            y.push(point.y as f32);
            z.push(point.z as f32);

            if let Some(color) = point.color {
                r.push(color.red as u8);
                g.push(color.green as u8);
                b.push(color.blue as u8);
            } else {
                r.push(0);
                g.push(0);
                b.push(0);
            }

            (x, y, z, r, g, b)
        },
    );

    Ok((df!["x" => x, "y" => y, "z" => z, "r" => r, "g" => g, "b" => b])?)
}

#[derive(Debug, serde::Deserialize)]
struct Vertex {
    x: f32,
    y: f32,
    z: f32,
    red: u8,
    green: u8,
    blue: u8,
}

pub fn load_ply_to_df(path: &str, max_points: Option<usize>) -> Result<DataFrame> {
    let file = std::fs::File::open(path)?;
    let reader = std::io::BufReader::new(file);

    let mut ply_reader = serde_ply::PlyReader::from_reader(reader)?;
    let vertices: Vec<Vertex> = ply_reader.next_element()?;

    let (x, y, z, r, g, b) = vertices
        .into_iter()
        .take(max_points.unwrap_or(usize::MAX))
        .fold(
            (vec![], vec![], vec![], vec![], vec![], vec![]),
            |(mut x, mut y, mut z, mut r, mut g, mut b), vertex| {
                x.push(vertex.x);
                y.push(vertex.y);
                z.push(vertex.z);
                r.push(vertex.red);
                g.push(vertex.green);
                b.push(vertex.blue);
                (x, y, z, r, g, b)
            },
        );

    Ok((df!["x" => x, "y" => y, "z" => z, "r" => r, "g" => g, "b" => b])?)
}
