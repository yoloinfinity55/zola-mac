import asyncio
import requests
from bs4 import BeautifulSoup
import os
import sys
import re
from readability import Document
from langdetect import detect, DetectorFactory
import edge_tts
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure consistent language detection
DetectorFactory.seed = 0

# Output folders
OUTPUT_FOLDER = Path("audio_output")
TEXT_FILE = OUTPUT_FOLDER / "web_audio.txt"
MP3_FILE = OUTPUT_FOLDER / "web_audio.mp3"
TEMP_FOLDER = Path("/tmp/audio_output")

# Create folders if they don't exist
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
TEMP_FOLDER.mkdir(parents=True, exist_ok=True)

# Max chunk size (Edge-TTS supports ~5000 characters per request)
MAX_CHUNK = 4000

def get_language(text):
    try:
        lang = detect(text)
        return lang
    except Exception:
        logger.warning("Language detection failed, defaulting to English.")
        return "en"

def chunk_text(text, max_len=MAX_CHUNK):
    """
    Split text into chunks that TTS can handle.
    """
    chunks = []
    current = ""
    for line in text.splitlines():
        if len(current) + len(line) + 1 > max_len:
            chunks.append(current.strip())
            current = ""
        current += line + " "
    if current.strip():
        chunks.append(current.strip())
    return chunks

async def generate_chunk(text, filename, voice="en-US-JennyNeural"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filename)
    logger.info(f"Chunk saved: {filename}")

def combine_mp3(temp_files, output_file):
    """
    Merge mp3 chunks with ffmpeg.
    """
    concat_list = TEMP_FOLDER / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for file in temp_files:
            f.write(f"file '{file}'\n")
    subprocess_cmd = [
        "ffmpeg", "-f", "concat", "-safe", "0",
        "-i", str(concat_list), "-c", "copy", str(output_file), "-y"
    ]
    logger.info("Merging audio files with ffmpeg...")
    import subprocess
    subprocess.run(subprocess_cmd, check=True)

async def process_url_to_mp3(url):
    # Fetch webpage with User-Agent
    logger.info(f"Fetching content from: {url}")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    response.encoding = response.apparent_encoding

    # Extract main content
    doc = Document(response.text)
    summary_html = doc.summary()
    soup = BeautifulSoup(summary_html, "html.parser")
    text = soup.get_text(separator="\n", strip=True)

    # Post-processing
    text = re.sub(r'打开APP阅读', '', text)
    text = re.sub(r'相关文章.*', '', text, flags=re.DOTALL)

    # Optional truncate
    if len(text) > 10000:
        text = text[:10000] + "\n[Text truncated for brevity.]"

    # Save text content first
    TEXT_FILE.write_text(text, encoding="utf-8")
    logger.info(f"Text content saved: {TEXT_FILE}")

    # Detect language and set voice
    lang = get_language(text)
    if lang.startswith("zh"):
        voice = "zh-CN-XiaoxiaoNeural"
    else:
        voice = "en-US-JennyNeural"

    # Chunking
    chunks = chunk_text(text)
    logger.info(f"Converting {len(chunks)} chunks to speech...")

    temp_files = []
    for i, chunk in enumerate(chunks):
        filename = TEMP_FOLDER / f"part_{i+1:03d}.mp3"
        await generate_chunk(chunk, str(filename), voice=voice)
        temp_files.append(filename)

    # Merge
    combine_mp3(temp_files, MP3_FILE)
    logger.info(f"Audio saved: {MP3_FILE}")

def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter the webpage URL: ").strip()

    try:
        asyncio.run(process_url_to_mp3(url))
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()
