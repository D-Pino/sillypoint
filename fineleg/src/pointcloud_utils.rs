use anyhow::Result;
use polars::df;
use polars::prelude::*;

// TODO: fix this. Not returning the expected number of points
pub fn voxel_downsample(pointcloud: DataFrame, num_voxels: usize) -> PolarsResult<DataFrame> {
    let num_voxels_per_axis = (num_voxels as f64).cbrt().round();

    let pointcloud_df_lazy = pointcloud.lazy();

    let pointcloud_bounds = pointcloud_df_lazy.clone().select([
        col("x").min().alias("x_min"),
        col("y").min().alias("y_min"),
        col("z").min().alias("z_min"),
        col("x").max().alias("x_max"),
        col("y").max().alias("y_max"),
        col("z").max().alias("z_max"),
    ]);

    pointcloud_df_lazy
        .cross_join(pointcloud_bounds, None)
        .with_columns([
            // TODO: Beware division by zero in these
            ((col("x_max") - col("x_min")) / lit(num_voxels_per_axis)).alias("voxel_size_x"),
            ((col("y_max") - col("y_min")) / lit(num_voxels_per_axis)).alias("voxel_size_y"),
            ((col("z_max") - col("z_min")) / lit(num_voxels_per_axis)).alias("voxel_size_z"),
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
            col("x").mean().alias("x"),
            col("y").mean().alias("y"),
            col("z").mean().alias("z"),
        ])
        .collect()
}

pub fn center_pointcloud(pointcloud: DataFrame) -> PolarsResult<DataFrame> {
    let pointcloud_df_lazy = pointcloud.lazy();

    // TODO: how much less efficient would it be if I just used col("").mean() repeatedly in
    // the main expression below, as opposed to calculating it here and "broadcasting" it with the cross_join?
    // It would be a little simpler
    let mean = pointcloud_df_lazy.clone().select([
        col("x").mean().alias("x_mean"),
        col("y").mean().alias("y_mean"),
        col("z").mean().alias("z_mean"),
    ]);

    pointcloud_df_lazy
        .cross_join(mean, None)
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
