use anyhow::Result;
use fineleg::las_utils::load_las_to_df;
use fineleg::viz::render_pointcloud_in_rerun;
use polars::prelude::*;

fn main() -> Result<()> {
    // This pointcloud has about 21M points, yikes
    let pointcloud = load_las_to_df("../common/data/pointclouds/2555_1137.las")?;
    println!("{:?}", pointcloud);

    // Let's downsample so my machine survives rendering
    // let pointcloud_downsampled = pointcloud.sample_n_literal(100_000, false, false, None)?;
    let pointcloud_downsampled = voxel_downsample(pointcloud, 100_000)?;
    println!("{:?}", pointcloud_downsampled);

    // let rec = rerun::RecordingStreamBuilder::new("switzerland").spawn()?;
    // render_pointcloud_in_rerun(rec, "points", pointcloud, None)?;

    Ok(())
}

fn voxel_downsample(pointcloud: DataFrame, num_voxels: u32) -> PolarsResult<DataFrame> {
    let num_voxels_per_axis = (num_voxels as f32).cbrt().round() as f64;

    let pointcloud_df_lazy = pointcloud.lazy();

    let pointcloud_bounds = pointcloud_df_lazy.clone().select([
        col("x").min().alias("min_x"),
        col("y").min().alias("min_y"),
        col("z").min().alias("min_z"),
        col("x").max().alias("max_x"),
        col("y").max().alias("max_y"),
        col("z").max().alias("max_z"),
    ]);

    pointcloud_df_lazy
        .cross_join(pointcloud_bounds.lazy(), None)
        .with_columns([
            // Beware division by zero in these
            ((col("max_x") - col("min_x")) / lit(num_voxels_per_axis)).alias("voxel_size_x"),
            ((col("max_y") - col("min_y")) / lit(num_voxels_per_axis)).alias("voxel_size_y"),
            ((col("max_z") - col("min_z")) / lit(num_voxels_per_axis)).alias("voxel_size_z"),
        ])
        .with_columns([
            ((col("x") - col("min_x")) / col("voxel_size_x"))
                .floor()
                .cast(DataType::Int64)
                .alias("voxel_idx_x"),
            ((col("y") - col("min_y")) / col("voxel_size_y"))
                .floor()
                .cast(DataType::Int64)
                .alias("voxel_idx_y"),
            ((col("z") - col("min_z")) / col("voxel_size_z"))
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
