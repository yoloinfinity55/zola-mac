#!/usr/bin/env python3
"""
Web to Blog Converter
Main entry point for converting web articles to blog posts with AI narration.
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

from processors.content_scraper import fetch_content, slugify, get_content_paths
from processors.tts_engine import generate_audio_from_text, validate_audio_file
from processors.image_processor import generate_blog_thumbnail
from processors.ai_processor import summarize_text_with_groq

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


def create_zola_markdown(text: str, headings: list, title: str, pub_date: str, md_path: Path) -> None:
    """
    Create Zola markdown post with front matter and content.

    Args:
        text: Main article text
        headings: List of (tag, heading) tuples
        title: Article title
        pub_date: Publication date
        md_path: Path to save markdown file
    """
    front_matter = f"""+++
title = "{title}"
date = "{pub_date}"
+++

"""

    md_content = front_matter

    # Add headings as H2 sections
    for tag, heading in headings:
        level = int(tag[1])  # h1, h2, h3 -> 1, 2, 3
        md_content += f"{'#' * level} {heading}\n\n"

    # Add main content
    md_content += text

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    logger.info(f"✅ Zola post created: {md_path}")


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
    Save raw extracted text to file.

    Args:
        text: Raw text content
        txt_path: Path to save text file
    """
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)
    logger.info(f"✅ Raw text saved: {txt_path}")


async def process_web_article(url: str) -> bool:
    """
    Process a web article into a blog post with audio narration.

    Args:
        url: URL of the web article to process

    Returns:
        True if processing successful, False otherwise
    """
    try:
        logger.info(f"🚀 Starting web article processing: {url}")

        # 1. Scrape content from web
        logger.info("📄 Scraping web content...")
        text, headings, title, pub_date = fetch_content(url)

        if not text.strip():
            logger.error("❌ No content extracted from URL")
            return False

        # 2. Generate slug and create directories
        slug = slugify(url)
        paths = get_content_paths(slug)
        post_dir = BASE_CONTENT / slug

        logger.info(f"📁 Processing post: {slug}")

        # 3. Save raw text
        save_raw_text(text, paths["txt"])

        # 4. Generate AI summary for TTS (shorter for audio)
        logger.info("🧠 Generating AI summary for audio narration...")
        if GROQ_API_KEY:
            summary = summarize_text_with_groq(text, GROQ_API_KEY, summary_ratio=0.3)
        else:
            summary = text  # Use original text if no API key

        # 5. Generate thumbnail
        logger.info("🖼️ Generating blog thumbnail...")
        generate_blog_thumbnail(text, title, post_dir, slug, GROQ_API_KEY, UNSPLASH_ACCESS_KEY)

        # 6. Create Zola markdown post
        logger.info("📝 Creating Zola markdown post...")
        create_zola_markdown(text, headings, title, pub_date, paths["md"])

        # 7. Generate audio narration
        logger.info("🔊 Generating audio narration...")
        await generate_audio_from_text(summary, paths["mp3"])

        # Validate audio file
        if not validate_audio_file(paths["mp3"]):
            logger.warning("⚠️ Audio file validation failed, but continuing...")

        # 8. Save metadata
        metadata = {
            "url": url,
            "slug": slug,
            "title": title,
            "pub_date": pub_date,
            "processing_date": str(Path.cwd()),
            "audio_file": str(paths["mp3"]),
            "text_file": str(paths["txt"]),
            "markdown_file": str(paths["md"]),
            "thumbnail_file": str(post_dir / "asset.jpg"),
            "content_length": len(text),
            "headings_count": len(headings)
        }
        save_metadata(metadata, paths["json"])

        logger.info("✅ Web article processing completed successfully!")
        logger.info(f"📄 Post available at: content/blog/{slug}/index.md")
        return True

    except Exception as e:
        logger.exception(f"❌ Web article processing failed: {e}")
        return False


def main():
    """Main entry point for web-to-blog conversion."""
    if len(sys.argv) < 2:
        logger.error("❌ Usage: python web_to_blog.py <url>")
        logger.info("Example: python web_to_blog.py https://example.com/article")
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
        logger.warning("⚠️ GROQ_API_KEY not found. Audio summarization will be skipped.")
    if not UNSPLASH_ACCESS_KEY:
        logger.warning("⚠️ UNSPLASH_ACCESS_KEY not found. Thumbnail generation may be limited.")

    # Process the article
    success = asyncio.run(process_web_article(url))

    if success:
        logger.info("🎉 Processing completed successfully!")
        logger.info("💡 Run 'zola build' to update your site with the new post.")
    else:
        logger.error("💥 Processing failed. Check the logs above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
