import os
import sys
import asyncio
import subprocess
from pathlib import Path
import tempfile
import requests
from bs4 import BeautifulSoup
import edge_tts


# ------------------------------
#  CONFIG
# ------------------------------

OUTPUT_DIR = Path("audio_output")
OUTPUT_DIR.mkdir(exist_ok=True)
VOICE = "en-US-JennyNeural"  # You can list all voices via: edge-tts --list-voices
RATE = "+0%"                 # Adjust speed, e.g. "+10%" or "-10%"
CHUNK_SIZE = 4000            # Characters per chunk for TTS API
OUTPUT_MP3 = OUTPUT_DIR / "web_audio.mp3"


# ------------------------------
#  UTILITIES
# ------------------------------

def clean_text(text: str) -> str:
    """Clean excessive whitespace and newlines."""
    return " ".join(text.split())


def extract_text_from_url(url: str) -> str:
    """Fetch webpage and extract main readable text."""
    print(f"Fetching content from: {url}")
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    # Remove script/style
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ")
    return clean_text(text)


def split_text(text: str, chunk_size: int = CHUNK_SIZE):
    """Split large text into smaller chunks for TTS API."""
    for i in range(0, len(text), chunk_size):
        yield text[i:i + chunk_size]


def combine_mp3(ffmpeg_files, output_file):
    """
    Concatenate MP3 files losslessly using ffmpeg.
    If there's only one file, just move it to output_file.
    """
    if not ffmpeg_files:
        raise ValueError("No MP3 files to merge")

    if len(ffmpeg_files) == 1:
        # Only one chunk, just copy
        print("Only one chunk, skipping merge...")
        os.replace(ffmpeg_files[0], output_file)
        return

    # Multiple files: create concat list
    concat_list = Path(tempfile.gettempdir()) / "concat_list.txt"
    with concat_list.open("w") as f:
        for mp3 in ffmpeg_files:
            f.write(f"file '{Path(mp3).resolve().as_posix()}'\n")

    print("Merging audio files with ffmpeg...")
    subprocess.run(
        ["ffmpeg", "-f", "concat", "-safe", "0",
         "-i", str(concat_list), "-c", "copy", str(output_file)],
        check=True
    )
    concat_list.unlink()



# ------------------------------
#  MAIN TTS PROCESS
# ------------------------------

async def text_to_speech(text: str, output_path: Path):
    """Convert text to speech using Edge TTS."""
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
    await communicate.save(str(output_path))


async def process_url_to_mp3(url: str):
    """Fetch text, convert to TTS MP3, and merge output."""
    text = extract_text_from_url(url)
    if not text:
        print("No readable text found.")
        return

    chunks = list(split_text(text))
    temp_mp3s = []

    print(f"Converting {len(chunks)} chunks to speech...")

    for i, chunk in enumerate(chunks, 1):
        part_path = OUTPUT_DIR / f"part_{i:03d}.mp3"
        temp_mp3s.append(part_path)
        print(f"→ Generating chunk {i}/{len(chunks)}")
        await text_to_speech(chunk, part_path)

    combine_mp3(temp_mp3s, OUTPUT_MP3)

    # Clean up parts
    for p in temp_mp3s:
        p.unlink(missing_ok=True)

    print(f"\n✅ Done! Final MP3 saved at: {OUTPUT_MP3.resolve()}")


# ------------------------------
#  ENTRY POINT
# ------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python web_to_audio_bs.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    asyncio.run(process_url_to_mp3(url))


if __name__ == "__main__":
    main()
