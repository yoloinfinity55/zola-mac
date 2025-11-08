import asyncio
import json
import os
import re
import subprocess
import time
import random

from pathlib import Path
from urllib.parse import urlparse, quote

from datetime import datetime
import logging

import edge_tts
import requests
from bs4 import BeautifulSoup
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

# TEMP folder for intermediate mp3 chunks
TEMP_FOLDER = Path("audio_output/tmp")
TEMP_FOLDER.mkdir(parents=True, exist_ok=True)

BASE_CONTENT = Path("content/blog")
BASE_CONTENT.mkdir(parents=True, exist_ok=True)

OUTPUT_FOLDER = Path("audio_output")
OUTPUT_FOLDER.mkdir(exist_ok=True)


def slugify(url_or_title: str) -> str:
    """Create URL-friendly slug for Zola"""
    if "://" in url_or_title:
        path = urlparse(url_or_title).path.strip("/").replace("/", "-")
        return re.sub(r"[^a-zA-Z0-9_-]", "", path) or "web-content"
    else:
        slug = url_or_title.lower().replace(" ", "-")
        return re.sub(r"[^a-z0-9_-]", "", slug)


def get_content_paths(slug: str):
    folder = BASE_CONTENT / slug
    folder.mkdir(parents=True, exist_ok=True)
    return {
        "md": folder / "index.md",
        "mp3": folder / "asset.mp3",
        "txt": folder / "asset.txt",
        "json": folder / "asset.json"
    }


def fetch_content(url: str, max_retries=10, backoff_factor=2):
    logger.info(f"Fetching content from: {url}")

    # Use a session with browser-like headers to avoid rate limiting
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })

    for attempt in range(max_retries):
        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Extract title
            title = None
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)
            h1_tag = soup.find('h1')
            if h1_tag and not title:
                title = h1_tag.get_text(strip=True)
            if not title:
                title = "Web Audio Content"

            # Extract publication date
            pub_date = None
            meta_pub = soup.find('meta', property='article:published_time')
            if meta_pub:
                content = meta_pub.get('content')
                if content:
                    try:
                        # Ensure it's a string
                        if isinstance(content, list):
                            content = content[0] if content else ''
                        # Parse ISO date
                        dt = datetime.fromisoformat(str(content).replace('Z', '+00:00'))
                        pub_date = dt.strftime('%Y-%m-%d')
                    except Exception as e:
                        logger.warning(f"Could not parse publication date: {e}. Falling back to current date.")
                        pass
            if not pub_date:
                # Fallback to current date
                pub_date = datetime.now().strftime('%Y-%m-%d')

            # Extract visible text
            texts = []
            headings = []
            for el in soup.find_all(["h1", "h2", "h3", "p", "li"]):
                t = el.get_text(strip=True)
                if t:
                    texts.append(t)
                if el.name in ["h1", "h2", "h3"]:
                    headings.append((el.name, t))
            text = "\n".join(texts)
            return text, headings, title, pub_date
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                # Add jitter to avoid thundering herd
                import random
                jitter = random.uniform(0.5, 1.5)
                wait_time = (backoff_factor ** attempt) * jitter
                logger.warning(f"Rate limited (429). Retrying in {wait_time:.1f} seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                logger.error(f"HTTP Error fetching content (status {e.response.status_code}): {e}")
                raise
        except Exception as e:
            logger.error(f"Error fetching content: {e}")
            if attempt < max_retries - 1:
                import random
                jitter = random.uniform(0.5, 1.5)
                wait_time = (backoff_factor ** attempt) * jitter
                logger.warning(f"Retrying in {wait_time:.1f} seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                raise
    raise Exception(f"Failed to fetch content after {max_retries} attempts")


def summarize_text_with_groq(text: str):
    """Summarize text using GROQ API"""
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set. Skipping GROQ summarization.")
        return text
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        data = {"text": text, "summary_ratio": 0.2}
        resp = requests.post("https://api.groq.ai/v1/summarize", headers=headers, json=data)
        resp.raise_for_status()
        summary = resp.json().get("summary")
        return summary or text
    except Exception as e:
        logger.error(f"GROQ summarization failed: {e}. Using original text as summary.")
        return text


def split_text_into_chunks(text: str, max_words=250):
    """Split text into chunks for TTS"""
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i:i + max_words])
        chunks.append(chunk)
    return chunks


async def text_to_speech_chunks(chunks, temp_folder):
    mp3_files = []
    for idx, chunk in enumerate(chunks):
        mp3_path = temp_folder / f"part_{idx+1:03}.mp3"
        mp3_files.append(mp3_path)
        logger.info(f"Converting chunk {idx+1}/{len(chunks)} to speech...")
        communicate = edge_tts.Communicate(chunk, "en-US-AriaNeural")
        await communicate.save(str(mp3_path))
    return mp3_files


def combine_mp3(mp3_files, output_file):
    """Combine mp3 chunks with ffmpeg"""
    concat_list = TEMP_FOLDER / "concat_list.txt"
    with open(concat_list, "w") as f:
        for mp3 in mp3_files:
            f.write(f"file '{mp3.resolve()}'\n")
    subprocess.run(
        ["ffmpeg", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(output_file)],
        check=True
    )


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


def generate_blog_thumbnail(text: str, title: str, post_dir: Path, slug: str) -> bool:
    """Generate a thumbnail image for a blog post using AI analysis and free images"""
    thumb_path = post_dir / "asset.jpg"

    # Skip if thumbnail already exists
    if thumb_path.exists():
        logger.info("Thumbnail already exists, skipping generation")
        return True

    try:
        # Generate keywords using AI
        keywords = generate_image_keywords_with_ai(text, title, slug)

        # Search for image
        image_url = search_unsplash_image(keywords, title)

        # Download and process image
        success = download_and_process_image(image_url, str(thumb_path))

        if success:
            logger.info(f"✅ Thumbnail generated: {thumb_path}")
        return success

    except Exception as e:
        logger.error(f"Thumbnail generation failed: {e}")
        return False


def save_zola_markdown_with_headings(text, headings, title, pub_date, md_path):
    """Save text into Zola Markdown"""
    front_matter = "+++\n"
    front_matter += f'title = "{title}"\n'
    front_matter += f'date = "{pub_date}"\n'
    front_matter += "+++\n\n"

    md_content = front_matter
    for tag, heading in headings:
        level = int(tag[1])
        md_content += f"{'#'*level} {heading}\n\n"
    md_content += text

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    logger.info(f"Zola post saved: {md_path}")


async def process_url(url: str):
    slug = slugify(url)
    paths = get_content_paths(slug)
    post_dir = BASE_CONTENT / slug

    text, headings, title, pub_date = fetch_content(url)
    summary = summarize_text_with_groq(text)

    # Save text
    with open(paths["txt"], "w", encoding="utf-8") as f:
        f.write(text)
    logger.info(f"Text saved: {paths['txt']}")

    # Generate thumbnail using AI analysis
    generate_blog_thumbnail(text, title, post_dir, slug)

    # Zola Markdown (save early in case TTS fails)
    save_zola_markdown_with_headings(text, headings, title, pub_date, paths["md"])

    # TTS
    chunks = split_text_into_chunks(summary)
    temp_mp3s = await text_to_speech_chunks(chunks, TEMP_FOLDER)
    combine_mp3(temp_mp3s, paths["mp3"])
    logger.info(f"Audio saved: {paths['mp3']}")

    # Metadata
    metadata = {"url": url, "chunks": len(chunks), "mp3": str(paths["mp3"]), "text": str(paths["txt"]), "slug": slug, "title": title, "pub_date": pub_date}
    with open(paths["json"], "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata saved: {paths['json']}")

    # Cleanup
    for mp3 in temp_mp3s:
        mp3.unlink()
    concat_file = TEMP_FOLDER / "concat_list.txt"
    if concat_file.exists():
        concat_file.unlink()
    try:
        TEMP_FOLDER.rmdir()
    except OSError:
        logger.warning(f"Could not remove temporary directory {TEMP_FOLDER}: It might not be empty.")


def main():
    import sys
    import subprocess
    import time

    if len(sys.argv) < 2:
        logger.error("Usage: python web_to_audio_zola.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    try:
        asyncio.run(process_url(url))
    except Exception as e:
        logger.exception(f"An unexpected error occurred during URL processing: {e}")

if __name__ == "__main__":
    main()
