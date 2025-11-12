#!/usr/bin/env python3
"""
generate_thumbnails.py
----------------------
Script to generate thumbnails for existing blog posts that don't have them.
Uses AI to analyze content and find appropriate images from free sources.
"""

import os
import json
import toml
from pathlib import Path
from urllib.parse import quote
import random
import logging

import requests
from dotenv import load_dotenv
from PIL import Image
import io

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load .env
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

CONTENT_DIR = "content/blog"


def generate_image_keywords_with_ai(text: str, title: str, post_slug: str) -> str:
    """Use AI to analyze blog content and generate relevant image search keywords"""
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set. Using fallback keywords.")
        return "technology blog article"

    logger.info("🧠 Generating image search keywords using AI...")

    # Create a more specific prompt that encourages uniqueness
    prompt = f"""
    Analyze this blog post and generate UNIQUE, SPECIFIC keywords for stock image search.
    Focus on the most distinctive visual elements and themes.

    TITLE: {title}
    SLUG: {post_slug}

    CONTENT SAMPLE:
    {text[:1200]}

    Generate 4-6 UNIQUE keywords that would help find a distinctive stock image.
    Be specific and avoid generic terms like "technology" or "computer" unless they're central.
    Focus on visual concepts, objects, scenes, or abstract concepts that could be illustrated.

    Return ONLY the keywords separated by commas, no other text.
    Examples:
    - For a coding tutorial: "laptop screen, code editor, programming, syntax highlighting, developer workspace"
    - For a history article: "ancient scroll, emperor portrait, dynasty artifacts, historical manuscript"
    - For an AI article: "neural network visualization, circuit board, artificial brain, data streams"
    """

    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,  # Increased for more variety
            "max_tokens": 120
        }

        resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        keywords = resp.json()["choices"][0]["message"]["content"].strip()

        # Clean and validate keywords
        keywords = keywords.strip('",.').replace('"', '').replace("'", "")
        if len(keywords.split(',')) < 3:
            # If AI didn't give enough keywords, add some variety
            base_keywords = keywords.split(',')
            additional_terms = ['digital', 'modern', 'concept', 'visual', 'illustration']
            while len(base_keywords) < 5:
                base_keywords.append(additional_terms[len(base_keywords) % len(additional_terms)])
            keywords = ', '.join(base_keywords)

        logger.info(f"✅ Generated keywords: {keywords}")
        return keywords
    except Exception as e:
        logger.error(f"AI keyword generation failed: {e}. Using fallback.")
        return "technology blog article"


def search_unsplash_image(keywords: str, title: str) -> str:
    """Search for a free image on Unsplash based on keywords"""
    logger.info(f"🔍 Searching Unsplash for images with keywords: {keywords}")

    # Use the first keyword for search
    search_term = keywords.split(',')[0].strip() if keywords != "technology blog article" else title.split()[0]

    # Try multiple search terms if the first one fails
    search_terms = [search_term]
    if len(title.split()) > 1:
        search_terms.append(title.split()[1])
    search_terms.extend(['technology', 'digital', 'computer', 'abstract'])

    for term in search_terms[:3]:  # Try up to 3 different terms
        url = f"https://api.unsplash.com/search/photos?query={quote(term)}&per_page=20&orientation=landscape"

        # Try with client ID if available, otherwise use public access
        headers = {'Accept-Version': 'v1'}
        unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY")
        if unsplash_key and unsplash_key.strip():
            headers['Authorization'] = f'Client-ID {unsplash_key}'

        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('results') and len(data['results']) > 0:
                    # Pick a random image from results
                    image_data = random.choice(data['results'])
                    image_url = image_data['urls']['regular']
                    logger.info(f"✅ Found Unsplash image for '{term}': {image_url}")
                    return image_url
            elif resp.status_code == 401:
                logger.warning(f"Unsplash API authentication failed for term '{term}'")
            else:
                logger.warning(f"Unsplash API returned status {resp.status_code} for term '{term}'")
        except Exception as e:
            logger.error(f"Unsplash search failed for term '{term}': {e}")

    # Multiple fallback URLs based on content hash to ensure variety
    import hashlib
    content_hash = hashlib.md5((keywords + title).encode()).hexdigest()
    hash_int = int(content_hash[:8], 16)

    fallback_urls = [
        "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800&h=450&fit=crop",
        "https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=800&h=450&fit=crop",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&h=450&fit=crop",
        "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&h=450&fit=crop",
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&h=450&fit=crop",
        "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=800&h=450&fit=crop",
        "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&h=450&fit=crop",
        "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=450&fit=crop"
    ]

    fallback_url = fallback_urls[hash_int % len(fallback_urls)]
    logger.info(f"Using fallback image: {fallback_url}")
    return fallback_url


def download_and_process_image(image_url: str, filepath: str) -> bool:
    """Download image from URL and crop to 16:9 aspect ratio"""
    logger.info(f"📥 Downloading and processing image to {filepath}")

    try:
        resp = requests.get(image_url, timeout=15)
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
        cropped_image.save(filepath, "JPEG", quality=85)

        logger.info("✅ Image downloaded and cropped successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Image download/processing failed: {e}")
        return False


def generate_thumbnail_for_post(post_dir: Path) -> bool:
    """Generate thumbnail for a single blog post"""
    md_file = post_dir / "index.md"
    thumb_path = post_dir / "asset.jpg"

    # Skip if thumbnail already exists
    if thumb_path.exists():
        logger.info(f"Thumbnail already exists for {post_dir.name}, skipping")
        return True

    # Check if markdown file exists
    if not md_file.exists():
        logger.warning(f"No index.md found in {post_dir}, skipping")
        return False

    try:
        # Read the markdown file
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract title from frontmatter
        title = post_dir.name  # fallback
        end_frontmatter = -1
        if content.startswith("+++"):
            end_frontmatter = content.find("+++", 3)
            if end_frontmatter != -1:
                frontmatter_str = content[3:end_frontmatter].strip()
                frontmatter = toml.loads(frontmatter_str)
                title = frontmatter.get("title", title)

        # Try to get content from asset.txt if it exists
        text_content = ""
        txt_file = post_dir / "asset.txt"
        if txt_file.exists():
            with open(txt_file, "r", encoding="utf-8") as f:
                text_content = f.read()
        else:
            # Extract content from markdown (after frontmatter)
            if end_frontmatter != -1:
                text_content = content[end_frontmatter + 3:].strip()

        if not text_content:
            logger.warning(f"No content found for {post_dir.name}, using title-only analysis")
            text_content = title

        logger.info(f"Processing {post_dir.name}: {title}")

        # Generate keywords using AI
        keywords = generate_image_keywords_with_ai(text_content, title, post_dir.name)

        # Search for image
        image_url = search_unsplash_image(keywords, title)

        # Download and process image
        success = download_and_process_image(image_url, str(thumb_path))

        if success:
            logger.info(f"✅ Thumbnail generated for {post_dir.name}")
        return success

    except Exception as e:
        logger.error(f"Failed to generate thumbnail for {post_dir.name}: {e}")
        return False


def main():
    """Generate thumbnails for all blog posts that don't have them"""
    logger.info("🔍 Scanning for blog posts without thumbnails...")

    content_path = Path(CONTENT_DIR)
    if not content_path.exists():
        logger.error(f"Content directory {CONTENT_DIR} does not exist")
        return

    processed = 0
    successful = 0

    # Find all blog post directories
    for post_dir in content_path.iterdir():
        if post_dir.is_dir() and (post_dir / "index.md").exists():
            processed += 1
            if generate_thumbnail_for_post(post_dir):
                successful += 1

    logger.info(f"📊 Processed {processed} posts, successfully generated {successful} thumbnails")


if __name__ == "__main__":
    main()
