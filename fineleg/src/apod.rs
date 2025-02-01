use anyhow::{anyhow, Result};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::env;

const APOD_BASE_URL: &str = "https://api.nasa.gov/planetary/apod";

#[derive(Serialize)]
struct ApodQueryParams {
    api_key: String,
    date: String,
    // count: usize,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ApodResponse {
    pub date: String,
    pub explanation: String,
    pub title: String,
    pub url: String,
    #[serde(rename = "hdurl")]
    pub hd_url: Option<String>,
    pub media_type: String,
    pub service_version: String,
}

async fn get_image_from_api() -> Result<()> {
    let client = Client::new();
    // let today = Local::now().format("%Y-%m-%d").to_string();
    let params = ApodQueryParams {
        date: "1998-05-10".to_string(),
        // count: 3,
        api_key: env::var("NASA_API_KEY")?,
    };
    let request = client.get(APOD_BASE_URL).query(&params).build()?;
    println!("Making request to {}...", request.url());
    let resp: ApodResponse = client.execute(request).await?.json().await?;

    // println!("{:?}", resp);
    match resp.media_type.as_str() {
        "image" => get_and_save_image(&resp.hd_url.unwrap(), client).await?,
        _ => println!("Media type not supported"),
    }

    Ok(())
}

async fn get_and_save_image(image_url: &str, client: Client) -> Result<()> {
    println!("Getting image from {}", image_url);
    let image_raw = client.get(image_url).send().await?.bytes().await?;
    let image = image::load_from_memory(&image_raw)?;
    let output_path = format!(
        "{}/common/data/images/{}",
        env::var("REPO_ROOT")?,
        image_url
            .split("/")
            .last()
            .ok_or_else(|| anyhow!("Failed to get image name"))?
    );
    image.save(output_path)?;

    Ok(())
}
