use crate::pointcloud_utils::load_las_to_df;
use anyhow::Result;
use plotly::common::{Marker, Mode};
use plotly::layout::{AspectMode, AspectRatio, LayoutScene};
use plotly::{Layout, Plot, Scatter3D};
use polars::prelude::*;
use rerun::RecordingStream;

pub fn render_pointcloud_in_rerun(
    rec: RecordingStream,
    entity_path: &str,
    pointcloud: DataFrame,
    point_radius: Option<f32>,
) -> Result<()> {
    let x = pointcloud.column("x")?.f32()?;
    let y = pointcloud.column("y")?.f32()?;
    let z = pointcloud.column("z")?.f32()?;
    let positions = x
        .into_iter()
        .zip(y)
        .zip(z)
        .filter_map(|((x, y), z)| Some((x?, y?, z?)));

    let r = pointcloud.column("r")?.u8()?;
    let g = pointcloud.column("g")?.u8()?;
    let b = pointcloud.column("b")?.u8()?;
    let colors = r
        .into_iter()
        .zip(g)
        .zip(b)
        .filter_map(|((r, g), b)| Some(rerun::Color::from_rgb(r?, g?, b?)));

    let rerun_pointcloud = rerun::Points3D::new(positions)
        .with_colors(colors)
        .with_radii([point_radius.unwrap_or(0.2)]);
    rec.log(entity_path, &rerun_pointcloud)?;
    Ok(())
}

pub fn render_las_in_rerun(
    rec: RecordingStream,
    entity_path: &str,
    path: &str,
    point_radius: Option<f32>,
) -> Result<()> {
    render_pointcloud_in_rerun(rec, entity_path, load_las_to_df(path)?, point_radius)?;
    Ok(())
}

pub fn render_pointcloud_in_plotly(pointcloud: DataFrame) -> Result<()> {
    // Try not to render > ~100k points with this

    // Get maxs and mins, for miltiple reasons
    // TODO: Can I optimize this
    let x_min = pointcloud.column("x")?.f64()?.min().unwrap();
    let x_max = pointcloud.column("x")?.f64()?.max().unwrap();
    let y_min = pointcloud.column("y")?.f64()?.min().unwrap();
    let y_max = pointcloud.column("y")?.f64()?.max().unwrap();
    let z_min = pointcloud.column("z")?.f64()?.min().unwrap();
    let z_max = pointcloud.column("z")?.f64()?.max().unwrap();

    // println!("x_min: {}", x_min);
    // println!("x_max: {}", x_max);
    // println!("y_min: {}", y_min);
    // println!("y_max: {}", y_max);
    // println!("z_min: {}", z_min);
    // println!("z_max: {}", z_max);

    // Centers, for the camera
    let cx = (x_min + x_max) / 2.0;
    let cy = (y_min + y_max) / 2.0;
    let cz = (z_min + z_max) / 2.0;

    // println!("cx: {}", cx);
    // println!("cy: {}", cy);
    // println!("cz: {}", cz);

    // Ranges, for both the camera and the aspect ratio
    let x_range = x_max - x_min;
    let y_range = y_max - y_min;
    let z_range = z_max - z_min;
    // println!("x_range: {}", x_range);
    // println!("y_range: {}", y_range);
    // println!("z_range: {}", z_range);

    // let max_range = x_range.max(y_range).max(z_range);
    // println!("max_range: {}", max_range);

    // let camera = Camera::new()
    // The actual data to plot
    let x = pointcloud.column("x")?.f64()?.to_vec();
    let y = pointcloud.column("y")?.f64()?.to_vec();
    let z = pointcloud.column("z")?.f64()?.to_vec();
    let trace = Scatter3D::new(x, y, z)
        .mode(Mode::Markers)
        .marker(Marker::new().size(2).color("#7851A9").opacity(0.3));

    // Layout lets me set the window size, camera position, and aspect ratio
    let layout = Layout::new().width(2400).height(1200).scene(
        LayoutScene::new()
            .aspect_mode(AspectMode::Manual)
            .aspect_ratio(AspectRatio::from((x_range, y_range, z_range))), // .camera(
                                                                           // Camera::new()
                                                                           // .eye(Eye::from((500.0, 500.0, 100.0))) // this doesn't work really for some reason
                                                                           // .center(CameraCenter::from((cx, cy, cz))),
                                                                           // ),
    );

    let mut plot = Plot::new();
    plot.set_layout(layout);
    plot.add_trace(trace);
    plot.show();

    Ok(())
}
