use polars::prelude::*;
use serde_json::Value;

const DATA_URL_BASE: &str = "https://rickandmortyapi.com/api/character/";

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let characters_data: DataFrame = get_character_data_seq()?;
    // println!("{characters_df}");
    for character_url in characters_data.column("url")?.str()?.into_iter() {
        if let Some(url) = character_url {
            let image = get_image(&url)?;
            let output_path_base = "../common/images/";
            let output_path = format!(
                "{}{}.jpg",
                output_path_base,
                url.split("/")
                    .last()
                    .ok_or("Failed to get character name")?
            );
            image.save_with_format(output_path, image::ImageFormat::Jpeg)?;
        }
    }
    Ok(())
}

fn get_character_data_seq() -> Result<DataFrame, reqwest::Error> {
    let mut all_chars = Vec::new();
    let mut next_url = Some(String::from(DATA_URL_BASE));
    while let Some(url) = next_url {
        // println!("Getting {url}...");
        let resp_json: Value = reqwest::blocking::get(&url)?.json()?;
        let resp_chars = resp_json["results"]
            .as_array()
            .unwrap_or(&Vec::new())
            .to_vec();
        // println!("Found {} characters", resp_chars.len());
        all_chars.extend(resp_chars);
        // println!("Fetched {} characters in total so far...", all_chars.len());
        // Cause im just messing around really
        if all_chars.len() >= 80 {
            break;
        }
        next_url = resp_json["info"]["next"].as_str().map(String::from);
    }
    let characters_json_str =
        serde_json::to_string(&all_chars).expect("Failed to serialize characters to jsonstr");
    let df = JsonReader::new(std::io::Cursor::new(characters_json_str))
        .finish()
        .expect("Failed to create DataFrame with characters jsonstr");
    return Ok(df);
}

// async fn get_data_async(base_url: &str, concurrency: usize) -> Result<DataFrame, reqwest::Error> {
//     todo!("Do this later");
// }

fn get_image(character_url: &str) -> Result<image::DynamicImage, Box<dyn std::error::Error>> {
    let resp_json: Value = reqwest::blocking::get(character_url)?.json()?;
    let image_url = resp_json
        .get("image")
        .and_then(Value::as_str)
        .ok_or("Missing image URL")?;
    let image_bytes = reqwest::blocking::get(image_url)?.bytes()?;
    let image = image::load_from_memory(&image_bytes)?;
    Ok(image)
}

