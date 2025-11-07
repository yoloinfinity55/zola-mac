import os
import asyncio
import edge_tts
from langdetect import detect
from pydub import AudioSegment
from tqdm import tqdm
import tempfile
import textwrap

# Optional background music file (set to None if not needed)
BACKGROUND_MUSIC = "bgm.mp3"  # place in same folder, or set to None

# Voice map per language
VOICE_MAP = {
    "zh": "zh-CN-XiaoxiaoNeural",
    "en": "en-US-JennyNeural",
    "ja": "ja-JP-NanamiNeural",
    "ko": "ko-KR-SunHiNeural",
    "es": "es-ES-ElviraNeural",
}

def detect_language(text):
    try:
        lang = detect(text)
        print(f"🌐 Detected language: {lang}")
        return lang
    except Exception:
        print("⚠️ Could not detect language, defaulting to English.")
        return "en"

def chunk_text(text, max_chars=300):
    """Split long text into natural short paragraphs for smoother synthesis."""
    text = text.replace("\n", " ").strip()
    parts = textwrap.wrap(text, max_chars, break_long_words=False)
    return parts

async def tts_chunk_to_mp3(text_chunk, voice, filename):
    """Generate MP3 for one chunk."""
    communicate = edge_tts.Communicate(text_chunk, voice=voice)
    await communicate.save(filename)

async def generate_tts(text, lang_code, output_file):
    """Generate final MP3, merging chunks and optional background music."""
    voice = VOICE_MAP.get(lang_code.split("-")[0], VOICE_MAP["en"])
    print(f"🗣️ Using voice: {voice}")

    chunks = chunk_text(text)
    temp_files = []

    # Generate chunk audio sequentially
    for i, chunk in enumerate(tqdm(chunks, desc="Generating speech chunks")):
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        await tts_chunk_to_mp3(chunk, voice, temp_file)
        temp_files.append(temp_file)

    # Merge all MP3s
    print("🔊 Combining audio segments...")
    final_audio = AudioSegment.empty()
    for f in temp_files:
        final_audio += AudioSegment.from_mp3(f)
        os.remove(f)

    # Add background music softly if available
    if BACKGROUND_MUSIC and os.path.exists(BACKGROUND_MUSIC):
        bgm = AudioSegment.from_mp3(BACKGROUND_MUSIC) - 25  # reduce volume
        bgm = bgm[:len(final_audio)]  # trim to same length
        final_audio = final_audio.overlay(bgm)
        print("🎶 Background music mixed in.")

    final_audio.export(output_file, format="mp3", bitrate="192k")
    print(f"✅ Speech saved to {output_file}")

def add_audio_link_to_markdown(audio_file, markdown_file="post.md"):
    """Append audio player link to a markdown blog post."""
    link = f"\n\n{{{{ audio({audio_file}) }}}}\n"
    with open(markdown_file, "a", encoding="utf-8") as f:
        f.write(link)
    print(f"📎 Added audio link to {markdown_file}")

def main():
    input_file = "web_audio.txt"
    output_file = "web_audio.mp3"

    if not os.path.exists(input_file):
        print(f"❌ {input_file} not found.")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        print("❌ Text file is empty.")
        return

    lang = detect_language(text)
    asyncio.run(generate_tts(text, lang, output_file))

    # Optional: Add to markdown automatically
    if os.path.exists("post.md"):
        add_audio_link_to_markdown(output_file, "post.md")

if __name__ == "__main__":
    main()
