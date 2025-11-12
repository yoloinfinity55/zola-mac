# Zola-Mac Manual Guide: Rebuilding the Project

## Introduction
This manual provides step-by-step instructions for rebuilding the Zola-Mac project from scratch. Zola-Mac is an automated blogging platform that converts web content and YouTube videos into multimedia blog posts with AI-generated audio narration.

## Prerequisites
- Python 3.8 or higher
- Git
- FFmpeg (for audio processing)
- Internet connection
- API keys for AI services

## Step 1: Project Initialization

### 1.1 Create Project Directory
```bash
mkdir zola-mac-blog
cd zola-mac-blog
```

### 1.2 Initialize Git Repository
```bash
git init
echo "# Zola-Mac Blog" > README.md
echo "*.mp3" > .gitignore
echo "*.mp4" > .gitignore
echo ".env" >> .gitignore
echo "audio_output/" >> .gitignore
echo "public/" >> .gitignore
```

### 1.3 Set Up Python Environment
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install --upgrade pip
```

## Step 2: Install Core Dependencies

### 2.1 Create requirements.txt
```txt
# Core dependencies for Zola-mac content automation

requests>=2.31.0
yt-dlp>=2023.0.0
python-slugify>=8.0.0
python-dotenv>=1.0.0
readability-lxml>=0.8.1
toml>=0.10.0
Pillow>=10.0.0

# Text-to-Speech (Edge-TTS)
edge-tts==7.0.0
langdetect>=1.0.9
tqdm>=4.67.1
pydub>=0.25.1

# Optional legacy fallback
# pyttsx3>=2.90  # Commented out — replaced by neural Edge-TTS

# FFmpeg required (not pip-installable)
# macOS: brew install ffmpeg
# Linux: sudo apt install ffmpeg
```

### 2.2 Install Python Packages
```bash
pip install -r requirements.txt
```

### 2.3 Install System Dependencies
```bash
# macOS
brew install ffmpeg zola

# Linux Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg
# Install Zola: https://www.getzola.org/documentation/getting-started/installation/

# Windows
# Install FFmpeg: https://ffmpeg.org/download.html
# Install Zola: https://www.getzola.org/documentation/getting-started/installation/
```

## Step 3: Configure Zola Site

### 3.1 Initialize Zola Site
```bash
zola init .
# Answer prompts or use defaults
```

### 3.2 Configure config.toml
```toml
base_url = "https://yourusername.github.io/zola-mac"
title = "Zola-mac"
description = "A blog about building beautiful static sites with Zola on macOS."
compile_sass = false
build_search_index = false
ignored_content = ["blog/archive/*.md"]

taxonomies = [
    { name = "tags", feed = true }
]

[markdown]
highlight_code = true
```

### 3.3 Create Directory Structure
```bash
mkdir -p content/blog
mkdir -p templates
mkdir -p static/css
mkdir -p static/js
mkdir -p scripts
mkdir -p audio_output
```

## Step 4: Build Templates

### 4.1 Create Base Template (templates/base.html)
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>{% if page.title %}Zola-mac | {{ page.title }}{% else %}Zola-mac{% endif %}</title>
    <meta name="description" content="A blog about building beautiful static sites with Zola on macOS.">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{{ get_url(path='css/style.css') }}">
  </head>

  <body class="{% block body_class %}{% endblock %}">
    <header>
      <h1><a href="{{ get_url(path="/") }}">Zola-mac</a></h1>
      <nav>
        <a href="{{ get_url(path="/") }}">Home</a>
        <a href="{{ get_url(path="blog") }}">Blog</a>
      </nav>
    </header>

    <main class="container">
      <div class="post-content">
        {% block content %}
        {% endblock content %}
      </div>
    </main>

    <footer>
      <div class="social-links">
        <a href="#" target="_blank">GitHub</a>
        <a href="#" target="_blank">Twitter</a>
        <a href="#" target="_blank">LinkedIn</a>
      </div>
      <p>© 2025 Zola-mac. Built with ❤️ using Zola.</p>
    </footer>

    <button id="back-to-top" title="Go to top">↑</button>

    <script>
      // Back to Top Button
      const backToTopButton = document.getElementById("back-to-top");

      window.onscroll = function() {
        if (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100) {
          backToTopButton.style.display = "block";
        } else {
          backToTopButton.style.display = "none";
        }
      };

      backToTopButton.onclick = function() {
        document.body.scrollTop = 0;
        document.documentElement.scrollTop = 0;
      };
    </script>
  </body>
</html>
```

### 4.2 Create Blog Template (templates/blog.html)
```html
{% extends "base.html" %}

{% block body_class %}blog{% endblock %}

{% block content %}
<div class="blog-header">
  <h1>{{ section.title }}</h1>
  <p>Exploring static site generation with Zola</p>
</div>

<div class="blog-posts">
  {% if paginator %}
    <div class="blog-posts-grid">
      {% for page in paginator.pages %}
        <article class="blog-post-card">
          {% if page.path is starting_with("/blog/") %}
            <div class="blog-post-image">
              <img src="{{ page.path }}/asset.jpg" alt="{{ page.title }}" loading="lazy">
            </div>
          {% endif %}
          <div class="post-card-header">
            <h2 class="post-card-title">
              <a href="{{ page.permalink }}">{{ page.title }}</a>
            </h2>
            <p class="post-meta">{{ page.date | date(format="%B %e, %Y") }}</p>
          </div>
          {% if page.summary %}
            <p class="post-card-summary">{{ page.summary | safe }}</p>
          {% endif %}
          <a href="{{ page.permalink }}" class="read-more">
            Read more <span>→</span>
          </a>
        </article>
      {% endfor %}
    </div>

    <nav class="pagination-nav">
      {% if paginator.previous %}
        <a href="{{ paginator.previous }}" class="pagination-btn prev-btn">
          <span>←</span> Newer posts
        </a>
      {% else %}
        <span class="pagination-placeholder"></span>
      {% endif %}
      {% if paginator.next %}
        <a href="{{ paginator.next }}" class="pagination-btn next-btn">
          Older posts <span>→</span>
        </a>
      {% endif %}
    </nav>
  {% else %}
    <!-- Fallback for non-paginated view -->
    <div class="blog-posts-grid">
      {% for page in section.pages %}
        <article class="blog-post-card">
          {% if page.path is starting_with("/blog/") %}
            <div class="blog-post-image">
              <img src="{{ page.path }}/asset.jpg" alt="{{ page.title }}" loading="lazy">
            </div>
          {% endif %}
          <div class="post-card-header">
            <h2 class="post-card-title">
              <a href="{{ page.permalink }}">{{ page.title }}</a>
            </h2>
            <p class="post-meta">{{ page.date | date(format="%B %e, %Y") }}</p>
          </div>
          {% if page.summary %}
            <p class="post-card-summary">{{ page.summary | safe }}</p>
          {% endif %}
          <a href="{{ page.permalink }}" class="read-more">
            Read more <span>→</span>
          </a>
        </article>
      {% endfor %}
    </div>
  {% endif %}
</div>
{% endblock content %}
```

### 4.3 Create Index Template (templates/index.html)
```html
{% extends "base.html" %}

{% block body_class %}home{% endblock %}

{% block content %}
<div class="hero">
  <h1>Welcome to Zola-Mac</h1>
  <p>Automated content creation with AI-powered audio narration</p>
</div>

<section class="home-posts-section">
  <h2 class="section-heading">Latest Posts</h2>

  <div class="posts-grid">
    {% for page in section.pages | slice(end=6) %}
      <article class="post-card">
        {% if page.path is starting_with("/blog/") %}
          <div class="post-card-image">
            <img src="{{ page.path }}/asset.jpg" alt="{{ page.title }}" loading="lazy">
          </div>
        {% endif %}
        <div class="post-card-content">
          <h3 class="post-card-title">
            <a href="{{ page.permalink }}">{{ page.title }}</a>
          </h3>
          <p class="post-card-meta">{{ page.date | date(format="%B %e, %Y") }}</p>
          {% if page.summary %}
            <p class="post-card-excerpt">{{ page.summary | safe }}</p>
          {% endif %}
        </div>
        <div class="post-card-footer">
          <a href="{{ page.permalink }}" class="read-more-link">
            Read more <span>→</span>
          </a>
        </div>
      </article>
    {% endfor %}
  </div>

  <div class="view-all">
    <a href="{{ get_url(path='blog') }}" class="view-all-btn">
      View All Posts <span>→</span>
    </a>
  </div>
</section>
{% endblock content %}
```

## Step 5: Create CSS Styling

### 5.1 Create Main Stylesheet (static/css/style.css)
```css
/* ===== CSS Variables ===== */
:root {
  --blue: #007bff;
  --gray: #f9f9f9;
  --dark: #1a1a1a;
  --light-gray: #f8f9fa;
  --accent: #2563eb;
  --accent-hover: #1d4ed8;
  --accent-light: #dbeafe;
  --muted: #64748b;
  --border: #e2e8f0;
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
  --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.08);
  --shadow-xl: 0 20px 40px rgba(0, 0, 0, 0.1);
}

* {
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  margin: 0;
  padding: 0;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  color: var(--dark);
  line-height: 1.7;
  font-size: 16px;
}

/* ===== Fixed Navbar ===== */
header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  color: var(--dark);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.2rem 3rem;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.06);
  border-bottom: 1px solid var(--border);
}

header h1 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

header h1 a {
  color: var(--dark);
  text-decoration: none;
  background: linear-gradient(135deg, var(--accent) 0%, #1d4ed8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  transition: opacity 0.3s ease;
}

header h1 a:hover {
  opacity: 0.8;
}

nav {
  display: flex;
  gap: 2.5rem;
}

nav a {
  color: var(--dark);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  position: relative;
  padding: 0.5rem 0;
}

nav a::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--accent), var(--accent-hover));
  transition: width 0.3s ease;
}

nav a:hover {
  color: var(--accent);
}

nav a:hover::after {
  width: 100%;
}

/* ===== Main Content ===== */
main.container {
  max-width: 850px;
  margin: 9rem auto 3rem auto;
  padding: 3rem;
  background: #fff;
  border-radius: 16px;
  box-shadow: var(--shadow-xl);
  border: 1px solid var(--border);
}

body.blog main.container {
  max-width: none;
  width: 100%;
  padding: 3rem 1rem;
  margin: 9rem 0 3rem 0;
}

body.home main.container {
  max-width: none;
  width: 100%;
  padding: 3rem 1rem;
  margin: 9rem 0 3rem 0;
}

/* ===== Blog Posts Grid ===== */
.blog-posts-grid, .posts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 2.5rem;
  margin-bottom: 3rem;
  padding: 0 1rem;
}

.blog-post-card, .post-card {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.95) 100%);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  border: 1px solid rgba(226, 232, 240, 0.8);
  padding: 2.5rem;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.blog-post-card:hover, .post-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-lg);
  border-color: var(--accent-light);
}

/* ===== Responsive Design ===== */
@media (max-width: 599px) {
  header {
    flex-direction: column;
    text-align: center;
    padding: 1rem 1.5rem;
  }

  nav {
    margin-top: 1rem;
    gap: 1.2rem;
  }

  main.container {
    margin: 7rem 1rem 2rem 1rem;
    padding: 1.5rem;
  }

  .blog-posts-grid, .posts-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .blog-post-card, .post-card {
    padding: 1.5rem;
  }
}

/* ===== Hero Section ===== */
.hero {
  text-align: center;
  padding: 2rem 1rem;
  margin-bottom: 3rem;
}

.hero h1 {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
  background: linear-gradient(135deg, var(--accent) 0%, #1d4ed8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.03em;
}

.hero p {
  font-size: 1.2rem;
  color: var(--muted);
  margin-bottom: 2rem;
}

/* ===== Footer ===== */
footer {
  text-align: center;
  padding: 3rem 2rem;
  color: var(--muted);
  font-size: 0.9rem;
  margin-top: 4rem;
}

.social-links {
  margin-bottom: 1.5rem;
}

.social-links a {
  margin: 0 0.8rem;
  color: var(--muted);
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s ease;
  padding: 0.5rem 1rem;
  border-radius: 8px;
}

.social-links a:hover {
  color: var(--accent);
  background: var(--accent-light);
}

footer p {
  margin: 0;
  color: var(--muted);
}

/* ===== Back to Top Button ===== */
#back-to-top {
  position: fixed;
  bottom: 30px;
  right: 30px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-hover) 100%);
  color: #fff;
  border: none;
  border-radius: 50%;
  width: 56px;
  height: 56px;
  font-size: 24px;
  cursor: pointer;
  display: none;
  box-shadow: var(--shadow-lg);
  transition: all 0.3s ease;
  z-index: 999;
}

#back-to-top:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-xl);
}
```

## Step 6: Build Core Automation Scripts

### 6.1 Create Web to Audio Script (scripts/web_to_audio_zola.py)
```python
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

            title = soup.find('title').get_text(strip=True) if soup.find('title') else "Web Audio Content"
            h1_tag = soup.find('h1')
            if h1_tag and not title:
                title = h1_tag.get_text(strip=True)

            pub_date = datetime.now().strftime('%Y-%m-%d')

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
        except Exception as e:
            logger.error(f"Error fetching content: {e}")
            if attempt < max_retries - 1:
                time.sleep(backoff_factor ** attempt)
            else:
                raise

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

    prompt = f"""
    Analyze this blog post and generate UNIQUE, SPECIFIC keywords for stock image search.
    Focus on the most distinctive visual elements and themes.

    TITLE: {title}
    SLUG: {post_slug}

    CONTENT SAMPLE:
    {text[:1200]}

    Generate 4-6 UNIQUE keywords that would help find a distinctive stock image.
    Be specific and avoid generic terms like "technology" or "computer" unless they're central.

    Return ONLY the keywords separated by commas, no other text.
    """

    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
            "max_tokens": 120
        }

        resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        keywords = resp.json()["choices"][0]["message"]["content"].strip()

        keywords = keywords.strip('",.').replace('"', '').replace("'", "")
        if len(keywords.split(',')) < 3:
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

    search_term = keywords.split(',')[0].strip() if keywords != "technology blog article" else title.split()[0]

    search_terms = [search_term]
    if len(title.split()) > 1:
        search_terms.append(title.split()[1])
    search_terms.extend(['technology', 'digital', 'computer', 'abstract'])

    for term in search_terms[:3]:
        url = f"https://api.unsplash.com/search/photos?query={quote(term)}&per_page=20&orientation=landscape"

        headers = {'Accept-Version': 'v1'}
        unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY")
        if unsplash_key and unsplash_key.strip():
            headers['Authorization'] = f'Client-ID {unsplash_key}'

        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('results') and len(data['results']) > 0:
                    image_data = random.choice(data['results'])
                    image_url = image_data['urls']['regular']
                    logger.info(f"✅ Found Unsplash image for '{term}': {image_url}")
                    return image_url
        except Exception as e:
            logger.error(f"Unsplash search failed for term '{term}': {e}")

    fallback_urls = [
        "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800&h=450&fit=crop",
        "https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=800&h=450&fit=crop",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&h=450&fit=crop"
    ]

    fallback_url = fallback_urls[hash(keywords + title) % len(fallback_urls)]
    logger.info(f"Using fallback image: {fallback_url}")
    return fallback_url

def download_and_process_image(image_url: str, filepath: str) -> bool:
    """Download image from URL and crop to 16:9 aspect ratio"""
    logger.info(f"📥 Downloading and processing image to {filepath}")

    try:
        resp = requests.get(image_url, timeout=15)
        resp.raise_for_status()

        image = Image.open(io.BytesIO(resp.content))

        width, height = image.size
        target_ratio = 16 / 9
        current_ratio = width / height

        if current_ratio > target_ratio:
            new_width = int(height * target_ratio)
            left = (width - new_width) // 2
            right = left + new_width
            top, bottom = 0, height
        else:
            new_height = int(width / target_ratio)
            top = (height - new_height) // 2
            bottom = top + new_height
            left, right = 0, width

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

    if thumb_path.exists():
        logger.info("Thumbnail already exists, skipping generation")
        return True

    try:
        keywords = generate_image_keywords_with_ai(text, title, slug)
        image_url = search_unsplash_image(keywords, title)
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

    with open(paths["txt"], "w", encoding="utf-8") as f:
        f.write(text)
    logger.info(f"Text saved: {paths['txt']}")

    generate_blog_thumbnail(text, title, post_dir, slug)

    save_zola_markdown_with_headings(text, headings, title, pub_date, paths["md"])

    chunks = split_text_into_chunks(summary)
    temp_mp3s = await text_to_speech_chunks(chunks, TEMP_FOLDER)
    combine_mp3(temp_mp3s, paths["mp3"])
    logger.info(f"Audio saved: {paths['mp3']}")

    metadata = {"url": url, "chunks": len(chunks), "mp3": str(paths["mp3"]), "text": str(paths["txt"]), "slug": slug, "title": title, "pub_date": pub_date}
    with open(paths["json"], "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata saved: {paths['json']}")

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
```

### 6.2 Create Environment Configuration
```bash
# Create .env file
echo "# API Keys for Zola-Mac" > .env
echo "GROQ_API_KEY=your_groq_api_key_here" >> .env
echo "UNSPLASH_ACCESS_KEY=your_unsplash_key_here" >> .env
```

## Step 7: Create Content Structure

### 7.1 Create Blog Index
```bash
# Create content/blog/_index.md
mkdir -p content/blog
cat > content/blog/_index.md << 'EOF'
+++
title = "Blog"
sort_by = "date"
template = "blog.html"
page_template = "page.html"
+++

# Blog Posts

Welcome to my blog where I explore automated content creation with AI and static site generation.
EOF
```

### 7.2 Create Homepage Content
```bash
# Create content/_index.md
cat > content/_index.md << 'EOF'
+++
title = "Home"
template = "index.html"
+++

# Welcome to Zola-Mac

An automated blogging platform that transforms web content into multimedia posts with AI-generated audio narration.

## Features

- **Automated Content Creation**: Convert web articles to blog posts instantly
- **AI-Powered Audio**: Neural text-to-speech narration for all content
- **Smart Thumbnails**: AI-generated relevant images for each post
- **Modern Design**: Responsive static site with beautiful aesthetics
- **Zola-Powered**: Fast, secure static site generation

## Getting Started

Choose a web article URL and run:

```bash
python scripts/web_to_audio_zola.py "https://example.com/article"
```

The system will automatically:
1. Extract and process the content
2. Generate AI narration audio
3. Create a relevant thumbnail
4. Build a complete blog post
5. Update the site

[View Blog Posts →](blog)
EOF
```

## Step 8: Test the System

### 8.1 Build the Site
```bash
# Build Zola site
zola build

# Check for errors
zola check
```

### 8.2 Test Content Generation
```bash
# Test with a sample URL
python scripts/web_to_audio_zola.py "https://example.com/sample-article"

# Rebuild site
zola build
```

### 8.3 Serve Locally
```bash
# Start development server
zola serve

# Visit http://localhost:1111
```

## Step 9: Deployment Setup

### 9.1 GitHub Pages Deployment
```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial Zola-Mac setup"

# Create GitHub repository
# Then push to GitHub
git remote add origin https://github.com/yourusername/zola-mac.git
git push -u origin main
```

### 9.2 GitHub Actions (Optional)
Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy Zola site to Pages

on:
  push:
    branches:
      - main

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      - name: Install Zola
        run: |
          wget https://github.com/getzola/zola/releases/download/v0.17.2/zola-v0.17.2-x86_64-unknown-linux-gnu.tar.gz
          tar -xzf zola-v0.17.2-x86_64-unknown-linux-gnu.tar.gz
          sudo mv zola /usr/local/bin/
      - name: Build site
        run: zola build
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./public
```

## Step 10: Customization and Extensions

### 10.1 Add More Templates
- Create `templates/page.html` for individual post pages
- Add `templates/taxonomy_list.html` for tag/category pages
- Customize templates for different content types

### 10.2 Extend Scripts
- Add YouTube processing capabilities
- Implement social media posting
- Create content scheduling features

### 10.3 Add Features
- Search functionality
- Comments system
- Analytics integration
- RSS feed generation

## Troubleshooting

### Common Issues
1. **FFmpeg not found**: Install FFmpeg system-wide
2. **API key errors**: Verify `.env` file and API keys
3. **Zola build fails**: Check template syntax and content structure
4. **Audio generation fails**: Check internet connection and Edge TTS availability

### Getting Help
- Check script logs for detailed error messages
- Verify all dependencies are installed
- Test with simple URLs first
- Ensure proper file permissions

## Next Steps
1. Generate your first content using the automation scripts
2. Customize the design and templates to match your brand
3. Set up automated deployment
4. Add more content sources and processing features
5. Integrate analytics and monitoring

Congratulations! You now have a fully functional automated blogging platform with AI-powered content creation capabilities.
