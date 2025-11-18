use anyhow::Result;
use fineleg::maptiles::download_tiles_for_bbox_async;
use std::path::Path;

// fn main() -> Result<()> {
//     // Initialize rerun
//     let rec = rerun::RecordingStreamBuilder::new("switzerland").spawn()?;
//
//     let pointcloud = load_las_to_df(
//         "/home/pino/github/sillypoint/fineleg/data/pointcloud/urban08/urban08/sick_pointcloud.las",
//     )?;
//     println!("Full pointcloud: {:?}", pointcloud);
//
//     for _ in 0..10 {
//         let pointcloud_downsampled = pointcloud.sample_n_literal(50_000, false, false, None)?;
//         render_pointcloud_in_rerun(rec.clone(), "points", pointcloud_downsampled, None)?;
//     }
//
//     // let centered = center_pointcloud(pointcloud_downsampled)?;
//     // render_pointcloud_in_plotly(pointcloud_downsampled.clone())?;
//
//     // render_pointcloud_in_rerun(rec, "points", pointcloud_downsampled_2, None)?;
//
//     Ok(())
// }

#[tokio::main]
async fn main() -> Result<()> {
    let base_dir = Path::new("/home/pino/github/sillypoint/fineleg/data/osm_test");

    let center_lat = 48.85837;
    let center_lon = 2.294481;
    let delta = 0.003; // degrees

    let min_lat = center_lat - delta;
    let max_lat = center_lat + delta;
    let min_lon = center_lon - delta;
    let max_lon = center_lon + delta;

    let zoom = 16;
    let concurrency = 2;

    download_tiles_for_bbox_async(
        min_lat,
        min_lon,
        max_lat,
        max_lon,
        zoom,
        concurrency,
        base_dir,
    )
    .await?;

    Ok(())
}
