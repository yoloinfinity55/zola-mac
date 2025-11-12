import os
import asyncio
import edge_tts
from langdetect import detect, LangDetectException
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def text_to_speech_edge_tts(text_file="web_audio.txt", output_file="web_audio.mp3"):
    if not os.path.exists(text_file):
        logger.error(f"{text_file} not found.")
        return

    with open(text_file, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        logger.error(f"{text_file} is empty.")
        return

    try:
        lang = detect(text[:500])
    except LangDetectException:
        lang = "en"
        logger.warning("Language detection failed, using English.")

    # Choose voice based on detected language
    if lang.startswith("zh"):
        voice = "zh-CN-XiaoxiaoNeural"
    elif lang.startswith("ja"):
        voice = "ja-JP-NanamiNeural"
    elif lang.startswith("ko"):
        voice = "ko-KR-SunHiNeural"
    elif lang.startswith("es"):
        voice = "es-ES-ElviraNeural"
    else:
        voice = "en-US-JennyNeural"

    logger.info(f"Detected language: {lang}, using voice: {voice}")

    communicate = edge_tts.Communicate(text, voice=voice)
    await communicate.save(output_file)
    logger.info(f"✅ Audio saved as {output_file}")

def main():
    asyncio.run(text_to_speech_edge_tts())

if __name__ == "__main__":
    main()
