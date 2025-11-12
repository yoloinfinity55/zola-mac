"""
TTS Engine Module
Handles text-to-speech conversion, audio processing, and voice synthesis.
"""

import asyncio
import logging
from pathlib import Path
from typing import List

import edge_tts
import subprocess

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
            communicate = edge_tts.Communicate(chunk, voice)
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


async def generate_audio_from_text(text: str, output_file: Path, voice: str = "en-US-AriaNeural", temp_dir: Path = None) -> None:
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
            communicate = edge_tts.Communicate(text, voice)
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
    ]
    return voices


def estimate_audio_duration(text: str, words_per_minute: int = 150) -> float:
    """
    Estimate audio duration in seconds based on text length.

    Args:
        text: Input text
        words_per_minute: Average speaking rate

    Returns:
        Estimated duration in seconds
    """
    word_count = len(text.split())
    minutes = word_count / words_per_minute
    return minutes * 60


def validate_audio_file(audio_file: Path) -> bool:
    """
    Validate that an audio file exists and is not corrupted.

    Args:
        audio_file: Path to audio file

    Returns:
        True if file is valid, False otherwise
    """
    if not audio_file.exists():
        logger.error(f"Audio file does not exist: {audio_file}")
        return False

    try:
        # Check file size (should be > 0)
        if audio_file.stat().st_size == 0:
            logger.error(f"Audio file is empty: {audio_file}")
            return False

        # Try to get audio info with ffprobe (if available)
        try:
            result = subprocess.run([
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", "-show_streams", str(audio_file)
            ], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                return True
            else:
                logger.warning(f"Audio file validation failed for {audio_file}")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # ffprobe not available or timeout - just check file size
            return audio_file.stat().st_size > 1000  # At least 1KB

    except Exception as e:
        logger.error(f"Error validating audio file {audio_file}: {e}")
        return False
