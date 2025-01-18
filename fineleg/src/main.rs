use polars::prelude::*;
use reqwest::get;
use serde_json::Value;

const DATA_URL_BASE: &str = "https://rickandmortyapi.com/api/character/";

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut characters = Vec::new();
    let mut next_url = Some(String::from(DATA_URL_BASE));
    while let Some(url) = next_url {
        println!("Getting {url}...");
        let resp_json: Value = get(&url).await?.json().await?;
        if let Some(results) = resp_json["results"].as_array() {
            characters.extend(results.clone());
        }
        println!("{}", resp_json["info"]);
        println!("Fetched {} characters so far...", characters.len());
        if characters.len() >= 100 {
            break;
        }
        next_url = resp_json["info"]["next"].as_str().map(String::from);
    }
    let characters_json_str = serde_json::to_string(&characters)?;
    let df = JsonReader::new(std::io::Cursor::new(characters_json_str)).finish()?;
    // let resp_json: Value = get(DATA_URL)?.json()?;
    // for (i, character) in resp_json["results"].as_array().unwrap().iter().enumerate() {
    //     println!("Character {}: {}", i+1, character["name"]);
    // }
    for character_url in df.column("url").unwrap().str().unwrap().into_iter() {
        if let Some(url) = character_url {
            println!("{}", url);
        }
    }

    println!("{}", df);
    Ok(())
}

// fn process_data(df: DataFrame) -> String {
//     println!("{df}");
//     String::from("lmao")
// }
