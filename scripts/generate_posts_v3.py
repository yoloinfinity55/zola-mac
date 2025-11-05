#!/usr/bin/env python3
"""
generate_posts_v3.py
-----------------------------------
Enhanced blog post generator for Zola (based on v1 with v2 improvements).
- Fetches YouTube metadata and transcript (working embed)
- Creates Markdown post with thumbnail, embed, keypoints, and AI-written narrative (via Groq)
- Enhanced error handling, logging, and retry logic
- Added rich metadata, intelligent tagging, and enhanced AI narrative
"""

import os
import sys
import argparse
import requests
from datetime import datetime, timedelta
from pathlib import Path
from slugify import slugify
from yt_dlp import YoutubeDL
import textwrap
import time
from typing import Optional, Dict, Any, List
import logging
import json
from dotenv import load_dotenv
import shutil
import base64
import subprocess
import math
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode

# -----------------------------
# CONFIGURATION
# -----------------------------
CONTENT_DIR = "content/blog"

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_TRANSCRIPT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_TRANSCRIPT_MODEL = "whisper-large-v3"
MAX_RETRIES = 3
RETRY_DELAY = 2

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


def categorize_video(categories: List[str], tags: List[str], title: str, description: str) -> List[str]:
    """Intelligently categorize video based on metadata."""
    blog_tags = set()

    # Category mapping
    category_map = {
        'Education': ['tutorial', 'learning', 'education'],
        'Science & Technology': ['tech', 'programming', 'development'],
        'Howto & Style': ['howto', 'guide', 'tutorial'],
        'Music': ['music', 'audio'],
        'Gaming': ['gaming', 'game'],
    }

    for cat in categories:
        if cat in category_map:
            blog_tags.update(category_map[cat])

    # Keyword extraction from title and tags
    keywords = {
        'zola': ['zola'],
        'rust': ['rust', 'programming'],
        'jamstack': ['jamstack', 'static-site'],
        'web': ['web', 'frontend', 'html', 'css'],
        'backend': ['backend', 'api', 'server'],
        'database': ['database', 'sql', 'nosql'],
        'docker': ['docker', 'container', 'devops'],
        'ai': ['ai', 'machine-learning', 'ml'],
    }

    text_lower = f"{title} {description}".lower()
    for keyword, related_tags in keywords.items():
        if keyword in text_lower:
            blog_tags.update(related_tags)

    # Add original tags (cleaned)
    if tags:
        blog_tags.update([t.lower().replace(' ', '-') for t in tags[:3]])

    return list(blog_tags)[:8]  # Limit to 8 tags


# -----------------------------
# INITIAL CHECKS
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
# ENHANCED YOUTUBE METADATA EXTRACTION
# -----------------------------
def fetch_youtube_info(url: str) -> Optional[Dict[str, Any]]:
    """Fetch comprehensive YouTube video metadata with working embed support."""
    clean_url = clean_youtube_url(url)
    logger.info(f"Fetching YouTube info for: {clean_url}")

    # Use basic options to get embeddability info
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)

        # Extract chapters if available (v2 enhancement)
        chapters = []
        if info.get('chapters'):
            chapters = [
                {
                    'title': ch.get('title', 'Untitled'),
                    'start_time': ch.get('start_time', 0),
                    'end_time': ch.get('end_time', 0),
                }
                for ch in info['chapters']
            ]

        return {
            "title": info.get("title", "Untitled Video"),
            "description": info.get("description", ""),
            "upload_date": info.get("upload_date"),
            "duration": info.get("duration", 0),
            "thumbnail": info.get("thumbnail"),
            "id": info.get("id"),
            "uploader": info.get("uploader", "Unknown"),
            "uploader_id": info.get("uploader_id", ""),
            "channel_url": info.get("channel_url", ""),
            "webpage_url": info.get("webpage_url"),
            "tags": info.get("tags", []),
            "categories": info.get("categories", []),
            "view_count": info.get("view_count", 0),
            "like_count": info.get("like_count", 0),
            "comment_count": info.get("comment_count", 0),
            "embeddable": info.get("embeddable", True),
            "chapters": chapters,
            "subtitles_available": bool(info.get('subtitles') or info.get('automatic_captions')),
        }
    except Exception as e:
        logger.error(f"Failed to fetch YouTube info: {e}")
        return None


# -----------------------------
# FETCH TRANSCRIPT
# -----------------------------
def fetch_transcript(video_id: str) -> str:
    """Fetch video transcript with retry logic."""
    logger.info("Fetching transcript...")

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(
                f"https://youtubetranscript.com/?server_vid2={video_id}",
                timeout=15
            )
            if resp.ok and len(resp.text) > 100:
                logger.info("✅ Transcript fetched successfully")
                return resp.text
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

    logger.warning("⚠️ Transcript unavailable after all retries")
    return "Transcript unavailable."


# -----------------------------
# ENHANCED AI NARRATIVE (v2 improvement)
# -----------------------------
def generate_ai_narrative(metadata: Dict[str, Any], transcript_text: str) -> Optional[str]:
    """Generate enhanced AI narrative with chapter awareness and rich context."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.warning("⚠️ Missing GROQ_API_KEY environment variable. Skipping AI narrative.")
        return None

    logger.info("🧠 Generating enhanced AI narrative via Groq...")

    # Build chapter context (v2 enhancement)
    chapter_info = ""
    if metadata.get('chapters'):
        chapter_info = "Video chapters:\n"
        for i, ch in enumerate(metadata['chapters'][:10], 1):
            timestamp = format_duration(int(ch['start_time']))
            chapter_info += f"{i}. [{timestamp}] {ch['title']}\n"

    # Build engagement context (v2 enhancement)
    engagement_info = ""
    if metadata.get('view_count'):
        views = metadata['view_count']
        likes = metadata.get('like_count', 0)
        engagement_info = f"\nEngagement: {views:,} views, {likes:,} likes"

    prompt = textwrap.dedent(f"""
    You are an expert technical content writer. Write a comprehensive, engaging blog article
    based on this YouTube video. Create content that adds value beyond just watching the video.

    VIDEO INFORMATION:
    Title: {metadata['title']}
    Channel: {metadata['uploader']}
    Duration: {format_duration(metadata.get('duration', 0))}
    Category: {', '.join(metadata.get('categories', ['General']))}
    {engagement_info}

    {chapter_info}

    Description: {metadata['description'][:600]}

    TRANSCRIPT EXCERPT:
    {transcript_text[:12000]}

    INSTRUCTIONS:
    Write a well-structured article with these sections:

    ## 🧭 Introduction (2-3 paragraphs)
    - Hook the reader with why this topic matters
    - Briefly explain what the video covers
    - Set expectations for what they'll learn

    ## 🔍 Step-by-Step Breakdown
    - Create a numbered list (4-7 items) of the main steps/concepts
    - Each item should be 1-2 sentences explaining the key point
    - Use chapter information if available to structure this

    ## 💡 Key Insights & Best Practices
    - Provide 5-7 actionable takeaways as bullet points
    - Focus on practical tips, gotchas, or important concepts
    - Go beyond what's obvious from the video title

    ## 🎯 When to Apply This
    - Brief paragraph (3-4 sentences) about practical use cases
    - Who should watch this and why
    - Real-world scenarios where this knowledge helps

    STYLE REQUIREMENTS:
    - Professional but conversational tone
    - Use technical terms accurately
    - Add context that enhances understanding
    - Total length: 600-900 words
    - Use markdown formatting
    - Include emojis in headers as shown

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
                "content": "You are a professional technical writer who creates engaging, informative blog posts that add value beyond the source material."
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 3000,
        "top_p": 0.9,
    }

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            logger.info("✅ Enhanced AI narrative generated successfully")
            return content
        except requests.RequestException as e:
            logger.warning(f"Groq API attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * attempt)

    logger.error("❌ Groq API failed after all retries")
    return None


# -----------------------------
# AUDIO PROCESSING (v1 functionality)
# -----------------------------
def split_audio_with_ffmpeg(audio_filepath: str, duration_sec: int, chunk_size_limit_bytes: int, target_dir: Path) -> Optional[list[Path]]:
    """Split audio for large file transcription."""
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


def transcribe_chunk_with_groq(audio_filepath: Path) -> str:
    """Transcribe audio chunk using Groq."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "ERROR: Missing API Key"

    headers = {"Authorization": f"Bearer {api_key}"}
    data = {'model': GROQ_TRANSCRIPT_MODEL}

    for attempt in range(MAX_RETRIES):
        try:
            with open(audio_filepath, 'rb') as audio_file:
                files = {'file': (audio_filepath.name, audio_file, 'audio/mp3')}

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


def generate_transcript_from_audio(metadata: Dict[str, Any], audio_filepath: str) -> str:
    """Generate transcript with chunking support."""
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
            logger.error(f"❌ Transcription failed: {transcript}")
            return "Automatic transcription failed."

        logger.info("✅ Transcript generated successfully.")
        return transcript.strip()

    # Chunking logic for large files
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

    # Cleanup
    for chunk_path in chunk_paths:
        os.remove(chunk_path)
    logger.info(f"✅ All {len(chunk_paths)} chunks transcribed and cleaned up successfully.")

    return " ".join(full_transcript).strip()


# -----------------------------
# DOWNLOAD FUNCTIONS
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
# GENERATE CHAPTERS SECTION (v2 enhancement)
# -----------------------------
def generate_chapters_markdown(chapters: List[Dict]) -> str:
    """Generate markdown for video chapters."""
    if not chapters:
        return ""

    md = "## 📑 Video Chapters\n\n"
    for i, ch in enumerate(chapters, 1):
        timestamp = format_duration(int(ch['start_time']))
        md += f"{i}. **[{timestamp}]** {ch['title']}\n"
    md += "\n"
    return md


# -----------------------------
# ENHANCED MARKDOWN GENERATION (v2 improvements)
# -----------------------------
def save_markdown(metadata: Dict[str, Any], transcript_text: str, audio_filepath: str, ai_article: Optional[str] = None) -> str:
    """Save enhanced markdown post with rich metadata."""
    slug = slugify(metadata["title"])
    date_str = parse_upload_date(metadata.get("upload_date"))

    # Create post directory
    post_dir = Path(CONTENT_DIR) / slug
    post_dir.mkdir(parents=True, exist_ok=True)
    filename = post_dir / "index.md"

    # Download assets
    thumb_filepath = post_dir / "asset.jpg"
    if metadata.get("thumbnail"):
        download_thumbnail(metadata["thumbnail"], str(thumb_filepath))

    if not Path(audio_filepath).exists():
        logger.warning(f"Audio file not found at {audio_filepath}. Audio link in markdown may be broken.")

    # Intelligent tagging (v2 enhancement)
    tags = categorize_video(
        metadata.get('categories', []),
        metadata.get('tags', []),
        metadata['title'],
        metadata['description']
    )
    tags_str = ", ".join([f'"{tag}"' for tag in tags])

    # Build summary
    summary = sanitize_text(
        metadata["description"].split('\n')[0][:180]
        if metadata["description"]
        else f"Watch this {format_duration(metadata.get('duration', 0))} tutorial by {metadata['uploader']}"
    )

    # Generate chapters section (v2 enhancement)
    chapters_md = generate_chapters_markdown(metadata.get('chapters', []))

    # Build engagement stats (v2 enhancement)
    stats_md = ""
    if metadata.get('view_count', 0) > 0:
        stats_md = f"""
## 📊 Video Stats

- **Views**: {metadata['view_count']:,}
- **Likes**: {metadata.get('like_count', 0):,}
- **Duration**: {format_duration(metadata.get('duration', 0))}
- **Published**: {date_str}
- **Subtitles**: {'Available' if metadata.get('subtitles_available') else 'Not available'}

"""

    # Enhanced frontmatter (v2 enhancement)
    frontmatter = f"""+++
title = "{sanitize_text(metadata['title'])}"
date = "{date_str}"
summary = "{summary}"
tags = [{tags_str}]
author = "{sanitize_text(metadata.get('uploader', 'Unknown'))}"

[extra]
youtube_url = "{metadata['webpage_url']}"
youtube_id = "{metadata['id']}"
channel_url = "{metadata.get('channel_url', '')}"
duration = {metadata.get('duration', 0)}
duration_formatted = "{format_duration(metadata.get('duration', 0))}"
thumbnail = "asset.jpg"
audio = "asset.mp3"
view_count = {metadata.get('view_count', 0)}
like_count = {metadata.get('like_count', 0)}
categories = {json.dumps(metadata.get('categories', []))}
has_chapters = {str(len(metadata.get('chapters', [])) > 0).lower()}
subtitles = {json.dumps(metadata.get('subtitles_available', False))}
+++

![{sanitize_text(metadata['title'])}](asset.jpg)

## 🎧 Listen to the Episode

<audio controls style="width: 100%;">
  <source src="asset.mp3" type="audio/mpeg">
  Your browser does not support the audio element.
</audio>

{stats_md}
{chapters_md}
{ai_article or '## 🧭 Introduction\\n\\n_AI-generated narrative unavailable. Please set GROQ_API_KEY environment variable._\\n\\n## 🔍 Key Points\\n\\n- Comprehensive video tutorial\\n- Detailed technical content\\n- Practical examples included'}

## 🗒️ Full Transcript

<details>
<summary>Click to expand complete transcript</summary>

{transcript_text}

</details>

## ▶️ Watch the Video

{('<div class="youtube-embed">\n<iframe width="560" height="315" src="https://www.youtube.com/embed/' + metadata['id'] + '" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>\n</div>\n\n' if metadata.get('embeddable', True) else '*⚠️ This video does not allow embedding. Please watch it directly on YouTube.*\n\n')}[🎥 Watch on YouTube]({metadata['webpage_url']}) | [📺 Visit Channel]({metadata.get('channel_url', metadata['webpage_url'])})

---

*This post was automatically generated from the video content. Video by {metadata['uploader']}.*
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(frontmatter)

    logger.info(f"✅ Enhanced markdown post saved: {filename}")
    logger.info(f"   Tags: {', '.join(tags)}")
    logger.info(f"   Chapters: {len(metadata.get('chapters', []))}")
    logger.info(f"   Subtitles: {metadata.get('subtitles_available', False)}")

    return str(filename)


# -----------------------------
# MAIN EXECUTION
# -----------------------------
def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Generate enhanced Markdown blog post from YouTube video.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          %(prog)s --youtube https://www.youtube.com/watch?v=VIDEO_ID
          %(prog)s --youtube https://youtu.be/VIDEO_ID --verbose

        Environment Variables:
          GROQ_API_KEY    API key for Groq AI narrative generation

        Features:
          ✓ Working YouTube embedding (based on v1)
          ✓ Enhanced metadata extraction (v2 additions)
          ✓ Chapter-aware AI narrative (v2 enhancement)
          ✓ Intelligent auto-categorization and tagging
          ✓ Rich frontmatter with extensive metadata
          ✓ Audio transcription with chunking support
        """)
    )
    parser.add_argument("--youtube", required=True, help="YouTube video URL")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    initial_checks()

    logger.info("=" * 70)
    logger.info("🚀 Starting Enhanced Blog Post Generation (v3.0)")
    logger.info("=" * 70)

    # Fetch enhanced metadata
    meta = fetch_youtube_info(args.youtube)
    if not meta:
        logger.error("❌ Failed to fetch video metadata. Exiting.")
        sys.exit(1)

    logger.info(f"📹 Video: {meta['title']}")
    logger.info(f"👤 Author: {meta['uploader']}")
    logger.info(f"⏱️  Duration: {format_duration(meta.get('duration', 0))}")
    logger.info(f"👁️  Views: {meta.get('view_count', 0):,}")
    logger.info(f"📑 Chapters: {len(meta.get('chapters', []))}")

    slug = slugify(meta["title"])
    post_bundle_dir = Path(CONTENT_DIR) / slug
    audio_filepath = post_bundle_dir / "asset.mp3"

    # Download audio
    post_bundle_dir.mkdir(parents=True, exist_ok=True)
    audio_downloaded = download_audio(meta["id"], str(audio_filepath))

    transcript_text = ""
    if audio_downloaded:
        transcript_text = generate_transcript_from_audio(meta, str(audio_filepath))
    else:
        transcript_text = "Automatic transcription failed because the audio file could not be downloaded."

    # Generate enhanced AI narrative (v2 improvement)
    ai_article = generate_ai_narrative(meta, transcript_text)

    # Save enhanced markdown
    filename = save_markdown(meta, transcript_text, str(audio_filepath), ai_article)

    logger.info("=" * 70)
    logger.info(f"✅ Blog post generation complete!")
    logger.info(f"📄 File: {filename}")
    logger.info(f"🏷️  Auto-generated {len(categorize_video(meta.get('categories', []), meta.get('tags', []), meta['title'], meta['description']))} relevant tags")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
