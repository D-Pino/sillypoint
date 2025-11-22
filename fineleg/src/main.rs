use anyhow::Result;
use fineleg::{maptiles, pointcloud_utils, viz};
use std::path::Path;

fn main() -> Result<()> {
    // Initialize rerun
    let rec = rerun::RecordingStreamBuilder::new("switzerland").spawn()?;

    // Load pointcloud
    println!("Loading pointcloud...");
    let pointcloud = pointcloud_utils::load_las_to_df(
        "/home/pino/github/sillypoint/fineleg/data/pointcloud/urban08/urban08/sick_pointcloud.las",
        // Some(1_000_000),
        None,
    )?;
    println!("Full pointcloud: {:?}", pointcloud);

    let num_points = pointcloud.height();
    // Show progressive downsampling at 10 levels
    let num_stages = 10;
    for stage in 0..num_stages {
        let target_points = if stage == 0 {
            num_points // First stage: full pointcloud
        } else {
            // Linear interpolation of voxels_per_axis (cube root), then cube it back
            let max_voxels_per_axis = (num_points as f64).cbrt();
            let min_voxels_per_axis = (num_points as f64 * 0.1).cbrt();
            let voxels_per_axis = max_voxels_per_axis
                - ((max_voxels_per_axis - min_voxels_per_axis) * stage as f64
                    / (num_stages - 1) as f64);
            (voxels_per_axis.powi(3).round()) as usize
        };

        println!("Stage {}: targeting {} points", stage, target_points);
        let new_pointcloud = if stage == 0 {
            pointcloud.clone()
        } else {
            pointcloud_utils::voxel_downsample(&pointcloud, target_points)?
        };
        println!("Stage {} actual points: {}", stage, new_pointcloud.height());

        viz::send_pointcloud_to_rerun(rec.clone(), "points", &new_pointcloud, None)?;
    }

    Ok(())
}

// #[tokio::main]
// async fn main() -> Result<()> {
//     let base_dir = Path::new("/home/pino/github/sillypoint/fineleg/data/osm_test");

//     let center_lat = 48.85837;
//     let center_lon = 2.294481;
//     let delta = 0.003; // degrees

//     let min_lat = center_lat - delta;
//     let max_lat = center_lat + delta;
//     let min_lon = center_lon - delta;
//     let max_lon = center_lon + delta;

//     let zoom = 16;
//     let concurrency = 2;

//     maptiles::download_tiles_for_bbox_async(
//         min_lat,
//         min_lon,
//         max_lat,
//         max_lon,
//         zoom,
//         concurrency,
//         base_dir,
//     )
//     .await?;

//     Ok(())
// }
