use anyhow::{anyhow, Result};
use futures::future::join_all;
use polars::prelude::*;
use reqwest::Client;
use serde_json::Value;
use tokio::task::JoinHandle;

const DATA_URL_BASE: &str = "https://rickandmortyapi.com/api/character/";

#[tokio::main]
async fn main() -> Result<()> {
    // let characters_data: DataFrame = get_character_data_sync()?; // Time elapsed: 16.446295416s
    let characters_data: DataFrame = get_character_data_async(10).await?; // Time elapsed: 2.594620419s
    println!("{characters_data}");
    
    // for character_url in characters_data.column("url")?.str()? {
    //     let handle = tokio::task::spawn_blocking(move || {
    //         if let Some(url) = character_url {
    //             let image = get_image(&url).unwrap();
    //             let output_path_base = "../common/images/";
    //             let output_path = format!(
    //                 "{}{}.jpg",
    //                 output_path_base,
    //                 url.split("/")
    //                     .last()
    //                     .ok_or_else(|| anyhow!("Failed to get character name")).unwrap()
    //             );
    //             image.save_with_format(output_path, image::ImageFormat::Jpeg).unwrap();
    //         }
    //     });
    //     handle.await?;
    // }
    Ok(())
}

fn get_character_data_sync() -> Result<DataFrame> {
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
        // println!("Fetched {} characters in total so far...");
        next_url = resp_json["info"]["next"].as_str().map(String::from);
    }
    let characters_json_str =
        serde_json::to_string(&all_chars).expect("Failed to serialize characters to jsonstr");
    let df = JsonReader::new(std::io::Cursor::new(characters_json_str))
        .finish()
        .expect("Failed to create DataFrame with characters jsonstr");
    return Ok(df);
}

async fn get_character_data_async(concurrency: usize) -> Result<DataFrame> {
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
        let mut handles: Vec<JoinHandle<Result<Vec<Value>>>> = vec![];

        for page in page_batch {
            let client = client.clone();
            handles.push(tokio::spawn(async move {
                // println!("Getting {page}...");
                let resp_json: Value = client.get(&page).send().await?.json().await?;
                let results = resp_json
                    .get("results")
                    .and_then(Value::as_array)
                    .ok_or_else(|| anyhow!("Error getting results from {}", page))?;
                Ok(results.to_vec())
            }));
        }

        for result in join_all(handles).await {
            match result {
                Ok(characters) => all_chars.extend(characters?),
                Err(e) => eprintln!("Error fetching page: {e}"),
            }
        }
    }

    let df = JsonReader::new(std::io::Cursor::new(serde_json::to_vec(&all_chars)?)).finish()?;
    Ok(df)
}

fn get_image(character_url: &str) -> Result<image::DynamicImage> {
    let resp_json: Value = reqwest::blocking::get(character_url)?.json()?;
    let image_url = resp_json
        .get("image")
        .and_then(Value::as_str)
        .ok_or_else(|| anyhow!("Missing image URL"))?;
    let image_bytes = reqwest::blocking::get(image_url)?.bytes()?;
    Ok(image::load_from_memory(&image_bytes)?)
}
