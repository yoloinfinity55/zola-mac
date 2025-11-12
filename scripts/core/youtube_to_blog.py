#!/usr/bin/env python3
"""
YouTube to Blog Converter
Main entry point for converting YouTube videos to blog posts with AI narration.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Import our modular processors
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from processors.youtube_processor import (
    fetch_youtube_info, download_audio, validate_youtube_url,
    parse_upload_date, format_duration, sanitize_text, download_youtube_subtitles
)
from processors.ai_processor import (
    transcribe_audio_with_groq, generate_ai_summary_and_structure,
    generate_final_article, generate_social_media_post
)
from processors.image_processor import generate_blog_thumbnail, download_youtube_thumbnail
from processors.tts_engine import generate_audio_from_text, validate_audio_file

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

# Constants
BASE_CONTENT = Path("content/blog")
OUTPUT_FOLDER = Path("audio_output")


def create_youtube_markdown(metadata: dict, transcript_text: str, has_audio: bool = False, ai_structure: Optional[str] = None,
                           final_article: Optional[str] = None, social_post: Optional[str] = None) -> str:
    """
    Create Zola markdown post for YouTube video with full content.

    Args:
        metadata: YouTube video metadata
        transcript_text: Video transcript
        ai_structure: AI-generated summary structure
        final_article: AI-generated full article
        social_post: Social media post text

    Returns:
        Complete markdown content
    """
    # Prepare metadata
    title = sanitize_text(metadata.get("title", "YouTube Video"))
    upload_date = parse_upload_date(metadata.get("upload_date", ""))
    if not upload_date:
        from datetime import datetime
        upload_date = datetime.now().strftime('%Y-%m-%d')

    duration = format_duration(metadata.get("duration", 0))
    uploader = sanitize_text(metadata.get("uploader", "Unknown"))
    tags = metadata.get("tags", [])[:5]
    tags_str = ", ".join([f'"{tag}"' for tag in tags]) if tags else '"youtube", "video", "tutorial"'

    # Front matter
    front_matter = f"""+++
title = "{title}"
date = "{upload_date}"
tags = [{tags_str}]
+++

"""

    # Content sections
    content = front_matter

    # Thumbnail
    content += f"![{title}](asset.jpg)\n\n"

    # TL;DR
    description = metadata.get("description", "")[:200]
    if description:
        content += f"## TL;DR (Quick Summary)\n\n> {sanitize_text(description)}\n\n"

    # Audio player (only if audio is available)
    if has_audio:
        content += """## 🎧 Listen to the Episode

<audio controls style="width: 100%;">
  <source src="asset.mp3" type="audio/mpeg">
  Your browser does not support the audio element.
</audio>

"""

    # AI-generated content
    if ai_structure:
        content += f"## 📋 Structured Key Takeaways\n\n{ai_structure}\n\n---\n\n"

    # Transcript
    if transcript_text and transcript_text != "ERROR: Audio transcription failed after all retries.":
        content += f"## 📝 Transcript (Auto-Generated)\n\n> {transcript_text[:1000]}...\n\n---\n\n"

    # Full article
    if final_article:
        content += f"## 📝 Full Article Narrative\n\n{final_article}\n\n---\n\n"

    # Video embed
    video_id = metadata.get("id")
    if video_id:
        content += f"""## ▶️ Watch the Video

* **Author:** {uploader}
* **Duration:** {duration}

<div class="youtube-embed">
<iframe width="560" height="315" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen></iframe>
</div>

[Watch on YouTube]({metadata.get("webpage_url", f"https://www.youtube.com/watch?v={video_id}")})

"""

    # Social media post
    if social_post:
        content += f"""---\n\n## 🐦 Social Media Post (X/Twitter)

**Copy and Paste for Promotion (280 Character Limit):**

{social_post}

"""

    return content


def save_metadata(metadata: dict, json_path: Path) -> None:
    """
    Save processing metadata to JSON file.

    Args:
        metadata: Dictionary containing processing metadata
        json_path: Path to save JSON file
    """
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    logger.info(f"✅ Metadata saved: {json_path}")


def save_raw_text(text: str, txt_path: Path) -> None:
    """
    Save raw text content to file.

    Args:
        text: Raw text content
        txt_path: Path to save text file
    """
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)
    logger.info(f"✅ Raw text saved: {txt_path}")


async def process_youtube_video(url: str) -> bool:
    """
    Process a YouTube video into a blog post with AI narration.

    Args:
        url: YouTube video URL

    Returns:
        True if processing successful, False otherwise
    """
    post_dir = None
    try:
        logger.info(f"🚀 Starting YouTube video processing: {url}")

        # 1. Validate URL
        if not validate_youtube_url(url):
            logger.error("❌ Invalid YouTube URL format")
            return False

        # 2. Fetch video metadata
        logger.info("📄 Fetching YouTube video metadata...")
        metadata = fetch_youtube_info(url)
        if not metadata:
            logger.error("❌ Failed to fetch video metadata")
            return False

        video_id = metadata.get("id")
        if not video_id:
            logger.error("❌ No video ID found in metadata")
            return False

        # 3. Generate slug and create directories
        from processors.content_scraper import slugify, get_content_paths
        slug = slugify(metadata.get("title", "youtube-video"))
        paths = get_content_paths(slug)
        post_dir = BASE_CONTENT / slug

        logger.info(f"📁 Processing video: {slug}")

        # 4. Download audio (try to download, create empty file if it fails)
        logger.info("🎵 Downloading video audio...")
        audio_downloaded = download_audio(video_id, paths["mp3"])
        if not audio_downloaded:
            logger.warning("⚠️ Audio download failed - creating empty placeholder file")
            # Create empty audio file as placeholder for consistent file structure
            with open(paths["mp3"], 'w') as f:
                f.write("")

        # 5. Get transcript - try YouTube subtitles first, then AI transcription
        logger.info("📝 Getting transcript...")
        transcript = ""

        # First try YouTube subtitles
        transcript_content = None
        if video_id:
            logger.info("🎭 Checking for YouTube subtitles/captions...")
            transcript_content = download_youtube_subtitles(video_id, post_dir)

        if transcript_content:
            transcript = transcript_content
            save_raw_text(transcript, paths["txt"])
            logger.info("📄 Saved YouTube transcript to asset.txt")
        else:
            # Fallback to AI transcription
            logger.info("ℹ️ No YouTube subtitles available, using AI transcription...")
            if audio_downloaded and GROQ_API_KEY:
                transcript = transcribe_audio_with_groq(str(paths["mp3"]), GROQ_API_KEY)
                if transcript.startswith("ERROR:"):
                    logger.warning(f"⚠️ AI transcription failed: {transcript}")
                    transcript = ""  # Reset to empty for fallback handling
                    # Final fallback to video description
                    video_description = metadata.get("description", "")
                    if video_description.strip():
                        save_raw_text(video_description, paths["txt"])
                        logger.info("📄 Saved video description to asset.txt")
                    else:
                        save_raw_text("Video description not available.", paths["txt"])
                else:
                    # Update asset.txt with AI transcript if transcription succeeded
                    if transcript.strip() and len(transcript.strip()) > 100:  # Meaningful transcript
                        save_raw_text(transcript, paths["txt"])
                        logger.info("📄 Updated asset.txt with AI-generated transcript")
                    else:
                        logger.info("📄 AI transcript too short, using video description")
                        video_description = metadata.get("description", "")
                        if video_description.strip():
                            save_raw_text(video_description, paths["txt"])
                        else:
                            save_raw_text("Video description not available.", paths["txt"])
            else:
                logger.warning("⚠️ Cannot perform AI transcription - missing audio or API key")
                # Fallback to video description
                video_description = metadata.get("description", "")
                if video_description.strip():
                    save_raw_text(video_description, paths["txt"])
                    logger.info("📄 Saved video description to asset.txt")
                else:
                    save_raw_text("Video description not available.", paths["txt"])

        # 6. Generate AI content (use any available content)
        ai_structure = None
        final_article = None
        social_post = None

        # Use transcript if available, otherwise use description
        content_for_ai = ""
        if transcript and transcript != "ERROR: Audio transcription failed after all retries." and len(transcript.strip()) > 50:
            content_for_ai = transcript
            logger.info("🧠 Generating AI content from transcript...")
        else:
            # Fallback to video description + title
            video_description = metadata.get("description", "")
            video_title = metadata.get("title", "")
            content_for_ai = f"{video_title}\n\n{video_description}"
            logger.info("🧠 Generating AI content from video description...")

        if content_for_ai.strip() and GROQ_API_KEY:
            # Generate structured summary
            ai_structure = generate_ai_summary_and_structure(
                metadata.get("title", ""),
                metadata.get("description", ""),
                content_for_ai,
                GROQ_API_KEY
            )

            # Generate full article
            final_article = generate_final_article(
                metadata.get("title", ""),
                metadata.get("description", ""),
                content_for_ai,
                ai_structure or "",
                GROQ_API_KEY
            )

            # Generate social media post
            social_post = generate_social_media_post(
                metadata.get("title", ""),
                metadata.get("description", ""),
                metadata.get("tags", []),
                GROQ_API_KEY
            )

        # 7. Download YouTube thumbnail
        logger.info("🖼️ Downloading YouTube video thumbnail...")
        thumbnail_url = metadata.get("thumbnail")
        if thumbnail_url:
            success = download_youtube_thumbnail(thumbnail_url, post_dir / "asset.jpg")
            if not success:
                logger.warning("⚠️ YouTube thumbnail download failed, generating AI thumbnail...")
                generate_blog_thumbnail(
                    metadata.get("description", ""),
                    metadata.get("title", ""),
                    post_dir,
                    slug,
                    GROQ_API_KEY,
                    UNSPLASH_ACCESS_KEY
                )
        else:
            logger.warning("⚠️ No thumbnail URL in metadata, generating AI thumbnail...")
            generate_blog_thumbnail(
                metadata.get("description", ""),
                metadata.get("title", ""),
                post_dir,
                slug,
                GROQ_API_KEY,
                UNSPLASH_ACCESS_KEY
            )

        # 8. Create Zola markdown post
        logger.info("📝 Creating Zola markdown post...")
        # Check if we have valid audio
        has_audio = audio_downloaded and validate_audio_file(paths["mp3"])
        markdown_content = create_youtube_markdown(
            metadata, transcript, has_audio, ai_structure, final_article, social_post
        )

        with open(paths["md"], "w", encoding="utf-8") as f:
            f.write(markdown_content)

        # 9. Generate audio narration (if we have content to narrate)
        narration_text = ""
        if final_article:
            narration_text = final_article
        elif ai_structure:
            narration_text = ai_structure
        elif transcript:
            narration_text = transcript[:2000]  # Limit for TTS

        if narration_text and GROQ_API_KEY:
            logger.info("🔊 Generating AI narration...")
            # Create a summary for narration
            summary = ""
            if GROQ_API_KEY:
                from processors.ai_processor import summarize_text_with_groq
                summary = summarize_text_with_groq(narration_text, GROQ_API_KEY, summary_ratio=0.4)

            if summary:
                await generate_audio_from_text(summary, paths["mp3"].parent / "narration.mp3")

        # Validate audio file
        if not validate_audio_file(paths["mp3"]):
            logger.warning("⚠️ Audio file validation failed, but continuing...")

        # 10. Save metadata
        processing_metadata = {
            "url": url,
            "video_id": video_id,
            "slug": slug,
            "title": metadata.get("title"),
            "uploader": metadata.get("uploader"),
            "duration": metadata.get("duration"),
            "upload_date": metadata.get("upload_date"),
            "view_count": metadata.get("view_count"),
            "processing_date": str(Path.cwd()),
            "audio_file": str(paths["mp3"]),
            "transcript_length": len(transcript) if transcript else 0,
            "has_ai_content": bool(ai_structure or final_article),
            "thumbnail_file": str(post_dir / "asset.jpg"),
        }
        save_metadata(processing_metadata, paths["json"])

        # 11. Clean up temporary files
        logger.info("🧹 Cleaning up temporary files...")
        import shutil

        # Clean up tmp directory in post folder
        tmp_dir = post_dir / "tmp"
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
            logger.info("✅ Post tmp directory cleaned up")

        # Clean up any subtitle files that were downloaded
        subtitle_files = list(post_dir.glob("subtitles*"))
        for subtitle_file in subtitle_files:
            subtitle_file.unlink()
            logger.info(f"🗑️ Removed subtitle file: {subtitle_file.name}")

        # Clean up any other temporary files yt-dlp might have created
        temp_files = list(post_dir.glob("*.temp")) + list(post_dir.glob("*.part"))
        for temp_file in temp_files:
            temp_file.unlink()
            logger.info(f"🗑️ Removed temp file: {temp_file.name}")

        logger.info("✅ All temporary files cleaned up")

        logger.info("✅ YouTube video processing completed successfully!")
        logger.info(f"📄 Post available at: content/blog/{slug}/index.md")
        return True

    except Exception as e:
        logger.exception(f"❌ YouTube video processing failed: {e}")
        return False

    finally:
        # Ensure cleanup happens even on failure
        if post_dir and post_dir.exists():
            logger.info("🧹 Running cleanup...")
            import shutil

            # Clean up tmp directory in post folder
            tmp_dir = post_dir / "tmp"
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir)
                logger.info("✅ Post tmp directory cleaned up")

            # Clean up any subtitle files that were downloaded
            subtitle_files = list(post_dir.glob("subtitles*"))
            for subtitle_file in subtitle_files:
                subtitle_file.unlink()
                logger.info(f"🗑️ Removed subtitle file: {subtitle_file.name}")

            # Clean up any other temporary files yt-dlp might have created
            temp_files = list(post_dir.glob("*.temp")) + list(post_dir.glob("*.part"))
            for temp_file in temp_files:
                temp_file.unlink()
                logger.info(f"🗑️ Removed temp file: {temp_file.name}")


def main():
    """Main entry point for YouTube to blog conversion."""
    if len(sys.argv) < 2:
        logger.error("❌ Usage: python youtube_to_blog.py <youtube_url>")
        logger.info("Example: python youtube_to_blog.py https://www.youtube.com/watch?v=VIDEO_ID")
        sys.exit(1)

    url = sys.argv[1]

    # Validate URL format
    if not url.startswith(('http://', 'https://')):
        logger.error("❌ Invalid URL format. Must start with http:// or https://")
        sys.exit(1)

    # Ensure required directories exist
    BASE_CONTENT.mkdir(parents=True, exist_ok=True)
    OUTPUT_FOLDER.mkdir(exist_ok=True)

    # Check for API keys
    if not GROQ_API_KEY:
        logger.warning("⚠️ GROQ_API_KEY not found. AI features will be limited.")
    if not UNSPLASH_ACCESS_KEY:
        logger.warning("⚠️ UNSPLASH_ACCESS_KEY not found. Thumbnail generation may be limited.")

    # Process the video
    success = asyncio.run(process_youtube_video(url))

    if success:
        logger.info("🎉 YouTube video processing completed successfully!")
        logger.info("💡 Run 'zola build' to update your site with the new post.")
    else:
        logger.error("💥 Processing failed. Check the logs above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
