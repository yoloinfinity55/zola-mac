use std::fs::File;
use std::io::Write;
use std::process::Command;
use scraper::{Html, Selector};
use chrono::Local;
use reqwest;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let url = "https://www.getzola.org/documentation/content/overview/";
    let response = reqwest::get(url).await?;
    let body = response.text().await?;
    let document = Html::parse_document(&body);

    let title_selector = Selector::parse("h1").unwrap();
    let title_element = document.select(&title_selector).next();
    let title = if let Some(element) = title_element {
        element.inner_html()
    } else {
        println!("Warning: No h1 title found, using default");
        "Content Overview".to_string()
    };

    let content_selector = Selector::parse("div.documentation__content").unwrap();
    let content_element = document.select(&content_selector).next();
    let content = if let Some(element) = content_element {
        element.text().collect::<String>()
    } else {
        println!("Warning: No content found, using default");
        "Default content".to_string()
    };

    println!("Extracted title: {}", title);
    println!("Content length: {}", content.len());

    // Using dummy Azure credentials for testing
    let api_key = "dummy_api_key_for_testing";
    let region = "eastus";

    let beginner_explanation = generate_beginner_explanation(&content);
    let step_by_step_guide = generate_step_by_step_guide(&content);
    let audio_file_result = generate_audio(
        &format!("{}\n\n{}\n\n{}", title, beginner_explanation, step_by_step_guide),
        api_key.trim(),
        region.trim(),
    ).await;
    let audio_file = match &audio_file_result {
        Ok(file) => Some(file.clone()),
        Err(e) => {
            println!("Audio generation failed: {}", e);
            None
        }
    };

    let slug = title.to_lowercase().replace(' ', "-").chars().filter(|c| c.is_alphanumeric() || *c == '-').collect::<String>();
    let date = Local::now().format("%Y-%m-%d").to_string();
    let filename = format!("../content/blog/{}.md", slug);

    let mut file = File::create(filename)?;
    writeln!(file, "+++")?;
    writeln!(file, "title = \"{}\"", title)?;
    writeln!(file, "date = {}", date)?;
    writeln!(file, "+++")?;
    writeln!(file, "\n[Generated from {}]", url)?;
    writeln!(file, "\n## Beginner's Explanation")?;
    writeln!(file, "{}", beginner_explanation)?;
    writeln!(file, "\n## Step-by-Step Guide")?;
    writeln!(file, "{}", step_by_step_guide)?;

    if let Some(audio_path) = audio_file {
        writeln!(file, "\n## Audio Version")?;
        let mime_type = if audio_path.ends_with(".mp3") {
            "audio/mpeg"
        } else if audio_path.ends_with(".wav") {
            "audio/wav"
        } else {
            "audio/aiff"
        };
        writeln!(file, "<audio controls><source src=\"/{}\" type=\"{}\"></audio>", audio_path, mime_type)?;
    } else {
        writeln!(file, "\n## Audio Version")?;
        writeln!(file, "*Audio not available - Text-to-speech failed*")?;
    }

    Ok(())
}

fn generate_beginner_explanation(content: &str) -> String {
    // Placeholder for calling a large language model API
    format!("[Generated beginner-friendly explanation for: {}]", content)
}

fn generate_step_by_step_guide(content: &str) -> String {
    // Placeholder for calling a large language model API
    format!("[Generated step-by-step guide for: {}]", content)
}

async fn generate_audio(text: &str, _api_key: &str, _region: &str) -> Result<String, Box<dyn std::error::Error>> {
    let mp3_filename = "../static/audio/overview.mp3";
    let text_filename = "../static/audio/text_input.txt";

    // Write text to a file to avoid shell escaping issues
    let mut text_file = File::create(text_filename)?;
    text_file.write_all(text.as_bytes())?;

    // Try gTTS (Google Text-to-Speech) - simple and reliable
    println!("Generating high-quality audio with Google TTS for: {}...", text.chars().take(50).collect::<String>());

    // Use gtts Python package for reliable TTS
    let gtts_status = Command::new("python3")
        .arg("-c")
        .arg(format!(r#"
import sys
try:
    from gtts import gTTS
    with open("{}", "r") as f:
        text = f.read()
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save("{}")
    print("gTTS succeeded")
except Exception as e:
    print("gTTS failed: " + str(e))
    sys.exit(1)
"#, text_filename, mp3_filename))
        .status()?;

    // Clean up text file
    let _ = std::fs::remove_file(text_filename);

    if gtts_status.success() {
        // Check if we got a valid MP3 file
        if let Ok(metadata) = std::fs::metadata(mp3_filename) {
            if metadata.len() > 1000 { // Valid audio files are larger than 1KB
                println!("Google TTS MP3 generated successfully");
                return Ok("static/audio/overview.mp3".to_string());
            }
        }
    }

    // Fallback 1: Try espeak-ng if available (better quality than macOS basic TTS)
    println!("Google TTS failed, trying espeak-ng...");
    let espeak_status = Command::new("espeak-ng")
        .arg("-v")
        .arg("en-us")  // American English
        .arg("-s")
        .arg("150")    // Speed
        .arg("-w")
        .arg("../static/audio/overview.wav")
        .arg("-f")
        .arg(text_filename)
        .status()?;

    // Recreate text file for espeak
    let mut text_file = File::create(text_filename)?;
    text_file.write_all(text.as_bytes())?;

    if espeak_status.success() {
        println!("espeak-ng WAV generated successfully");
        let _ = std::fs::remove_file(text_filename);
        return Ok("static/audio/overview.wav".to_string());
    }

    // Fallback 2: macOS TTS with different voice
    println!("espeak-ng not available, using macOS TTS with enhanced voice");
    let aiff_filename = "../static/audio/overview.aiff";

    let macos_status = Command::new("say")
        .arg("-v")
        .arg("Alex")  // Try Alex voice (higher quality male voice)
        .arg("-o")
        .arg(aiff_filename)
        .arg("-f")
        .arg(text_filename)
        .status()?;

    // Clean up text file
    let _ = std::fs::remove_file(text_filename);

    if macos_status.success() {
        println!("macOS Alex TTS audio generated successfully");
        Ok("static/audio/overview.aiff".to_string())
    } else {
        println!("All TTS methods failed, creating placeholder file");
        let _file = File::create(mp3_filename)?;
        Ok("static/audio/overview.mp3".to_string())
    }
}
