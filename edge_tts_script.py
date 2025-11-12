"""
Edge TTS Script
Converts text to speech using Microsoft Edge TTS, with support for multilingual voices.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional

import subprocess
from edge_tts import Communicate, VoicesManager

logger = logging.getLogger(__name__)


async def text_to_speech_chunks(chunks: List[str], temp_folder: Path, voice: str = "en-US-AriaNeural") -> List[Path]:
    """
    Convert text chunks to speech using Edge TTS.

    Args:
        chunks: List of text chunks to convert
        temp_folder: Directory to store temporary audio files
        voice: TTS voice to use

    Returns:
        List of paths to generated audio files
    """
    mp3_files = []
    for idx, chunk in enumerate(chunks):
        mp3_path = temp_folder / "03d"
        mp3_files.append(mp3_path)
        logger.info(f"Converting chunk {idx+1}/{len(chunks)} to speech...")
        try:
            communicate = Communicate(chunk, voice)
            await communicate.save(str(mp3_path))
        except Exception as e:
            logger.error(f"Failed to convert chunk {idx+1}: {e}")
            raise
    return mp3_files


def combine_mp3(mp3_files: List[Path], output_file: Path) -> None:
    """
    Combine multiple MP3 files into a single audio file using FFmpeg.

    Args:
        mp3_files: List of MP3 file paths to combine
        output_file: Output file path
    """
    logger.info(f"Combining {len(mp3_files)} audio chunks...")

    # Create concat list file
    temp_folder = mp3_files[0].parent
    concat_list = temp_folder / "concat_list.txt"

    try:
        with open(concat_list, "w") as f:
            for mp3 in mp3_files:
                f.write(f"file '{mp3.resolve()}'\n")

        # Run FFmpeg concatenation
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            "-y",  # Overwrite output file
            str(output_file)
        ]

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Successfully combined audio into {output_file}")

    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg concatenation failed: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Audio combination failed: {e}")
        raise
    finally:
        # Clean up concat list
        if concat_list.exists():
            concat_list.unlink()


def split_text_into_chunks(text: str, max_words: int = 250) -> List[str]:
    """
    Split text into chunks for TTS processing.

    Args:
        text: Input text to split
        max_words: Maximum words per chunk

    Returns:
        List of text chunks
    """
    words = text.split()
    chunks = []

    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i:i + max_words])
        if chunk.strip():  # Only add non-empty chunks
            chunks.append(chunk)

    logger.info(f"Split text into {len(chunks)} chunks (max {max_words} words each)")
    return chunks


async def generate_audio_from_text(text: str, output_file: Path, voice: str = "en-US-AriaNeural", temp_dir: Optional[Path] = None) -> None:
    """
    Generate audio from text using Edge TTS.

    Args:
        text: Text to convert to speech
        output_file: Output audio file path
        voice: TTS voice to use
        temp_dir: Temporary directory for chunk processing
    """
    if temp_dir is None:
        temp_dir = output_file.parent / "tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Split text into manageable chunks
        chunks = split_text_into_chunks(text)

        if len(chunks) == 1:
            # Single chunk - direct conversion
            logger.info("Single chunk - direct TTS conversion")
            communicate = Communicate(text, voice)
            await communicate.save(str(output_file))
        else:
            # Multiple chunks - process and combine
            logger.info(f"Multiple chunks ({len(chunks)}) - processing with combination")
            temp_mp3s = await text_to_speech_chunks(chunks, temp_dir, voice)
            combine_mp3(temp_mp3s, output_file)

            # Clean up temporary files
            for mp3 in temp_mp3s:
                if mp3.exists():
                    mp3.unlink()

    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        raise


async def get_multilingual_voices() -> dict:
    """
    Get list of available Edge TTS voices that can handle English, Chinese, or mixed text.

    Returns:
        Dictionary with voice categories
    """
    try:
        voices = await VoicesManager.create()
        english_voices = voices.find(Language="en")
        chinese_voices = voices.find(Language="zh")
        multilingual_voices = voices.find(Language="en") + voices.find(Language="zh")  # Combined for mixed

        return {
            "english": [v["ShortName"] for v in english_voices],
            "chinese": [v["ShortName"] for v in chinese_voices],
            "multilingual": [v["ShortName"] for v in multilingual_voices if "Multilingual" in v["ShortName"]]
        }
    except Exception as e:
        logger.error(f"Failed to fetch voices: {e}")
        # More comprehensive fallback list
        return {
            "english": [
                "en-US-AriaNeural", "en-US-ZiraNeural", "en-US-JennyNeural", "en-US-GuyNeural",
                "en-GB-SoniaNeural", "en-GB-RyanNeural", "en-GB-LibbyNeural", "en-GB-AriaNeural",
                "en-AU-NatashaNeural", "en-AU-WilliamNeural", "en-CA-ClaraNeural", "en-CA-LiamNeural",
                "en-IN-NeerjaNeural", "en-IN-PrabhatNeural"
            ],
            "chinese": [
                "zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural", "zh-CN-XiaochenNeural", "zh-CN-XiaohanNeural",
                "zh-CN-XiaomengNeural", "zh-CN-XiaomoNeural", "zh-CN-XiaoqiuNeural", "zh-CN-XiaoruiNeural",
                "zh-CN-XiaoshuangNeural", "zh-CN-XiaoxuanNeural", "zh-CN-XiaoyanNeural", "zh-CN-XiaoyouNeural",
                "zh-CN-XiaozhenNeural", "zh-CN-YunfengNeural", "zh-CN-YunhaoNeural", "zh-CN-YunjianNeural",
                "zh-CN-YunxiaNeural", "zh-CN-YunyangNeural", "zh-CN-YunyeNeural", "zh-CN-YunzeNeural",
                "zh-HK-HiuGaaiNeural", "zh-HK-HiuMaanNeural", "zh-HK-WanLungNeural",
                "zh-TW-HsiaoChenNeural", "zh-TW-HsiaoYuNeural", "zh-TW-YunJheNeural"
            ],
            "multilingual": [
                "en-US-AriaNeural", "en-US-ZiraNeural", "zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural"
            ]
        }


def get_available_voices() -> List[str]:
    """
    Get list of available Edge TTS voices.

    Returns:
        List of voice names
    """
    # Common Edge TTS voices
    voices = [
        "en-US-AriaNeural",      # Female, clear and natural
        "en-US-ZiraNeural",      # Female, warm and professional
        "en-US-JennyNeural",     # Female, friendly and approachable
        "en-US-GuyNeural",       # Male, clear and professional
        "en-GB-SoniaNeural",     # British Female
        "en-GB-RyanNeural",      # British Male
        "en-AU-NatashaNeural",   # Australian Female
        "en-CA-ClaraNeural",     # Canadian Female
        "zh-CN-XiaoxiaoNeural",  # Chinese Female
        "zh-CN-YunxiNeural",     # Chinese Male
    ]
    return voices


async def main():
    """Main function to convert input.txt to audio."""
    logging.basicConfig(level=logging.INFO)

    input_file = Path('input.txt')
    if not input_file.exists():
        logger.error("Input file 'input.txt' not found.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read().strip()

    if not text:
        logger.error("Input text is empty.")
        return

    # Get available voices
    logger.info("Fetching available multilingual voices...")
    voices = await get_multilingual_voices()
    logger.info(f"English voices: {voices['english'][:5]}...")  # Show first 5
    logger.info(f"Chinese voices: {voices['chinese'][:5]}...")
    logger.info(f"Multilingual voices: {voices['multilingual'][:5]}...")

    # Write voices to list.txt
    def format_voice(voice):
        parts = voice.split('-')
        if len(parts) >= 3:
            locale = f"{parts[0]}-{parts[1]}"
            name = '-'.join(parts[2:])
            return f"({locale}, {name})"
        return f"({voice})"

    with open("list.txt", "w", encoding="utf-8") as f:
        f.write("Fetching Available Voices\n\n")
        f.write("English Voices:\n\n")
        for voice in voices['english']:
            f.write(f"Microsoft Server Speech Text to Speech Voice {format_voice(voice)}\n")
        f.write("\n\n\nChinese Voices:\n\n")
        for voice in voices['chinese']:
            f.write(f"Microsoft Server Speech Text to Speech Voice {format_voice(voice)}\n")
        f.write("\n\n\nMultilingual Voices:\n\n")
        for voice in voices['multilingual']:
            f.write(f"Microsoft Server Speech Text to Speech Voice {format_voice(voice)}\n")

    logger.info("✅ Voices list written to list.txt")

    # Generate audio for each multilingual voice
    multilingual_voices = voices['multilingual']
    if not multilingual_voices:
        logger.error("No multilingual voices available")
        return

    for voice in multilingual_voices:
        output_file = Path(f"output_{voice}.mp3")
        logger.info(f"Converting text to speech using voice: {voice}")

        try:
            await generate_audio_from_text(text, output_file, voice)
            logger.info(f"✅ Audio saved to {output_file}")
        except Exception as e:
            logger.error(f"Failed to generate audio for {voice}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
