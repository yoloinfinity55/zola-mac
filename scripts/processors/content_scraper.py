"""
Content Scraper Module
Handles web scraping, HTML parsing, and content extraction.
"""

import re
import time
import logging
from typing import Tuple, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def slugify(url_or_title: str) -> str:
    """Create URL-friendly slug for Zola"""
    if "://" in url_or_title:
        path = urlparse(url_or_title).path.strip("/").replace("/", "-")
        return re.sub(r"[^a-zA-Z0-9_-]", "", path) or "web-content"
    else:
        slug = url_or_title.lower().replace(" ", "-")
        return re.sub(r"[^a-z0-9_-]", "", slug)


def fetch_content(url: str, max_retries: int = 10, backoff_factor: float = 2) -> Tuple[str, List[Tuple[str, str]], str, str]:
    """
    Fetch and extract content from a web URL.

    Args:
        url: The URL to scrape
        max_retries: Maximum number of retry attempts
        backoff_factor: Exponential backoff multiplier

    Returns:
        Tuple of (text_content, headings_list, title, publication_date)
    """
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
                        from datetime import datetime
                        dt = datetime.fromisoformat(str(content).replace('Z', '+00:00'))
                        pub_date = dt.strftime('%Y-%m-%d')
                    except Exception as e:
                        logger.warning(f"Could not parse publication date: {e}. Falling back to current date.")
                        pass
            if not pub_date:
                # Fallback to current date
                from datetime import datetime
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
                logger.warning(".1f")
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
                logger.warning(".1f")
                time.sleep(wait_time)
            else:
                raise
    raise Exception(f"Failed to fetch content after {max_retries} attempts")


def extract_text_from_html(html_content: str) -> str:
    """
    Extract readable text from HTML content.

    Args:
        html_content: Raw HTML string

    Returns:
        Extracted text content
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.extract()

    # Get text
    text = soup.get_text()

    # Break into lines and remove leading/trailing space
    lines = (line.strip() for line in text.splitlines())
    # Break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # Drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)

    return text


def get_content_paths(slug: str) -> dict:
    """
    Get file paths for a blog post directory.

    Args:
        slug: URL slug for the post

    Returns:
        Dictionary with paths for different file types
    """
    from pathlib import Path
    BASE_CONTENT = Path("content/blog")
    folder = BASE_CONTENT / slug
    folder.mkdir(parents=True, exist_ok=True)
    return {
        "md": folder / "index.md",
        "mp3": folder / "asset.mp3",
        "txt": folder / "asset.txt",
        "json": folder / "asset.json"
    }


def get_page_metadata(url: str) -> dict:
    """
    Extract metadata from a web page.

    Args:
        url: The URL to analyze

    Returns:
        Dictionary containing page metadata
    """
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        metadata = {
            'url': url,
            'title': None,
            'description': None,
            'author': None,
            'published_date': None,
            'modified_date': None,
            'tags': []
        }

        # Title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text(strip=True)

        # Meta description
        desc_meta = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
        if desc_meta:
            metadata['description'] = desc_meta.get('content')

        # Author
        author_meta = soup.find('meta', attrs={'name': 'author'}) or soup.find('meta', attrs={'property': 'article:author'})
        if author_meta:
            metadata['author'] = author_meta.get('content')

        # Published date
        pub_meta = soup.find('meta', attrs={'property': 'article:published_time'})
        if pub_meta:
            metadata['published_date'] = pub_meta.get('content')

        # Modified date
        mod_meta = soup.find('meta', attrs={'property': 'article:modified_time'})
        if mod_meta:
            metadata['modified_date'] = mod_meta.get('content')

        return metadata

    except Exception as e:
        logger.error(f"Error extracting metadata from {url}: {e}")
        return {'url': url, 'error': str(e)}
