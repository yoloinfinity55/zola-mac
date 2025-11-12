import asyncio
import logging
import subprocess
from pathlib import Path
from edge_tts import Communicate

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
MAX_WORDS_PER_CHUNK = 250
TEMP_DIR = Path("temp_audio")
TEMP_DIR.mkdir(exist_ok=True)

def split_text_into_chunks(text: str, max_words: int = MAX_WORDS_PER_CHUNK) -> list[str]:
    """Split text into chunks for TTS processing."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i:i + max_words])
        if chunk.strip():
            chunks.append(chunk)
    logger.info(f"Split text into {len(chunks)} chunks (max {max_words} words each)")
    return chunks

async def text_to_speech_chunks(chunks: list[str], voice: str) -> list[Path]:
    """Convert text chunks to speech."""
    mp3_files = []
    for idx, chunk in enumerate(chunks):
        mp3_path = TEMP_DIR / "03d"
        mp3_files.append(mp3_path)
        logger.info(f"Converting chunk {idx+1}/{len(chunks)} for {voice}...")
        try:
            communicate = Communicate(chunk, voice)
            await communicate.save(str(mp3_path))
        except Exception as e:
            logger.error(f"Failed to convert chunk {idx+1} for {voice}: {e}")
            raise
    return mp3_files

def combine_mp3(mp3_files: list[Path], output_file: Path) -> None:
    """Combine multiple MP3 files into a single audio file using FFmpeg."""
    logger.info(f"Combining {len(mp3_files)} audio chunks...")

    concat_list = TEMP_DIR / "concat_list.txt"
    try:
        with open(concat_list, "w") as f:
            for mp3 in mp3_files:
                f.write(f"file '{mp3.resolve()}'\n")

        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            "-y",
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
        if concat_list.exists():
            concat_list.unlink()

async def generate_audio_for_voice(text: str, voice: str) -> None:
    """Generate audio for a single voice, handling chunking if necessary."""
    output_file = Path(f"output_{voice}.mp3")
    try:
        chunks = split_text_into_chunks(text)
        if len(chunks) == 1:
            # Single chunk - direct conversion
            logger.info(f"Single chunk for {voice} - direct TTS conversion")
            communicate = Communicate(text, voice)
            await communicate.save(str(output_file))
        else:
            # Multiple chunks - process and combine
            logger.info(f"Multiple chunks ({len(chunks)}) for {voice} - processing with combination")
            temp_mp3s = await text_to_speech_chunks(chunks, voice)
            combine_mp3(temp_mp3s, output_file)

            # Clean up temporary files
            for mp3 in temp_mp3s:
                if mp3.exists():
                    mp3.unlink()

        logger.info(f"✅ Successfully generated {output_file} for {voice}")

    except Exception as e:
        logger.error(f"❌ Failed to generate for {voice}: {e}")

async def main():
    input_file = Path('input.txt')
    if not input_file.exists():
        logger.error("Input file 'input.txt' not found.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read().strip()

    if not text:
        logger.error("Input text is empty.")
        return

    voices = [
        "de-DE-FlorianMultilingualNeural",
        "de-DE-SeraphinaMultilingualNeural",
        "en-AU-WilliamMultilingualNeural",
        "en-US-AndrewMultilingualNeural",
        "en-US-AvaMultilingualNeural",
        "en-US-BrianMultilingualNeural",
        "en-US-EmmaMultilingualNeural",
        "fr-FR-RemyMultilingualNeural",
        "fr-FR-VivienneMultilingualNeural",
        "it-IT-GiuseppeMultilingualNeural",
        "ko-KR-HyunsuMultilingualNeural",
        "pt-BR-ThalitaMultilingualNeural"
    ]

    logger.info(f"Starting TTS generation for {len(voices)} voices...")

    for voice in voices:
        await generate_audio_for_voice(text, voice)

    # Clean up temp dir if empty
    try:
        TEMP_DIR.rmdir()
    except OSError:
        pass  # Not empty, leave it

    logger.info("All TTS generations completed.")

if __name__ == "__main__":
    asyncio.run(main())
