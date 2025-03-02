use anyhow::Result;
use polars::df;
use polars::prelude::*;

pub fn voxel_downsample(
    pointcloud: DataFrame,
    num_voxels_in_grid: usize,
) -> PolarsResult<DataFrame> {
    // NB: This is a little naive, the caller specifies the number of voxels in the grid, but
    // can't (yet) specify how many voxels with actual points in them will be returned
    // TODO: upgrade this so that user can specify number of points in final pointcloud (not trivial)
    let num_voxels_per_axis = (num_voxels_in_grid as f64).cbrt().round();

    let pointcloud_df_lazy = pointcloud.lazy();

    // These are one-off calculations, so we do them separately and broadcast them to the df with cross_join
    let pointcloud_bounds = pointcloud_df_lazy
        .clone()
        .select([
            col("x").min().alias("x_min"),
            col("y").min().alias("y_min"),
            col("z").min().alias("z_min"),
            col("x").max().alias("x_max"),
            col("y").max().alias("y_max"),
            col("z").max().alias("z_max"),
        ])
        .with_columns([
            (col("x_max") - col("x_min")).alias("x_range"),
            (col("y_max") - col("y_min")).alias("y_range"),
            (col("z_max") - col("z_min")).alias("z_range"),
        ]);

    // TODO: Beware division by zero in here
    pointcloud_df_lazy
        .cross_join(pointcloud_bounds, None)
        .with_columns([
            ((col("x_range")) / lit(num_voxels_per_axis)).alias("voxel_size_x"),
            ((col("y_range")) / lit(num_voxels_per_axis)).alias("voxel_size_y"),
            ((col("z_range")) / lit(num_voxels_per_axis)).alias("voxel_size_z"),
        ])
        .with_columns([
            ((col("x") - col("x_min")) / col("voxel_size_x"))
                .floor()
                .cast(DataType::Int64)
                .alias("voxel_idx_x"),
            ((col("y") - col("y_min")) / col("voxel_size_y"))
                .floor()
                .cast(DataType::Int64)
                .alias("voxel_idx_y"),
            ((col("z") - col("z_min")) / col("voxel_size_z"))
                .floor()
                .cast(DataType::Int64)
                .alias("voxel_idx_z"),
        ])
        .group_by(["voxel_idx_x", "voxel_idx_y", "voxel_idx_z"])
        .agg([
            col("x").mean().alias("x_voxel_value"),
            col("y").mean().alias("y_voxel_value"),
            col("z").mean().alias("z_voxel_value"),
        ])
        .select([
            col("x_voxel_value").alias("x"),
            col("y_voxel_value").alias("y"),
            col("z_voxel_value").alias("z"),
        ])
        .collect()
}

pub fn center_pointcloud(pointcloud: DataFrame) -> PolarsResult<DataFrame> {
    let pointcloud_df_lazy = pointcloud.lazy();

    // These are one-off calculations, so we do them separately and broadcast them to the df below with cross_join
    let means = pointcloud_df_lazy.clone().select([
        col("x").mean().alias("x_mean"),
        col("y").mean().alias("y_mean"),
        col("z").mean().alias("z_mean"),
    ]);

    pointcloud_df_lazy
        .cross_join(means, None)
        .with_columns([
            (col("x") - col("x_mean")).alias("x"),
            (col("y") - col("y_mean")).alias("y"),
            (col("z") - col("z_mean")).alias("z"),
        ])
        .collect()
}
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
