#!/usr/bin/env python3
# web_to_audio_zola.py
import asyncio
import json
import os
import re
import subprocess
import time

from pathlib import Path
from urllib.parse import urlparse

from datetime import datetime

import edge_tts
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

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


def fetch_content(url: str):
    print(f"Fetching content from: {url}")
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

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
    return text, headings


def summarize_text_with_groq(text: str):
    """Summarize text using GROQ API"""
    if not GROQ_API_KEY:
        return text
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        data = {"text": text, "summary_ratio": 0.2}
        resp = requests.post("https://api.groq.ai/v1/summarize", headers=headers, json=data)
        resp.raise_for_status()
        summary = resp.json().get("summary")
        return summary or text
    except Exception as e:
        print(f"GROQ summarization failed: {e}. Using original text as summary.")
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
        print(f"Converting chunk {idx+1}/{len(chunks)} to speech...")
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


def save_zola_markdown_with_headings(text, headings, md_path):
    """Save text into Zola Markdown"""
    front_matter = "+++\n"
    front_matter += f'title = "Web Audio Content"\n'
    front_matter += f'date = "{time.time()}"\n'
    front_matter += "+++\n\n"

    md_content = front_matter
    for tag, heading in headings:
        level = int(tag[1])
        md_content += f"{'#'*level} {heading}\n\n"
    md_content += text

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Zola post saved: {md_path}")


async def process_url(url: str):
    slug = slugify(url)
    paths = get_content_paths(slug)

    text, headings = fetch_content(url)
    summary = summarize_text_with_groq(text)

    # Save text
    with open(paths["txt"], "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Text saved: {paths['txt']}")

    # TTS
    chunks = split_text_into_chunks(summary)
    temp_mp3s = await text_to_speech_chunks(chunks, TEMP_FOLDER)
    combine_mp3(temp_mp3s, paths["mp3"])
    print(f"Audio saved: {paths['mp3']}")

    # Metadata
    metadata = {"url": url, "chunks": len(chunks), "mp3": str(paths["mp3"]), "text": str(paths["txt"]), "slug": slug}
    with open(paths["json"], "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved: {paths['json']}")

    # Zola Markdown
    save_zola_markdown_with_headings(text, headings, paths["md"])

    # Cleanup
    for mp3 in temp_mp3s:
        mp3.unlink()
    concat_file = TEMP_FOLDER / "concat_list.txt"
    if concat_file.exists():
        concat_file.unlink()
    try:
        TEMP_FOLDER.rmdir()
    except OSError:
        pass


def main():
    import sys
    import subprocess
    import time

    if len(sys.argv) < 2:
        print("Usage: python web_to_audio_zola.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    asyncio.run(process_url(url))


if __name__ == "__main__":
    main()
