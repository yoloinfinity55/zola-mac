#!/usr/bin/env python3
"""
generate_posts.py
-----------------------------------
Automated blog post generator for Zola.
- Fetches YouTube metadata and transcript
- Creates Markdown post with thumbnail, embed, keypoints, and AI-written narrative (via Groq)
- Enhanced error handling, logging, and retry logic
"""

import os
import sys
import argparse
import requests
from datetime import datetime
from pathlib import Path
from slugify import slugify
from yt_dlp import YoutubeDL
import textwrap
import time
from typing import Optional, Dict, Any
import logging
from dotenv import load_dotenv
import shutil
import base64
import subprocess # <-- ADDED for FFmpeg control
import math # <-- ADDED for ceiling function

# -----------------------------
# CONFIGURATION
# -----------------------------
# All files (index.md, asset.jpg, asset.mp3) will go into a subfolder under this base directory.
CONTENT_DIR = "content/blog" 

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_TRANSCRIPT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_TRANSCRIPT_MODEL = "whisper-large-v3"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Define file size limit for Groq (25MB is common, 20MB is a safe buffer)
GROQ_FILE_SIZE_LIMIT_MB = 20
GROQ_FILE_SIZE_LIMIT_BYTES = GROQ_FILE_SIZE_LIMIT_MB * 1024 * 1024

# Assume average MP3 bitrate of 192 kbps for chunking calculation
AVERAGE_MP3_BITRATE_KBPS = 192

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# -----------------------------
# UTILITY FUNCTIONS
# -----------------------------
def sanitize_text(text: str) -> str:
    """Sanitize text for markdown frontmatter."""
    return text.replace('"', '\\"').replace('\n', ' ').strip()


def format_duration(seconds: int) -> str:
    """Convert seconds to human-readable duration."""
    if not seconds:
        return "Unknown"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def parse_upload_date(upload_date: str) -> str:
    """Convert YYYYMMDD to YYYY-MM-DD."""
    if upload_date and len(upload_date) == 8:
        return f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
    return datetime.now().strftime("%Y-%m-%d")


# -----------------------------
# INITIAL CHECKS (Unchanged)
# -----------------------------
def initial_checks():
    """Performs pre-execution checks for dependencies and environment."""
    logger.info("🛠️ Running initial checks...")
    
    # 1. Check for FFmpeg dependency (required by yt-dlp and for manual splitting)
    if not shutil.which("ffmpeg"):
        logger.error("❌ FFmpeg not found in system PATH. Audio download and processing will fail.")
        logger.error("Please install FFmpeg and ensure it's accessible in your terminal.")
        sys.exit(1)
        
    # 2. Check and create content base directory
    content_base_path = Path(CONTENT_DIR)
    if not content_base_path.exists():
        logger.warning(f"Creating content directory: {CONTENT_DIR}")
        content_base_path.mkdir(parents=True, exist_ok=True)
        
    logger.info("✅ Initial checks passed.")


# -----------------------------
# FETCH YOUTUBE METADATA (Unchanged)
# -----------------------------
def fetch_youtube_info(url: str) -> Optional[Dict[str, Any]]:
    """Fetch YouTube video metadata with error handling."""
    logger.info(f"Fetching YouTube info for: {url}")
    
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "writesubtitles": False,
        "no_warnings": True,
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        return {
            "title": info.get("title", "Untitled Video"),
            "description": info.get("description", ""),
            "upload_date": info.get("upload_date"),
            "duration": info.get("duration", 0),
            "thumbnail": info.get("thumbnail"),
            "id": info.get("id"),
            "uploader": info.get("uploader", "Unknown"),
            "webpage_url": info.get("webpage_url"),
            "tags": info.get("tags", []),
            "view_count": info.get("view_count", 0),
        }
    except Exception as e:
        logger.error(f"Failed to fetch YouTube info: {e}")
        return None


# -----------------------------
# FFmpeg AUDIO SPLITTING LOGIC (NEW)
# -----------------------------
def split_audio_with_ffmpeg(audio_filepath: str, duration_sec: int, chunk_size_limit_bytes: int, target_dir: Path) -> Optional[list[Path]]:
    """
    Splits a large MP3 file into smaller chunks using FFmpeg based on file size limit.
    Returns a list of paths to the created chunks.
    """
    logger.info("Calculating optimal audio chunk size...")
    
    # Calculate target time duration in seconds for a single 20MB file
    # (File Size in bits) / (Bitrate in bits/sec) = Duration in seconds
    # (20 MB * 8 bits/byte) / (192 kbps * 1000 bits/kbit) = 833 seconds (approx 13.9 min)
    target_duration_sec = (chunk_size_limit_bytes * 8) / (AVERAGE_MP3_BITRATE_KBPS * 1000)
    
    num_chunks = math.ceil(duration_sec / target_duration_sec)
    chunk_duration_sec = math.ceil(duration_sec / num_chunks)
    
    logger.info(f"Video duration: {duration_sec}s. Splitting into {num_chunks} chunks of ~{chunk_duration_sec}s.")
    
    chunk_files = []
    
    for i in range(num_chunks):
        start_time = i * chunk_duration_sec
        chunk_path = target_dir / f"chunk_{i:03d}.mp3"
        
        # FFmpeg command: 
        # -i <input> -ss <start time> -t <duration> -c copy <output>
        command = [
            'ffmpeg',
            '-i', audio_filepath,
            '-ss', str(start_time),
            '-t', str(chunk_duration_sec),
            '-c', 'copy', # Copy stream without re-encoding for speed
            '-y', # Overwrite output files without asking
            str(chunk_path)
        ]

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            chunk_files.append(chunk_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ FFmpeg chunking failed for chunk {i}: {e.stderr}")
            return None
    
    return chunk_files

# -----------------------------
# CORE GROQ TRANSCRIPTION LOGIC (SLIGHTLY MODIFIED)
# -----------------------------
def transcribe_chunk_with_groq(audio_filepath: Path) -> str:
    """
    Transcribes a single audio chunk (file) using Groq API.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("API key is missing during transcription attempt.")
        return "ERROR: Missing API Key"

    headers = {"Authorization": f"Bearer {api_key}"}
    data = {'model': GROQ_TRANSCRIPT_MODEL}
    
    for attempt in range(MAX_RETRIES):
        try:
            # Open file within the loop to ensure the file handle is reset for retries
            with open(audio_filepath, 'rb') as audio_file:
                files = {
                    'file': (audio_filepath.name, audio_file, 'audio/mp3')
                }
                
                resp = requests.post(
                    GROQ_TRANSCRIPT_URL, 
                    headers=headers, 
                    data=data, 
                    files=files, 
                    timeout=120
                )
            
            resp.raise_for_status() # Raises exception for 4xx or 5xx status codes
            data = resp.json()
            return data.get("text", "")
            
        except requests.RequestException as e:
            logger.warning(f"Groq Chunk API attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    
    return "ERROR: Chunk transcription failed after all retries."


# -----------------------------
# GENERATE TRANSCRIPT FROM AUDIO (UPDATED TO USE FFmpeg SPLIT)
# -----------------------------
def generate_transcript_from_audio(metadata: Dict[str, Any], audio_filepath: str) -> str:
    """Generate transcript using Groq API, with FFmpeg chunking for large files."""
    audio_file_path = Path(audio_filepath)
    audio_file_size = os.path.getsize(audio_file_path)
    
    if audio_file_size <= GROQ_FILE_SIZE_LIMIT_BYTES:
        logger.info(f"🎤 Transcribing single file ({audio_file_size // 1024**2} MB) via Groq...")
        
        transcript = transcribe_chunk_with_groq(audio_file_path)
        
        if transcript.startswith("ERROR:"):
            logger.error(f"❌ Transcription failed for single file: {transcript}")
            return "Automatic transcription failed."
            
        logger.info("✅ Transcript generated successfully.")
        return transcript.strip()
    
    # --- CHUNKING LOGIC FOR LARGE FILES ---
    
    logger.info(f"🎤 File size ({audio_file_size // 1024**2} MB) exceeds limit. Starting FFmpeg audio chunking...")

    # The directory where the audio is stored is the target for chunks
    target_dir = audio_file_path.parent
    duration_sec = metadata.get("duration")

    if not duration_sec:
        logger.error("❌ Cannot chunk audio: Video duration metadata is missing.")
        return "Automatic transcription failed (missing video duration)."

    chunk_paths = split_audio_with_ffmpeg(
        str(audio_file_path), 
        duration_sec, 
        GROQ_FILE_SIZE_LIMIT_BYTES, 
        target_dir
    )
    
    if not chunk_paths:
        return "Automatic transcription failed during audio splitting."

    full_transcript = []
    
    for i, chunk_path in enumerate(chunk_paths):
        logger.info(f"   -> Transcribing chunk {i+1}/{len(chunk_paths)}...")
        chunk_transcript = transcribe_chunk_with_groq(chunk_path)
        
        if chunk_transcript.startswith("ERROR:"):
            logger.error(f"❌ Chunk {i+1} failed: {chunk_transcript}")
            return "Automatic transcription failed during chunk processing."
        
        full_transcript.append(chunk_transcript)
        
    # --- Cleanup ---
    for chunk_path in chunk_paths:
        os.remove(chunk_path)
    logger.info(f"✅ All {len(chunk_paths)} chunks transcribed and cleaned up successfully.")
    
    return " ".join(full_transcript).strip()


# -----------------------------
# AI NARRATIVE (GROQ) (Unchanged)
# -----------------------------
def generate_ai_narrative(title: str, summary: str, transcript_text: str) -> Optional[str]:
    """Generate AI narrative using Groq API with structured blog format."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.warning("⚠️ Missing GROQ_API_KEY environment variable. Skipping AI narrative.")
        return None

    logger.info("🧠 Generating AI narrative via Groq...")

    prompt = textwrap.dedent(f"""
    You are an experienced technical content writer. Write a comprehensive, engaging blog article 
    based on this video content. Structure your article with these sections:
    
    ## 🧭 Introduction
    Write a compelling 2-3 paragraph introduction that hooks the reader and explains what they'll learn.
    
    ## 🔍 Step-by-Step Summary
    Provide a numbered list (4-6 items) breaking down the main steps or concepts covered in the video.
    
    ## 💡 Key Insights
    Provide 4-6 bullet points highlighting the most important takeaways, best practices, or insights.
    
    Requirements:
    - Use emojis as shown in section headers
    - Write in a conversational yet professional tone
    - Be concise but informative
    - Focus on practical value
    - Total length: 400-600 words
    
    Video Title: {title}
    Video Description: {summary[:500]}
    
    Transcript (use as reference):
    {transcript_text[:10000]}
    
    Write the article now:
    """)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a professional technical writer who creates engaging, well-structured blog posts with clear sections and practical insights."
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 2500,
        "top_p": 0.9,
    }

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=90)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            logger.info("✅ AI narrative generated successfully")
            return content
        except requests.RequestException as e:
            logger.warning(f"Groq API attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    
    logger.error("❌ Groq API failed after all retries")
    return None


# -----------------------------
# DOWNLOAD THUMBNAIL (Unchanged)
# -----------------------------
def download_thumbnail(url: str, filepath: str) -> bool:
    """Download thumbnail with retry logic."""
    logger.info(f"Downloading thumbnail to {filepath}")
    
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(resp.content)
            logger.info("✅ Thumbnail downloaded successfully")
            return True
        except requests.RequestException as e:
            logger.warning(f"Thumbnail download attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    
    logger.error("❌ Failed to download thumbnail after all retries")
    return False


# -----------------------------
# DOWNLOAD AUDIO (Unchanged)
# -----------------------------
def download_audio(video_id: str, filepath: str) -> bool:
    """Download audio from YouTube video."""
    logger.info(f"Downloading audio to {filepath}")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': str(Path(filepath).with_suffix('')),
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
        logger.info("✅ Audio downloaded successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to download audio: {e}")
        return False


# -----------------------------
# SAVE MARKDOWN POST (Unchanged)
# -----------------------------
def save_markdown(metadata: Dict[str, Any], transcript_text: str, audio_filepath: str, ai_article: Optional[str] = None) -> str:
    """Save markdown post and assets into a Zola Page Bundle subfolder."""
    slug = slugify(metadata["title"])
    date_str = parse_upload_date(metadata.get("upload_date"))
    
    # 1. Define the post's subfolder path (Page Bundle)
    post_bundle_dir = Path(CONTENT_DIR) / slug
    filename = post_bundle_dir / "index.md" 
    
    # 2. Create the new Page Bundle directory
    post_bundle_dir.mkdir(parents=True, exist_ok=True)
    
    # Define asset filenames for Zola Page Bundle
    thumb_filename = "asset.jpg"
    thumb_filepath = post_bundle_dir / thumb_filename
    
    # 3. Download thumbnail
    if metadata.get("thumbnail"):
        download_thumbnail(metadata["thumbnail"], str(thumb_filepath))
    
    if not Path(audio_filepath).exists():
        logger.warning(f"Audio file not found at {audio_filepath}. Audio link in markdown may be broken.")

    # 4. Prepare Zola Paths and Metadata
    zola_asset_url_base = "./asset" 
    tags = metadata.get("tags", [])[:5]
    if not tags:
        tags = ["zola", "youtube", "tutorial", "jamstack"]
    tags_str = ", ".join([f'"{tag}"' for tag in tags])
    summary_text = sanitize_text(metadata["description"].split('\n')[0][:160] if metadata["description"] else metadata["title"])
    
    # 5. Build Markdown Content
    frontmatter = textwrap.dedent(f"""\
+++
title = "{sanitize_text(metadata['title'])}"
date = "{date_str}"
tags = [{tags_str}]
+++
""")
    
    body = textwrap.dedent(f"""
![{sanitize_text(metadata['title'])}]({zola_asset_url_base}.jpg)

## TL;DR (Summary)

> {summary_text}

## 🎧 Listen to the Episode

<audio controls style="width: 100%;">
  <source src="{zola_asset_url_base}.mp3" type="audio/mpeg">
  Your browser does not support the audio element.
</audio>

{ai_article or '## 🧭 Introduction\\n\\n_AI-generated narrative unavailable. Please set GROQ_API_KEY environment variable._\\n\\n## 🔍 Key Points\\n\\n- Video covers important concepts\\n- Detailed tutorial content\\n- Practical examples included'}

## 🗒️ Transcript (Auto-Generated)

> {transcript_text}

## ▶️ Watch the Video

* **Author:** {sanitize_text(metadata.get('uploader', 'Unknown'))}
* **Duration:** {format_duration(metadata.get('duration', 0))}

<div class="youtube-embed">
<iframe width="560" height="315" src="https://www.youtube.com/embed/{metadata['id']}" frameborder="0" allowfullscreen></iframe>
</div>

[Watch on YouTube]({metadata['webpage_url']})
""")
    
    # Concatenate the frontmatter and body, removing the leading newline.
    md = frontmatter + body.lstrip('\n') 
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md)
    
    logger.info(f"✅ Markdown post saved: {filename}")
    return str(filename)


# -----------------------------
# MAIN EXECUTION
# -----------------------------
def main():
    # Load environment variables from .env file
    load_dotenv() 

    parser = argparse.ArgumentParser(
        description="Generate Markdown blog post from YouTube video.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          %(prog)s --youtube https://www.youtube.com/watch?v=VIDEO_ID
          %(prog)s --youtube https://youtu.be/VIDEO_ID --verbose
        
        Environment Variables:
          GROQ_API_KEY     API key for Groq AI narrative generation
        """)
    )
    parser.add_argument("--youtube", required=True, help="YouTube video URL")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Run checks before proceeding
    initial_checks()
    
    logger.info("=" * 60)
    logger.info("Starting blog post generation...")
    logger.info("=" * 60)
    
    # Fetch metadata
    meta = fetch_youtube_info(args.youtube)
    if not meta:
        logger.error("❌ Failed to fetch video metadata. Exiting.")
        sys.exit(1)

    slug = slugify(meta["title"])
    post_bundle_dir = Path(CONTENT_DIR) / slug
    audio_filepath = post_bundle_dir / "asset.mp3"

    # 1. Download audio first
    post_bundle_dir.mkdir(parents=True, exist_ok=True)
    audio_downloaded = download_audio(meta["id"], str(audio_filepath))
    
    transcript_text = ""
    if audio_downloaded:
        # 2. Generate transcript from the downloaded audio (now uses FFmpeg for splitting)
        # Pass the full metadata which includes the video duration
        transcript_text = generate_transcript_from_audio(meta, str(audio_filepath))
    else:
        transcript_text = "Automatic transcription failed because the audio file could not be downloaded."
    
    # 3. Generate AI narrative (uses the new transcript)
    ai_article = generate_ai_narrative(meta["title"], meta["description"], transcript_text)
    
    # 4. Save markdown (which also downloads thumbnail)
    filename = save_markdown(meta, transcript_text, str(audio_filepath), ai_article)
    
    logger.info("=" * 60)
    logger.info(f"✅ Blog post generation complete!")
    logger.info(f"📄 File saved: {filename}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()