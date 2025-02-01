use anyhow::{anyhow, Result};
use polars::prelude::{DataFrame, JsonReader, SerReader};
use reqwest::Client;
use serde_json::Value;
use std::sync::Arc;
use tokio::task::JoinSet;

const DATA_URL_BASE: &str = "https://rickandmortyapi.com/api/character/";

// fn get_character_data_sync() -> Result<DataFrame> {
//     let mut all_chars = Vec::new();
//     let mut next_url = Some(String::from(DATA_URL_BASE));
//     while let Some(url) = next_url {
//         // println!("Getting {url}...");
//         let resp_json: Value = reqwest::blocking::get(&url)?.json()?;
//         let resp_chars = resp_json["results"]
//             .as_array()
//             .unwrap_or(&Vec::new())
//             .to_vec();
//         // println!("Found {} characters", resp_chars.len());
//         all_chars.extend(resp_chars);
//         // println!("Fetched {} characters in total so far...");
//         next_url = resp_json["info"]["next"].as_str().map(String::from);
//     }
//     let characters_json_str =
//         serde_json::to_string(&all_chars).expect("Failed to serialize characters to jsonstr");
//     let df = JsonReader::new(std::io::Cursor::new(characters_json_str))
//         .finish()
//         .expect("Failed to create DataFrame with characters jsonstr");
//     return Ok(df);
// }

pub async fn get_character_data_async(concurrency: usize) -> Result<DataFrame> {
    let client = Arc::new(Client::new());
    let resp_json: Value = client.get(DATA_URL_BASE).send().await?.json().await?;

    let num_pages = resp_json
        .get("info")
        .and_then(|i| i.get("pages"))
        .and_then(Value::as_i64)
        .ok_or_else(|| anyhow!("Couldn't get number of pages from response"))?;
    let pages: Vec<String> = (0..num_pages)
        .map(|i| format!("{}?page={}", DATA_URL_BASE, i + 1))
        .collect();

    let mut all_chars: Vec<Value> = vec![];
    for page_batch in pages.chunks(concurrency).map(|chunk| chunk.to_vec()) {
        let mut handles: JoinSet<Result<_>> = JoinSet::new();

        for page in page_batch {
            let client = client.clone();
            handles.spawn(async move {
                // println!("Getting {page}...");
                let resp_json: Value = client.get(&page).send().await?.json().await?;
                let results = resp_json
                    .get("results")
                    .and_then(Value::as_array)
                    .ok_or_else(|| anyhow!("Error getting results from {}", page))?;
                Ok(results.to_vec())
            });
        }

        while let Some(result) = handles.join_next().await {
            match result {
                Ok(characters) => all_chars.extend(characters?),
                Err(e) => eprintln!("Error fetching page: {e}"),
            }
        }
    }

    let df = JsonReader::new(std::io::Cursor::new(serde_json::to_vec(&all_chars)?)).finish()?;
    Ok(df)
}

pub fn get_image(character_url: &str) -> Result<image::DynamicImage> {
    let resp_json: Value = reqwest::blocking::get(character_url)?.json()?;
    let image_url = resp_json
        .get("image")
        .and_then(Value::as_str)
        .ok_or_else(|| anyhow!("Missing image URL"))?;
    let image_bytes = reqwest::blocking::get(image_url)?.bytes()?;
    Ok(image::load_from_memory(&image_bytes)?)
}

// =================== IGNORE ===================

// use anyhow::{anyhow, Result};
// use fineleg::scratchpad::{get_character_data_async, get_image};
// use polars::frame::DataFrame;
// use tokio::runtime::Runtime;

// fn main() -> Result<()> {
//     let characters_data: DataFrame = Runtime::new()?.block_on(get_character_data_async(10))?;
//     println!("{characters_data}");
//     for character_url in characters_data.column("url")?.str()? {
//         if let Some(url) = character_url {
//             println!("Getting image from {url}...");
//             let image = get_image(&url)?;
//             let output_path_base = "../common/data/images/";
//             let output_path = format!(
//                 "{}{}.jpg",
//                 output_path_base,
//                 url.split("/")
//                     .last()
//                     .ok_or_else(|| anyhow!("Failed to get character name"))?
//             );
//             image.save_with_format(output_path, image::ImageFormat::Jpeg)?;
//         }
//     }
//     Ok(())
// }
