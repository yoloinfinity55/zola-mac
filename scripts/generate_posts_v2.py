#!/usr/bin/env python3
"""
generate_posts.py (Enhanced v3.0)
-----------------------------------
Advanced blog post generator for Zola with rich YouTube metadata.
- Comprehensive yt-dlp metadata extraction
- Chapter-based content structure
- Enhanced AI narrative with context
- Multi-quality thumbnail and audio options
- Automatic categorization and tagging
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
from PIL import Image
import io
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
import toml

# -----------------------------
# CONFIGURATION
# -----------------------------
CONTENT_DIR = "content/blog"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_RETRIES = 3
RETRY_DELAY = 2

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
    td = timedelta(seconds=seconds)
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    secs = td.seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def parse_upload_date(upload_date: Optional[str]) -> str:
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
# ENHANCED YOUTUBE METADATA EXTRACTION
# -----------------------------
def fetch_youtube_info(url: str) -> Optional[Dict[str, Any]]:
    """Fetch comprehensive YouTube video metadata."""
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

        # Extract chapters if available
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

        # Get best quality info (may not be available with minimal options)
        formats = info.get('formats', [])
        best_audio = {}
        best_video = {}
        if formats:
            best_audio = next((f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none'), {})
            best_video = next((f for f in formats if f.get('vcodec') != 'none' and f.get('height', 0) >= 720), {})

        # Extract subtitles info (may not be available with minimal options)
        subtitles_available = []
        if info.get('subtitles'):
            subtitles_available = list(info.get('subtitles', {}).keys())
        elif info.get('automatic_captions'):
            subtitles_available = list(info.get('automatic_captions', {}).keys())
        
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
            "age_limit": info.get("age_limit", 0),
            "is_live": info.get("is_live", False),
            "embeddable": info.get("embeddable", True),
            "chapters": chapters,
            "subtitles_available": subtitles_available,
            "resolution": best_video.get("height", "Unknown"),
            "fps": best_video.get("fps", 30),
            "audio_bitrate": best_audio.get("abr", 128),
            "language": info.get("language", "en"),
            "availability": info.get("availability", "public"),
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
# ENHANCED AI NARRATIVE
# -----------------------------
def generate_ai_narrative(metadata: Dict[str, Any], transcript_text: str) -> Optional[str]:
    """Generate enhanced AI narrative with chapter awareness and rich context."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.warning("⚠️ Missing GROQ_API_KEY environment variable. Skipping AI narrative.")
        return None

    logger.info("🧠 Generating AI narrative via Groq...")

    # Build chapter context
    chapter_info = ""
    if metadata.get('chapters'):
        chapter_info = "Video chapters:\n"
        for i, ch in enumerate(metadata['chapters'][:10], 1):
            timestamp = format_duration(int(ch['start_time']))
            chapter_info += f"{i}. [{timestamp}] {ch['title']}\n"
    
    # Build engagement context
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
            logger.info("✅ AI narrative generated successfully")
            return content
        except requests.RequestException as e:
            logger.warning(f"Groq API attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * attempt)
    
    logger.error("❌ Groq API failed after all retries")
    return None


# -----------------------------
# DOWNLOAD ASSETS
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


def download_audio(video_id: str, filepath: str) -> bool:
    """Download highest quality audio."""
    logger.info(f"Downloading audio to {filepath}")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': filepath.replace('.mp3', ''),
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
# GENERATE CHAPTERS SECTION
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
# SAVE ENHANCED MARKDOWN POST
# -----------------------------
def save_markdown(metadata: Dict[str, Any], transcript_text: str, ai_article: Optional[str] = None) -> str:
    """Save enhanced markdown post with rich metadata in a dedicated folder."""
    slug = slugify(metadata["title"])
    date_str = parse_upload_date(metadata.get("upload_date"))
    
    # Create a directory for the post
    post_dir = Path(CONTENT_DIR) / slug
    post_dir.mkdir(parents=True, exist_ok=True)
    
    filename = post_dir / "index.md"
    
    # Define asset paths within the post's directory
    thumb_filename = post_dir / "asset.jpg"
    audio_filename = post_dir / "asset.mp3"
    
    # Download assets
    if metadata.get("thumbnail"):
        download_thumbnail(metadata["thumbnail"], str(thumb_filename))
    
    download_audio(metadata["id"], str(audio_filename))
    
    # Intelligent tagging
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
    
    # Generate chapters section
    chapters_md = generate_chapters_markdown(metadata.get('chapters', []))
    
    # Build engagement stats
    stats_md = ""
    if metadata.get('view_count', 0) > 0:
        stats_md = f"""
## 📊 Video Stats

- **Views**: {metadata['view_count']:,}
- **Likes**: {metadata.get('like_count', 0):,}
- **Duration**: {format_duration(metadata.get('duration', 0))}
- **Published**: {date_str}
- **Quality**: {metadata.get('resolution', 'HD')}p @ {metadata.get('fps', 30)} FPS

"""
    
    # Build markdown with relative paths for assets
    md = f"""+++
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
subtitles = {json.dumps(metadata.get('subtitles_available', []))}
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

{('<div class="youtube-embed">\n<iframe width="560" height="315" src="https://www.youtube.com/embed/' + metadata['id'] + '" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>\n</div>\n\n' if metadata.get('embeddable', True) else '')}[🎥 Watch on YouTube]({metadata['webpage_url']}) | [📺 Visit Channel]({metadata.get('channel_url', metadata['webpage_url'])})

---

*This post was automatically generated from the video content. Video by {metadata['uploader']}.*
"""
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md)
    
    logger.info(f"✅ Markdown post saved: {filename}")
    logger.info(f"   Tags: {', '.join(tags)}")
    logger.info(f"   Chapters: {len(metadata.get('chapters', []))}")
    logger.info(f"   Subtitles: {len(metadata.get('subtitles_available', []))}")
    
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
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Generate enhanced Markdown blog post from YouTube video.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          %(prog)s --youtube https://www.youtube.com/watch?v=VIDEO_ID
          %(prog)s --youtube https://youtu.be/VIDEO_ID --verbose
        
        Environment Variables:
          GROQ_API_KEY    API key for Groq AI narrative generation (required for AI content)
        
        Features:
          ✓ Comprehensive metadata extraction (views, likes, chapters, etc.)
          ✓ Intelligent auto-categorization and tagging
          ✓ Chapter-aware AI narrative generation
          ✓ High-quality audio and thumbnail download
          ✓ Rich frontmatter with extensive metadata
          ✓ Engagement statistics display
        """)
    )
    parser.add_argument("--youtube", required=True, help="YouTube video URL")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info("=" * 70)
    logger.info("🚀 Starting Enhanced Blog Post Generation (v3.0)")
    logger.info("=" * 70)
    
    # Fetch comprehensive metadata
    meta = fetch_youtube_info(args.youtube)
    if not meta:
        logger.error("❌ Failed to fetch video metadata. Exiting.")
        sys.exit(1)
    
    logger.info(f"📹 Video: {meta['title']}")
    logger.info(f"👤 Author: {meta['uploader']}")
    logger.info(f"⏱️  Duration: {format_duration(meta.get('duration', 0))}")
    logger.info(f"👁️  Views: {meta.get('view_count', 0):,}")
    logger.info(f"📑 Chapters: {len(meta.get('chapters', []))}")
    
    # Fetch transcript
    transcript = fetch_transcript(meta["id"])
    
    # Generate enhanced AI narrative
    ai_article = generate_ai_narrative(meta, transcript)
    
    # Save markdown
    filename = save_markdown(meta, transcript, ai_article)
    
    logger.info("=" * 70)
    logger.info(f"✅ Blog post generation complete!")
    logger.info(f"📄 File: {filename}")
    logger.info(f"🏷️  Auto-generated {len(categorize_video(meta.get('categories', []), meta.get('tags', []), meta['title'], meta['description']))} relevant tags")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
