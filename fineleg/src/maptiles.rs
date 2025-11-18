use anyhow::Result;
use reqwest::Client;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tokio::task::JoinSet;

const USER_AGENT: &str = "fineleg/0.1.0 (danielpino1121@gmail.com)";
const MAX_TILES_PER_INVOCATION: usize = 10;

/// Converts latitude/longitude coordinates to tile x/y indices at a given zoom level.
/// Uses the Web Mercator projection (EPSG:3857).
fn lon_lat_to_tile_xy(lat: f64, lon: f64, zoom: u8) -> (u32, u32) {
    let lat_rad = lat.to_radians();
    let n = 2f64.powi(zoom as i32);
    let x = ((lon + 180.0) / 360.0 * n) as u32;
    let y = ((1.0 - (lat_rad.tan() + 1.0 / lat_rad.cos()).ln() / std::f64::consts::PI) / 2.0 * n)
        as u32;
    (x, y)
}

/// Represents a single map tile identified by zoom level and x/y coordinates.
#[derive(Debug, Clone, Copy)]
pub struct Tile {
    pub z: u8,
    pub x: u32,
    pub y: u32,
}

/// Computes all tiles needed to cover a bounding box at a given zoom level.
/// Returns tiles in the Web Mercator tile coordinate system.
fn tiles_for_bbox(min_lat: f64, min_lon: f64, max_lat: f64, max_lon: f64, zoom: u8) -> Vec<Tile> {
    let (min_x, max_y) = lon_lat_to_tile_xy(min_lat, min_lon, zoom);
    let (max_x, min_y) = lon_lat_to_tile_xy(max_lat, max_lon, zoom);

    let x_start = min_x.min(max_x);
    let x_end = min_x.max(max_x);
    let y_start = min_y.min(max_y);
    let y_end = min_y.max(max_y);

    let mut tiles = Vec::new();
    for x in x_start..=x_end {
        for y in y_start..=y_end {
            tiles.push(Tile { z: zoom, x, y });
        }
    }
    tiles
}

/// Constructs the OpenStreetMap tile URL for a given tile.
fn tile_url(tile: Tile) -> String {
    format!(
        "https://tile.openstreetmap.org/{}/{}/{}.png",
        tile.z, tile.x, tile.y
    )
}

/// Constructs the output file path for a tile, organized as `base_dir/z/x/y.png`.
/// Creates necessary directories if they don't exist.
fn tile_output_path(base_dir: &Path, tile: Tile) -> Result<PathBuf> {
    let mut path = PathBuf::from(base_dir);
    path.push(tile.z.to_string());
    path.push(tile.x.to_string());
    std::fs::create_dir_all(&path)?;
    path.push(format!("{}.png", tile.y));
    Ok(path)
}

/// Downloads OpenStreetMap tiles for a bounding box at a given zoom level.
///
/// This function downloads tiles concurrently with a configurable concurrency limit.
/// Tiles are saved to `base_dir/z/x/y.png`.
///
/// # Arguments
/// * `min_lat` - Minimum latitude of the bounding box
/// * `min_lon` - Minimum longitude of the bounding box
/// * `max_lat` - Maximum latitude of the bounding box
/// * `max_lon` - Maximum longitude of the bounding box
/// * `zoom` - Zoom level (0-19 typically)
/// * `concurrency` - Maximum number of concurrent downloads
/// * `base_dir` - Base directory where tiles will be saved
///
/// # Example
/// ```no_run
/// use std::path::Path;
/// # use anyhow::Result;
/// # async fn example() -> Result<()> {
/// // Download tiles for San Francisco at zoom level 13
/// download_tiles_for_bbox_async(
///     37.7, -122.5,  // min_lat, min_lon
///     37.8, -122.4,  // max_lat, max_lon
///     13,            // zoom
///     5,             // concurrency
///     Path::new("./tiles")
/// ).await?;
/// # Ok(())
/// # }
/// ```
pub async fn download_tiles_for_bbox_async(
    min_lat: f64,
    min_lon: f64,
    max_lat: f64,
    max_lon: f64,
    zoom: u8,
    concurrency: usize,
    base_dir: &Path,
) -> Result<()> {
    let mut tiles = tiles_for_bbox(min_lat, min_lon, max_lat, max_lon, zoom);
    if tiles.len() > MAX_TILES_PER_INVOCATION {
        tiles.truncate(MAX_TILES_PER_INVOCATION);
    }
    println!("Downloading {} tiles", tiles.len());
    let client = Arc::new(Client::builder().user_agent(USER_AGENT).build()?);

    for tile_batch in tiles.chunks(concurrency) {
        let mut handles: JoinSet<Result<()>> = JoinSet::new();

        for &tile in tile_batch {
            let client = client.clone();
            let base_dir = base_dir.to_path_buf();

            handles.spawn(async move {
                let url = tile_url(tile);
                let response = client.get(&url).send().await?;
                let bytes = response.bytes().await?;

                let output_path = tile_output_path(&base_dir, tile)?;
                tokio::fs::write(&output_path, &bytes).await?;

                Ok(())
            });
        }

        while let Some(result) = handles.join_next().await {
            match result {
                Ok(tile_result) => {
                    if let Err(e) = tile_result {
                        eprintln!("Error downloading tile: {e}");
                    }
                }
                Err(e) => eprintln!("Task join error: {e}"),
            }
        }
    }

    Ok(())
}
