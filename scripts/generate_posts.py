#!/usr/bin/env python3
"""
generate_posts.py
-----------------------------------
Automated blog post generator for Zola.
- Fetches YouTube metadata and transcript
- Creates Markdown post with thumbnail, embed, keypoints, and AI-written narrative (via Groq)
"""

import os
import sys
import argparse
import requests
from datetime import datetime
from slugify import slugify
from yt_dlp import YoutubeDL
import textwrap

# -----------------------------
# CONFIGURATION
# -----------------------------
CONTENT_DIR = "content/blog"
THUMBNAIL_DIR = "static/blog"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-8b-8192"


# -----------------------------
# FETCH YOUTUBE METADATA
# -----------------------------
def fetch_youtube_info(url):
    print(f"Fetching YouTube info for: {url}")
    ydl_opts = {"quiet": True, "skip_download": True, "writesubtitles": False}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return {
        "title": info.get("title", "Untitled Video"),
        "description": info.get("description", ""),
        "upload_date": info.get("upload_date"),
        "duration": info.get("duration"),
        "thumbnail": info.get("thumbnail"),
        "id": info.get("id"),
        "uploader": info.get("uploader"),
        "webpage_url": info.get("webpage_url"),
    }


# -----------------------------
# FETCH TRANSCRIPT
# -----------------------------
def fetch_transcript(video_id):
    print("Fetching transcript...")
    try:
        resp = requests.get(f"https://youtubetranscript.com/?server_vid2={video_id}", timeout=10)
        if resp.ok and "text" in resp.text:
            return resp.text
    except Exception as e:
        print(f"⚠️ Transcript fetch failed: {e}")
    return "Transcript unavailable."


# -----------------------------
# AI Narrative (Groq)
# -----------------------------
def generate_ai_narrative(title, summary, transcript_text):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("⚠️ Missing GROQ_API_KEY environment variable. Skipping AI narrative.")
        return None

    print("🧠 Generating AI narrative via Groq...")

    prompt = textwrap.dedent(f"""
    You are a skilled technology writer. Write a clear, human-like narrative article
    based on the following video details.

    Title: {title}
    Summary: {summary}

    Use the transcript below as source context, but rewrite it naturally and engagingly.
    Include key insights and transitions. Use full paragraphs — no outline or bullet list
    unless absolutely necessary.

    Transcript excerpt:
    {transcript_text[:8000]}
    """)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a professional blog writer for technical tutorials."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.8,
        "max_tokens": 1800,
    }

    try:
        resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=90)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        print("✅ AI narrative generated successfully.")
        return content
    except Exception as e:
        print(f"❌ Groq API failed: {e}")
        return None


# -----------------------------
# SAVE MARKDOWN POST
# -----------------------------
def save_markdown(metadata, transcript_text, ai_article=None):
    slug = slugify(metadata["title"])
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{CONTENT_DIR}/{slug}.md"

    os.makedirs(CONTENT_DIR, exist_ok=True)
    os.makedirs(THUMBNAIL_DIR, exist_ok=True)

    # Download thumbnail
    thumb_filename = f"{THUMBNAIL_DIR}/{slug}.jpg"
    try:
        if metadata["thumbnail"]:
            r = requests.get(metadata["thumbnail"], timeout=10)
            with open(thumb_filename, "wb") as f:
                f.write(r.content)
    except Exception as e:
        print(f"⚠️ Failed to download thumbnail: {e}")

    md = textwrap.dedent(f"""\
    +++
    title = "{metadata['title']}"
    date = "{date_str}"
    summary = "{metadata['description'][:160].replace('"', "'")}"
    tags = ["zola", "youtube", "automation", "jamstack"]
    author = "{metadata.get('uploader', 'Unknown')}"

    [extra]
    youtube_url = "{metadata['webpage_url']}"
    duration = {metadata.get('duration', 0)}
    thumbnail = "blog/{slug}.jpg"
    +++

    ![{metadata['title']}]({{static}}/blog/{slug}.jpg)

    <div class="youtube-embed">
    <iframe width="560" height="315" src="https://www.youtube.com/embed/{metadata['id']}" frameborder="0" allowfullscreen></iframe>
    </div>

    [Watch on YouTube]({metadata['webpage_url']})

    ## Key Points
    - Tutorial video on {metadata['title']}
    - Covers key techniques for Zola / JAMstack
    - Duration: {int(metadata.get('duration') or 0) // 60} minutes
    - Author: {metadata.get('uploader', 'Unknown')}

    ## AI-Written Narrative
    {ai_article or '_AI narrative unavailable. Check GROQ_API_KEY configuration._'}

    ## Transcript
    {transcript_text}
    """)

    with open(filename, "w") as f:
        f.write(md)
    print(f"✅ Markdown saved: {filename}")


# -----------------------------
# MAIN EXECUTION
# -----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Markdown blog post from YouTube video.")
    parser.add_argument("--youtube", required=True, help="YouTube video URL")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    meta = fetch_youtube_info(args.youtube)
    transcript = fetch_transcript(meta["id"])
    ai_article = generate_ai_narrative(meta["title"], meta["description"], transcript)
    save_markdown(meta, transcript, ai_article)
    print("🚀 Blog post generation complete!")
