use anyhow::{anyhow, Result};
use fineleg::scratchpad::{get_character_data_async, get_image};
use polars::frame::DataFrame;
use tokio::runtime::Runtime;

fn main() -> Result<()> {
    let characters_data: DataFrame = Runtime::new()?.block_on(get_character_data_async(10))?;
    println!("{characters_data}");
    for character_url in characters_data.column("url")?.str()? {
        if let Some(url) = character_url {
            println!("Getting image from {url}...");
            let image = get_image(&url)?;
            let output_path_base = "../common/images/";
            let output_path = format!(
                "{}{}.jpg",
                output_path_base,
                url.split("/")
                    .last()
                    .ok_or_else(|| anyhow!("Failed to get character name"))?
            );
            image.save_with_format(output_path, image::ImageFormat::Jpeg)?;
        }
    }
    Ok(())
}
