"""
Image Processor Module
Handles thumbnail generation, image processing, and visual asset creation.
"""

import logging
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import requests
from PIL import Image
import io

logger = logging.getLogger(__name__)


def generate_image_keywords_with_ai(text: str, title: str, post_slug: str, groq_api_key: Optional[str] = None) -> str:
    """
    Use AI to analyze blog content and generate relevant image search keywords.

    Args:
        text: Blog post content
        title: Blog post title
        post_slug: URL slug for the post
        groq_api_key: Groq API key for AI processing

    Returns:
        Comma-separated keywords for image search
    """
    if not groq_api_key:
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
        headers = {"Authorization": f"Bearer {groq_api_key}", "Content-Type": "application/json"}
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


def search_unsplash_image(keywords: str, title: str, unsplash_key: Optional[str] = None) -> str:
    """
    Search for a free image on Unsplash based on keywords.

    Args:
        keywords: Comma-separated search keywords
        title: Blog post title for fallback
        unsplash_key: Unsplash API access key

    Returns:
        URL of the selected image
    """
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
        if unsplash_key and unsplash_key.strip():
            headers['Authorization'] = f'Client-ID {unsplash_key}'

        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('results') and len(data['results']) > 0:
                    # Pick a random image from results
                    import random
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


def download_and_process_image(image_url: str, filepath: Path, crop_to_16_9: bool = True) -> bool:
    """
    Download image from URL and optionally crop to 16:9 aspect ratio.

    Args:
        image_url: URL of the image to download
        filepath: Local file path to save the image
        crop_to_16_9: Whether to crop image to 16:9 aspect ratio

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"📥 Downloading and processing image to {filepath}")

    try:
        resp = requests.get(image_url, timeout=15)
        resp.raise_for_status()

        # Open image with PIL
        image = Image.open(io.BytesIO(resp.content))

        if crop_to_16_9:
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
        else:
            # Save as-is
            image.save(filepath, "JPEG", quality=85)

        logger.info("✅ Image downloaded and processed successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Image download/processing failed: {e}")
        return False


def download_youtube_thumbnail(thumbnail_url: str, filepath: Path) -> bool:
    """
    Download YouTube video thumbnail from URL.

    Args:
        thumbnail_url: YouTube thumbnail URL
        filepath: Local file path to save the thumbnail

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"📥 Downloading YouTube thumbnail: {thumbnail_url}")

    try:
        resp = requests.get(thumbnail_url, timeout=15)
        resp.raise_for_status()

        # Save the image directly (YouTube thumbnails are already optimized)
        with open(filepath, 'wb') as f:
            f.write(resp.content)

        logger.info(f"✅ YouTube thumbnail downloaded: {filepath}")
        return True
    except Exception as e:
        logger.error(f"❌ YouTube thumbnail download failed: {e}")
        return False


def generate_blog_thumbnail(text: str, title: str, post_dir: Path, slug: str, groq_api_key: Optional[str] = None, unsplash_key: Optional[str] = None) -> bool:
    """
    Generate a thumbnail image for a blog post using AI analysis and free images.

    Args:
        text: Blog post content
        title: Blog post title
        post_dir: Directory to save the thumbnail
        slug: Post slug for content analysis
        groq_api_key: Groq API key for AI processing
        unsplash_key: Unsplash API key

    Returns:
        True if thumbnail was generated successfully
    """
    thumb_path = post_dir / "asset.jpg"

    # Skip if thumbnail already exists
    if thumb_path.exists():
        logger.info("Thumbnail already exists, skipping generation")
        return True

    try:
        # Generate keywords using AI
        keywords = generate_image_keywords_with_ai(text, title, slug, groq_api_key)

        # Search for image
        image_url = search_unsplash_image(keywords, title, unsplash_key)

        # Download and process image
        success = download_and_process_image(image_url, thumb_path)

        if success:
            logger.info(f"✅ Thumbnail generated: {thumb_path}")
        return success

    except Exception as e:
        logger.error(f"Thumbnail generation failed: {e}")
        return False


def validate_image_file(image_file: Path) -> bool:
    """
    Validate that an image file exists and is not corrupted.

    Args:
        image_file: Path to image file

    Returns:
        True if file is valid, False otherwise
    """
    if not image_file.exists():
        logger.error(f"Image file does not exist: {image_file}")
        return False

    try:
        # Try to open with PIL to verify it's a valid image
        with Image.open(image_file) as img:
            img.verify()  # Verify the image is not corrupted
        return True
    except Exception as e:
        logger.error(f"Image file validation failed for {image_file}: {e}")
        return False


def get_image_dimensions(image_file: Path) -> Optional[tuple]:
    """
    Get the dimensions of an image file.

    Args:
        image_file: Path to image file

    Returns:
        Tuple of (width, height) or None if error
    """
    try:
        with Image.open(image_file) as img:
            return img.size
    except Exception as e:
        logger.error(f"Could not get dimensions for {image_file}: {e}")
        return None


def optimize_image(image_file: Path, max_width: int = 1200, quality: int = 85) -> bool:
    """
    Optimize an image by resizing and compressing.

    Args:
        image_file: Path to image file
        max_width: Maximum width to resize to
        quality: JPEG quality (1-100)

    Returns:
        True if optimization was successful
    """
    try:
        with Image.open(image_file) as img:
            # Only resize if image is larger than max_width
            if img.width > max_width:
                # Calculate new height maintaining aspect ratio
                aspect_ratio = img.height / img.width
                new_height = int(max_width * aspect_ratio)

                # Resize image
                resized_img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

                # Save optimized image
                resized_img.save(image_file, "JPEG", quality=quality, optimize=True)
                logger.info(f"Optimized image {image_file} to {max_width}x{new_height}")
            else:
                # Just recompress if not resizing
                img.save(image_file, "JPEG", quality=quality, optimize=True)
                logger.info(f"Recompressed image {image_file}")

        return True
    except Exception as e:
        logger.error(f"Image optimization failed for {image_file}: {e}")
        return False
