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
import subprocess
import math
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
from PIL import Image
import io
import toml

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
    """Convert YYYYMMDD to YYYY-MM-DD (Used only for YouTube metadata, not frontmatter)."""
    if upload_date and len(upload_date) == 8:
        return f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
    return datetime.now().strftime("%Y-%m-%d")


def clean_youtube_url(url: str) -> str:
    """Strips playlist parameters (list, index) from a YouTube URL."""
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # Keep only the 'v' parameter (video ID) and rebuild the query string
    new_query = {}
    if 'v' in query_params:
        new_query['v'] = query_params['v']
    
    cleaned_url = urlunparse(
        parsed_url._replace(query=urlencode(new_query, doseq=True))
    )
    
    if not new_query and 'youtu.be' not in parsed_url.netloc:
        return url
        
    logger.info(f"Cleaned URL: {cleaned_url}")
    return cleaned_url


# -----------------------------
# INITIAL CHECKS (Unchanged)
# -----------------------------
def initial_checks():
    """Performs pre-execution checks for dependencies and environment."""
    logger.info("🛠️ Running initial checks...")
    
    # 1. Check for FFmpeg dependency
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
# FETCH YOUTUBE METADATA (Unchanged, uses clean URL)
# -----------------------------
def fetch_youtube_info(url: str) -> Optional[Dict[str, Any]]:
    """Fetch YouTube video metadata with error handling."""
    
    clean_url = clean_youtube_url(url)
    logger.info(f"Fetching YouTube info for: {clean_url}")
    
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "writesubtitles": False,
        "no_warnings": True,
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)
        
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
# FFmpeg AUDIO SPLITTING LOGIC (Unchanged)
# -----------------------------
def split_audio_with_ffmpeg(audio_filepath: str, duration_sec: int, chunk_size_limit_bytes: int, target_dir: Path) -> Optional[list[Path]]:
    """
    Splits a large MP3 file into smaller chunks using FFmpeg based on file size limit.
    Returns a list of paths to the created chunks.
    """
    logger.info("Calculating optimal audio chunk size...")
    
    target_duration_sec = (chunk_size_limit_bytes * 8) / (AVERAGE_MP3_BITRATE_KBPS * 1000)
    
    num_chunks = math.ceil(duration_sec / target_duration_sec)
    chunk_duration_sec = math.ceil(duration_sec / num_chunks)
    
    logger.info(f"Video duration: {duration_sec}s. Splitting into {num_chunks} chunks of ~{chunk_duration_sec}s.")
    
    chunk_files = []
    
    for i in range(num_chunks):
        start_time = i * chunk_duration_sec
        chunk_path = target_dir / f"chunk_{i:03d}.mp3"
        
        command = [
            'ffmpeg',
            '-i', audio_filepath,
            '-ss', str(start_time),
            '-t', str(chunk_duration_sec),
            '-c', 'copy', 
            '-y', 
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
# CORE GROQ TRANSCRIPTION LOGIC (Unchanged)
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
            
            resp.raise_for_status()
            data = resp.json()
            return data.get("text", "")
            
        except requests.RequestException as e:
            logger.warning(f"Groq Chunk API attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    
    return "ERROR: Chunk transcription failed after all retries."


# -----------------------------
# GENERATE TRANSCRIPT FROM AUDIO (Unchanged)
# -----------------------------
def generate_transcript_from_audio(metadata: Dict[str, Any], audio_filepath: str) -> str:
    """Generate transcript using Groq API, with FFmpeg chunking for large files."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.warning("⚠️ Missing GROQ_API_KEY. Cannot use API for transcription.")
        return "Automatic transcription unavailable due to missing API key."
        
    audio_file_path = Path(audio_filepath)
    if not audio_file_path.exists():
        logger.error(f"❌ Audio file not found at {audio_filepath}. Cannot transcribe.")
        return "Automatic transcription failed (audio file missing)."
        
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
            for p in chunk_paths:
                if p.exists(): os.remove(p)
            return "Automatic transcription failed during chunk processing."
        
        full_transcript.append(chunk_transcript)
        
    # --- Cleanup ---
    for chunk_path in chunk_paths:
        os.remove(chunk_path)
    logger.info(f"✅ All {len(chunk_paths)} chunks transcribed and cleaned up successfully.")
    
    return " ".join(full_transcript).strip()


# -----------------------------
# AI NARRATIVE STEP 1: SUMMARY AND STRUCTURE (Unchanged)
# -----------------------------
def generate_ai_summary_and_structure(title: str, summary: str, transcript_text: str) -> Optional[str]:
    """Generate structured key points and summary using Groq API."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.warning("⚠️ Missing GROQ_API_KEY environment variable. Skipping AI structure generation.")
        return None

    logger.info("🧠 Generating structured AI summary via Groq...")

    prompt = textwrap.dedent(f"""
    You are an expert content analyzer. Your task is to extract the core value and structure of the following video content. Format your output strictly using the following markdown sections:
    
    ## 🔍 Step-by-Step Summary
    Provide a numbered list (4-6 items) breaking down the main steps or concepts covered in the video.
    
    ## 💡 Key Insights
    Provide 4-6 bullet points highlighting the most important takeaways, best practices, or insights.
    
    Requirements:
    - Use emojis as shown in section headers
    - Be extremely concise and focused on actionable points.
    
    Video Title: {title}
    Video Description: {summary[:500]}
    
    Transcript (use as reference):
    {transcript_text[:10000]}
    
    Generate the structured content now:
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
                "content": "You are a professional content analyst who extracts concise, structured summaries and key takeaways from technical transcripts."
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.5,
        "max_tokens": 1500,
        "top_p": 0.9,
    }

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=90)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            logger.info("✅ AI structure generated successfully")
            return content
        except requests.RequestException as e:
            logger.warning(f"Groq API (Structure) attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    
    logger.error("❌ Groq API (Structure) failed after all retries")
    return None

# -----------------------------
# AI NARRATIVE STEP 2: HUMAN-LIKE ARTICLE (Unchanged)
# -----------------------------
def generate_final_article(title: str, summary: str, transcript_text: str, ai_structure: str) -> Optional[str]:
    """Generate a flowing, human-readable article based on the summary and transcript."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.warning("⚠️ Missing GROQ_API_KEY environment variable. Skipping final article generation.")
        return None

    logger.info("✍️ Generating final human-like article via Groq...")

    prompt = textwrap.dedent(f"""
    You are an experienced, engaging technical blog writer. Write a comprehensive, human-like article based on the provided video content and structured summary.
    
    ## 🚀 Introduction
    Write a compelling 2-3 paragraph introduction that hooks the reader, sets the context, and explains what they'll learn from the video/article.
    
    ## ✍️ Full Article Narrative
    Using the steps and insights provided in the AI Structure, write a flowing, detailed narrative. Use multiple paragraphs, subheadings (H3 or H4), and strong transitions. Do NOT include the original structured lists (Step-by-Step Summary, Key Insights) in this section. Instead, weave them naturally into the narrative flow.
    
    Requirements:
    - Write in an active, conversational, yet professional tone.
    - Total length for the combined sections: 400-600 words.
    - Do NOT use emojis in this final article text.
    
    Video Title: {title}
    Video Description: {summary[:500]}
    
    AI Structure (Source Material for Content):
    {ai_structure}
    
    Transcript (Reference for detail/context):
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
                "content": "You are a professional technical blog writer focused on creating clear, engaging, human-readable narratives."
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
            logger.info("✅ Final article generated successfully")
            return content
        except requests.RequestException as e:
            logger.warning(f"Groq API (Article) attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    
    logger.error("❌ Groq API (Article) failed after all retries")
    return None

# -----------------------------
# AI NARRATIVE STEP 3: SOCIAL MEDIA POST (Unchanged)
# -----------------------------
def generate_social_media_post(title: str, summary: str, tags: list[str]) -> Optional[str]:
    """Generate a concise, promotional post for X.com (Twitter) with a 280-character limit."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.warning("⚠️ Missing GROQ_API_KEY environment variable. Skipping social media post generation.")
        return None

    logger.info("🐦 Generating social media post (X/Twitter) via Groq...")
    
    # Create hashtags from tags
    hashtags = " ".join([f"#{tag.replace(' ', '').lower()}" for tag in tags[:4]])
    
    prompt = textwrap.dedent(f"""
    You are a social media marketing expert. Write a single promotional post (tweet) for X.com for a new blog article.
    
    Requirements:
    - Be catchy and engaging.
    - Maximize character count to use the full space, but **DO NOT exceed 280 characters.**
    - Use relevant emojis.
    - Include a clear call-to-action to read the full article.
    - You must include the following auto-generated hashtags at the end: {hashtags}
    
    Blog Title: {title}
    Blog Summary: {summary[:200]}
    
    Write ONLY the tweet content (no markdown or introductory text):
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
                "content": "You are a social media copywriter who crafts engaging, concise tweets under the 280-character limit."
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.8, 
        "max_tokens": 150, # Set a low max token count to encourage brevity
        "top_p": 0.9,
    }

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=45)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            
            # Simple check to enforce the limit if the model went slightly over
            if len(content) > 280:
                 content = content[:277] + "..." # Truncate and add ellipsis
                 logger.warning("⚠️ Social media post truncated to fit 280-character limit.")
            
            logger.info("✅ Social media post generated successfully")
            return content
        except requests.RequestException as e:
            logger.warning(f"Groq API (Social) attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    
    logger.error("❌ Groq API (Social) failed after all retries")
    return None


# -----------------------------
# DOWNLOAD THUMBNAIL (Updated for 16:9 cropping)
# -----------------------------
def download_thumbnail(url: str, filepath: str) -> bool:
    """Download thumbnail with retry logic and crop to 16:9 aspect ratio."""
    logger.info(f"Downloading and cropping thumbnail to {filepath}")

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()

            # Open image with PIL
            image = Image.open(io.BytesIO(resp.content))

            # Calculate 16:9 crop dimensions
            width, height = image.size
            target_ratio = 16 / 9
            current_ratio = width / height

            if current_ratio > target_ratio:
                # Too wide, crop width
                new_width = int(height * target_ratio)
                left = (width - new_width) // 2
                right = left + new_width
                top, bottom = 0, height
            else:
                # Too tall, crop height
                new_height = int(width / target_ratio)
                top = (height - new_height) // 2
                bottom = top + new_height
                left, right = 0, width

            # Crop and save
            cropped_image = image.crop((left, top, right, bottom))
            cropped_image.save(filepath, "JPEG")

            logger.info("✅ Thumbnail downloaded and cropped successfully")
            return True
        except requests.RequestException as e:
            logger.warning(f"Thumbnail download attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
        except Exception as e:
            logger.warning(f"Thumbnail processing attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

    logger.error("❌ Failed to download and crop thumbnail after all retries")
    return False


# -----------------------------
# DOWNLOAD AUDIO (Unchanged, uses minimal URL)
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
        minimal_url = f"https://www.youtube.com/watch?v={video_id}"
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([minimal_url])
        logger.info("✅ Audio downloaded successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to download audio: {e}")
        return False


# -----------------------------
# SAVE MARKDOWN POST (FIXED SYNTAX ERROR)
# -----------------------------
def save_markdown(metadata: Dict[str, Any], transcript_text: str, audio_filepath: str, ai_structure: Optional[str] = None, final_article: Optional[str] = None, social_post: Optional[str] = None) -> str:
    """Save markdown post and assets into a Zola Page Bundle subfolder."""
    slug = slugify(metadata["title"])
    
    # Use current generation time for the date field
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    
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
    
    # FRONT MATTER (Using current generation time)
    frontmatter = textwrap.dedent(f"""\
    +++
    title = "{sanitize_text(metadata['title'])}"
    date = "{current_date_str}"
    tags = [{tags_str}]
    +++
    """)
    
    # BODY CONTENT 
    
    # FIX: Sanitize dynamic content against accidental triple quotes which cause the SyntaxError
    safe_ai_structure = (ai_structure or '## 🔍 Key Points\\n\\n- Structured summary unavailable.\\n')
    safe_ai_structure = safe_ai_structure.replace('"""', '\"\"\"')
    
    safe_final_article = (final_article or '## 📝 Full Article Narrative\\n\\n_AI-generated narrative unavailable. Please ensure GROQ_API_KEY is set and the API calls succeed._\\n')
    safe_final_article = safe_final_article.replace('"""', '\"\"\"')
    
    safe_social_post = (social_post if social_post else "_Social media post generation failed or API key missing._")
    safe_social_post = safe_social_post.replace('"""', '\"\"\"')


    body = textwrap.dedent(f"""
![{sanitize_text(metadata['title'])}]({zola_asset_url_base}.jpg)

## TL;DR (Quick Summary)

> {summary_text}

## 🎧 Listen to the Episode

<audio controls style="width: 100%;">
  <source src="{zola_asset_url_base}.mp3" type="audio/mpeg">
  Your browser does not support the audio element.
</audio>

## 📋 Structured Key Takeaways

{safe_ai_structure}

---

## 🗒️ Transcript (Auto-Generated)

> {transcript_text}

---

## 📝 Full Article Narrative

{safe_final_article}

---

## ▶️ Watch the Video

* **Author:** {sanitize_text(metadata.get('uploader', 'Unknown'))}
* **Duration:** {format_duration(metadata.get('duration', 0))}

<div class="youtube-embed">
<iframe width="560" height="315" src="https://www.youtube.com/embed/{metadata['id']}" frameborder="0" allowfullscreen></iframe>
</div>

[Watch on YouTube]({metadata['webpage_url']})

---

## 🐦 Social Media Post (X/Twitter)

**Copy and Paste for Promotion (280 Character Limit):**

{safe_social_post}

""")
    
    md = frontmatter + body.lstrip('\n') 
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md)
    
    logger.info(f"✅ Markdown post saved: {filename}")
    return str(filename)


# -----------------------------
# FIX EXISTING THUMBNAILS
# -----------------------------
def fix_existing_thumbnails():
    """
    Iterates through all post directories, finds the index.md,
    extracts the youtube_id, and re-downloads the thumbnail as asset.jpg.
    """
    logger.info("Starting to fix existing thumbnails with the new directory structure...")

    content_path = Path(CONTENT_DIR)
    # Look for index.md files in subdirectories
    for md_file in content_path.glob("**/index.md"):
        if md_file.is_file():
            post_dir = md_file.parent
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Find the end of the frontmatter
                frontmatter_end = content.find("+++", 3)
                if frontmatter_end != -1:
                    frontmatter_str = content[3:frontmatter_end].strip()
                    frontmatter = toml.loads(frontmatter_str)

                    if "extra" in frontmatter and "youtube_id" in frontmatter["extra"]:
                        youtube_id = frontmatter["extra"]["youtube_id"]
                        thumb_filename = post_dir / "asset.jpg"

                        logger.info(f"Processing {post_dir.name}...")
                        logger.info(f"  - YouTube ID: {youtube_id}")
                        logger.info(f"  - Thumbnail Path: {thumb_filename}")

                        # Re-download and crop the thumbnail
                        download_thumbnail(youtube_id, str(thumb_filename))
                    else:
                        logger.warning(f"Skipping {md_file.name}: youtube_id not found in frontmatter.")
                else:
                    logger.warning(f"Skipping {md_file.name}: frontmatter not found.")
            except Exception as e:
                logger.error(f"Error processing {md_file.name}: {e}")

    logger.info("Finished fixing thumbnails.")


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
    
    try:
        initial_checks()
        
        logger.info("=" * 60)
        logger.info("Starting blog post generation...")
        logger.info("=" * 60)
        
        meta = fetch_youtube_info(args.youtube)
        if not meta:
            logger.error("❌ Failed to fetch video metadata. Exiting.")
            sys.exit(1)

        slug = slugify(meta["title"])
        post_bundle_dir = Path(CONTENT_DIR) / slug
        audio_filepath = post_bundle_dir / "asset.mp3"

        # 1. Download audio
        post_bundle_dir.mkdir(parents=True, exist_ok=True)
        audio_downloaded = download_audio(meta["id"], str(audio_filepath))
        
        transcript_text = ""
        if audio_downloaded:
            # 2. Generate transcript (handles chunking)
            transcript_text = generate_transcript_from_audio(meta, str(audio_filepath))
        else:
            transcript_text = "Automatic transcription failed because the audio file could not be downloaded."
        
        # 3. Generate AI structured summary
        ai_structure = generate_ai_summary_and_structure(meta["title"], meta["description"], transcript_text)
        
        # 4. Generate the final human-like article
        final_article = generate_final_article(meta["title"], meta["description"], transcript_text, ai_structure or "")
        
        # 5. Generate the social media post
        social_post = generate_social_media_post(meta["title"], meta["description"], meta.get("tags", []))
        
        # 6. Save markdown (which also downloads thumbnail)
        filename = save_markdown(meta, transcript_text, str(audio_filepath), ai_structure, final_article, social_post)
        
        logger.info("=" * 60)
        logger.info(f"✅ Blog post generation complete!")
        logger.info(f"📄 File saved: {filename}")
        logger.info("=" * 60)
    except Exception as e:
        logger.exception(f"An unexpected error occurred during post generation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
