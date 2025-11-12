import os
import re
import asyncio
import subprocess
import argparse
from pathlib import Path
from typing import List
import logging

from dotenv import load_dotenv
from langdetect import detect
import edge_tts

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ----- Config & environment -----
load_dotenv()
GOOGLE_CLOUD_KEY = os.getenv("GOOGLE_CLOUD_KEY")  # Optional, for Google TTS

# Directories for output and temporary files
OUTPUT_DIR = Path("audio_output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR = OUTPUT_DIR / "tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)

# ----- Utilities -----

def detect_lang_safe(text: str, fallback: str = "en") -> str:
    """Safely detect language, falling back to English on error."""
    try:
        return detect(text)
    except Exception:
        logger.warning("Language detection failed, falling back to English on error.")
        return fallback

def pick_voice_for_lang(lang: str) -> str:
    """Selects a default voice for a given language for Edge TTS."""
    L = (lang or "").lower()
    if L.startswith("zh"):
        return "zh-CN-XiaoxiaoNeural"
    if L.startswith("ja"):
        return "ja-JP-NanamiNeural"
    if L.startswith("ko"):
        return "ko-KR-SunHiNeural"
    if L.startswith("fr"):
        return "fr-FR-DeniseNeural"
    if L.startswith("es"):
        return "es-ES-ElviraNeural"
    if L.startswith("de"):
        return "de-DE-KatjaNeural"
    return "en-US-AriaNeural"

# ----- Sentence-aware chunking -----

SENTENCE_END_REGEX = re.compile(r'(?<=[。！？.!?])\s+')

def split_text_into_sentences(text: str) -> List[str]:
    """Splits text into a list of sentences based on punctuation."""
    text = text.replace("\r\n", "\n").strip()
    paras = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
    sentences: List[str] = []
    for p in paras:
        parts = SENTENCE_END_REGEX.split(p)
        for part in parts:
            s = part.strip()
            if s:
                sentences.append(s)
    return sentences if sentences else [text]

def pack_sentences_into_chunks(sentences: List[str], max_words: int = 220) -> List[str]:
    """Groups sentences into larger text chunks for TTS processing."""
    chunks = []
    current_chunk = []
    current_words = 0
    for s in sentences:
        word_count = len(s.split())
        if current_words + word_count > max_words and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [s]
            current_words = word_count
        else:
            current_chunk.append(s)
            current_words += word_count
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

# ----- TTS Methods -----

async def tts_edge(text: str, lang: str, tmp_dir: Path, max_words: int = 220) -> List[Path]:
    """Edge TTS (Microsoft) - Free, fast, good quality"""
    voice = pick_voice_for_lang(lang)
    logger.info("\n" + "="*60)
    logger.info("TTS Method : Edge TTS (Microsoft)")
    logger.info(f"Model/Voice: {voice}")
    logger.info("="*60)

    sentences = split_text_into_sentences(text)
    chunks = pack_sentences_into_chunks(sentences, max_words=max_words)
    audio_parts: List[Path] = []
    for i, chunk in enumerate(chunks):
        out_file = tmp_dir / f"part_{i:03}.mp3"
        logger.info(f"  Synthesizing chunk {i+1}/{len(chunks)}...")
        communicator = edge_tts.Communicate(chunk, voice)
        await communicator.save(str(out_file))
        audio_parts.append(out_file)
    return audio_parts

async def tts_coqui(text: str, lang: str, tmp_dir: Path, max_words: int = 220) -> List[Path]:
    """Coqui TTS - Open-source, high quality, supports voice cloning"""
    try:
        from TTS.api import TTS
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Select model based on language
        if lang.startswith("zh"):
            model_name = "tts_models/zh-CN/baker/tacotron2-DDC-GST"
        elif lang.startswith("ja"):
            model_name = "tts_models/ja/kokoro/tacotron2-DDC"
        else:
            model_name = "tts_models/en/ljspeech/tacotron2-DDC"

        logger.info("\n" + "="*60)
        logger.info("TTS Method : Coqui TTS (Open-Source)")
        logger.info(f"Model      : {model_name} (on {device})")
        logger.info("="*60)
        
        tts = TTS(model_name).to(device)
        
        sentences = split_text_into_sentences(text)
        chunks = pack_sentences_into_chunks(sentences, max_words=max_words)
        audio_parts: List[Path] = []
        
        for i, chunk in enumerate(chunks):
            out_file = tmp_dir / f"part_{i:03}.wav"
            logger.info(f"  Synthesizing chunk {i+1}/{len(chunks)}...")
            tts.tts_to_file(text=chunk, file_path=str(out_file))
            audio_parts.append(out_file)
        
        return audio_parts
    except ImportError:
        logger.error("\n[ERROR] Coqui TTS not installed. Run: pip install TTS")
        return []
    except Exception as e:
        logger.error(f"\n[ERROR] Coqui TTS failed: {e}")
        return []

async def tts_google(text: str, lang: str, tmp_dir: Path, max_words: int = 220) -> List[Path]:
    """Google Cloud TTS - High quality, requires API key"""
    try:
        from google.cloud import texttospeech
        
        if not GOOGLE_CLOUD_KEY or not Path(GOOGLE_CLOUD_KEY).exists():
            logger.error("\n[ERROR] GOOGLE_CLOUD_KEY env variable not set or path is invalid.")
            return []
        
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CLOUD_KEY
        client = texttospeech.TextToSpeechClient()
        
        if lang.startswith("zh"):
            voice_name, language_code = "cmn-CN-Wavenet-A", "cmn-CN"
        elif lang.startswith("ja"):
            voice_name, language_code = "ja-JP-Wavenet-A", "ja-JP"
        else:
            voice_name, language_code = "en-US-Wavenet-D", "en-US"
        
        logger.info("\n" + "="*60)
        logger.info("TTS Method : Google Cloud TTS")
        logger.info(f"Model/Voice: {voice_name}")
        logger.info("="*60)
        
        sentences = split_text_into_sentences(text)
        chunks = pack_sentences_into_chunks(sentences, max_words=max_words)
        audio_parts: List[Path] = []
        
        for i, chunk in enumerate(chunks):
            synthesis_input = texttospeech.SynthesisInput(text=chunk)
            voice = texttospeech.VoiceSelectionParams(language_code=language_code, name=voice_name)
            audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
            
            logger.info(f"  Synthesizing chunk {i+1}/{len(chunks)}...")
            response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
            
            out_file = tmp_dir / f"part_{i:03}.mp3"
            with open(out_file, "wb") as f:
                f.write(response.audio_content)
            audio_parts.append(out_file)
        
        return audio_parts
    except ImportError:
        logger.error("\n[ERROR] Google Cloud TTS library not installed. Run: pip install google-cloud-texttospeech")
        return []
    except Exception as e:
        logger.error(f"\n[ERROR] Google TTS failed: {e}")
        return []

async def tts_piper(text: str, lang: str, tmp_dir: Path, max_words: int = 220) -> List[Path]:
    """Piper TTS - Lightweight, fast, offline"""
    try:
        from piper.voice import PiperVoice
        import wave
        
        if lang.startswith("zh"): model_path = "models/zh_CN-huayan-medium.onnx"
        elif lang.startswith("ja"):
            model_path = "models/ja_JP-m-1.0.onnx"
        else: model_path = "models/en_US-lessac-medium.onnx"
        
        if not Path(model_path).exists():
            logger.error(f"\n[ERROR] Piper model not found at '{model_path}'")
            logger.error("Please download models from: https://huggingface.co/rhasspy/piper-voices/tree/main")
            return []
        
        logger.info("\n" + "="*60)
        logger.info("TTS Method : Piper TTS (Open-Source)")
        logger.info(f"Model      : {model_path}")
        logger.info("="*60)

        voice = PiperVoice.load(model_path)
        
        sentences = split_text_into_sentences(text)
        chunks = pack_sentences_into_chunks(sentences, max_words=max_words)
        audio_parts: List[Path] = []
        
        for i, chunk in enumerate(chunks):
            out_file = tmp_dir / f"part_{i:03}.wav"
            logger.info(f"  Synthesizing chunk {i+1}/{len(chunks)}...")
            with wave.open(str(out_file), "wb") as wav_file:
                voice.synthesize(chunk, wav_file)
            audio_parts.append(out_file)
        
        return audio_parts
    except ImportError:
        logger.error("\n[ERROR] Piper TTS not installed. Run: pip install piper-tts")
        return []
    except Exception as e:
        logger.error(f"\n[ERROR] Piper TTS failed: {e}")
        return []

# ----- TTS Dispatcher & Audio Merging -----

async def synthesize_audio(text: str, lang: str, tmp_dir: Path, method: str) -> List[Path]:
    """Dispatches to the selected TTS method."""
    dispatch = {
        "coqui": tts_coqui,
        "google": tts_google,
        "piper": tts_piper,
        "edge": tts_edge,
    }
    tts_function = dispatch.get(method.lower(), tts_edge)
    return await tts_function(text, lang, tmp_dir)

def merge_audio_parts(parts: List[Path], out_file: Path):
    """Merges multiple audio files into one MP3 using ffmpeg."""
    if not parts:
        raise RuntimeError("No audio parts were generated to merge.")

    concat_list_path = TMP_DIR / "concat_list.txt"
    converted_parts = []
    
    # Convert any WAV files to MP3 to ensure compatibility for concatenation
    for i, part in enumerate(parts):
        if part.suffix.lower() == ".wav":
            mp3_part = TMP_DIR / f"part_{i:03}_converted.mp3"
            convert_cmd = ["ffmpeg", "-y", "-i", str(part), "-ar", "44100", "-q:a", "2", str(mp3_part)]
            subprocess.run(convert_cmd, check=True, capture_output=True, text=True)
            converted_parts.append(mp3_part)
        else:
            converted_parts.append(part)

    with open(concat_list_path, "w", encoding="utf-8") as f:
        for part in converted_parts:
            f.write(f"file '{part.resolve()}'\n")

    merge_cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list_path), "-c", "copy", str(out_file)]
    logger.info("\n[ffmpeg] Merging audio chunks...")
    result = subprocess.run(merge_cmd, check=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg merge failed: {result.stderr}")

    # Cleanup temporary files
    logger.info("[Cleanup] Removing temporary files...")
    concat_list_path.unlink()
    for part in converted_parts + parts:
        if part.exists():
            part.unlink()

# ----- Main Pipeline -----

async def run_tts_test(input_path: Path, tts_method: str):
    """Main function to run the TTS test pipeline."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    original_text = input_path.read_text(encoding="utf-8").strip()
    if not original_text:
        raise ValueError("Input text is empty.")

    overall_lang = detect_lang_safe(original_text)
    logger.info(f"Detected language: {overall_lang}")

    # Generate audio from the raw article text
    audio_parts = await synthesize_audio(original_text, overall_lang, TMP_DIR, tts_method)
    
    if audio_parts:
        output_file = OUTPUT_DIR / f"article_{tts_method}.mp3"
        merge_audio_parts(audio_parts, output_file)
        logger.info("\n" + "="*60)
        logger.info("✓ PIPELINE COMPLETE")
        logger.info(f"  Output Audio File: {output_file}")
        logger.info("="*60 + "\n")
    else:
        logger.error("\n[ERROR] Audio generation failed. No output file was created.")

# ----- CLI -----

def main():
    parser = argparse.ArgumentParser(
        description="TTS testing pipeline for raw article text.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
TTS Methods:
  edge    - Edge TTS (Microsoft) [Default, Free, Fast]
  coqui   - Coqui TTS (Open-Source, High Quality, Voice Cloning)
  google  - Google Cloud TTS (Requires API Key, WaveNet Quality)
  piper   - Piper TTS (Lightweight, Offline, Fast, requires downloaded models)

Examples:
  python %(prog)s input.txt
  python %(prog)s input.txt --tts-method coqui
  python %(prog)s C:\\Users\\user\\Documents\\article.txt --tts-method piper
"""
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the input text file (e.g., input.txt)."
    )
    parser.add_argument(
        "--tts-method",
        choices=["edge", "coqui", "google", "piper"],
        default="edge",
        help="TTS engine to use for audio generation. Default: edge."
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_tts_test(args.input_file, args.tts_method))
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        logger.critical(f"\n[CRITICAL ERROR] {e}")
    except Exception as e:
        logger.exception(f"\n[UNEXPECTED ERROR] An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()")
        print("="*60)
        
        tts = TTS(model_name).to(device)
        
        sentences = split_text_into_sentences(text)
        chunks = pack_sentences_into_chunks(sentences, max_words=max_words)
        audio_parts: List[Path] = []
        
        for i, chunk in enumerate(chunks):
            out_file = tmp_dir / f"part_{i:03}.wav"
            print(f"  Synthesizing chunk {i+1}/{len(chunks)}...")
            tts.tts_to_file(text=chunk, file_path=str(out_file))
            audio_parts.append(out_file)
        
        return audio_parts
    except ImportError:
        print("\n[ERROR] Coqui TTS not installed. Run: pip install TTS")
        return []
    except Exception as e:
        print(f"\n[ERROR] Coqui TTS failed: {e}")
        return []

async def tts_google(text: str, lang: str, tmp_dir: Path, max_words: int = 220) -> List[Path]:
    """Google Cloud TTS - High quality, requires API key"""
    try:
        from google.cloud import texttospeech
        
        if not GOOGLE_CLOUD_KEY or not Path(GOOGLE_CLOUD_KEY).exists():
            print("\n[ERROR] GOOGLE_CLOUD_KEY env variable not set or path is invalid.")
            return []
        
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CLOUD_KEY
        client = texttospeech.TextToSpeechClient()
        
        if lang.startswith("zh"):
            voice_name, language_code = "cmn-CN-Wavenet-A", "cmn-CN"
        elif lang.startswith("ja"):
            voice_name, language_code = "ja-JP-Wavenet-A", "ja-JP"
        else:
            voice_name, language_code = "en-US-Wavenet-D", "en-US"
        
        print("\n" + "="*60)
        print("TTS Method : Google Cloud TTS")
        print(f"Model/Voice: {voice_name}")
        print("="*60)
        
        sentences = split_text_into_sentences(text)
        chunks = pack_sentences_into_chunks(sentences, max_words=max_words)
        audio_parts: List[Path] = []
        
        for i, chunk in enumerate(chunks):
            synthesis_input = texttospeech.SynthesisInput(text=chunk)
            voice = texttospeech.VoiceSelectionParams(language_code=language_code, name=voice_name)
            audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
            
            print(f"  Synthesizing chunk {i+1}/{len(chunks)}...")
            response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
            
            out_file = tmp_dir / f"part_{i:03}.mp3"
            with open(out_file, "wb") as f:
                f.write(response.audio_content)
            audio_parts.append(out_file)
        
        return audio_parts
    except ImportError:
        print("\n[ERROR] Google Cloud TTS library not installed. Run: pip install google-cloud-texttospeech")
        return []
    except Exception as e:
        print(f"\n[ERROR] Google TTS failed: {e}")
        return []

async def tts_piper(text: str, lang: str, tmp_dir: Path, max_words: int = 220) -> List[Path]:
    """Piper TTS - Lightweight, fast, offline"""
    try:
        from piper.voice import PiperVoice
        import wave
        
        if lang.startswith("zh"): model_path = "models/zh_CN-huayan-medium.onnx"
        elif lang.startswith("ja"): model_path = "models/ja_JP-m-1.0.onnx"
        else: model_path = "models/en_US-lessac-medium.onnx"
        
        if not Path(model_path).exists():
            print(f"\n[ERROR] Piper model not found at '{model_path}'")
            print("Please download models from: https://huggingface.co/rhasspy/piper-voices/tree/main")
            return []
        
        print("\n" + "="*60)
        print("TTS Method : Piper TTS (Open-Source)")
        print(f"Model      : {model_path}")
        print("="*60)

        voice = PiperVoice.load(model_path)
        
        sentences = split_text_into_sentences(text)
        chunks = pack_sentences_into_chunks(sentences, max_words=max_words)
        audio_parts: List[Path] = []
        
        for i, chunk in enumerate(chunks):
            out_file = tmp_dir / f"part_{i:03}.wav"
            print(f"  Synthesizing chunk {i+1}/{len(chunks)}...")
            with wave.open(str(out_file), "wb") as wav_file:
                voice.synthesize(chunk, wav_file)
            audio_parts.append(out_file)
        
        return audio_parts
    except ImportError:
        print("\n[ERROR] Piper TTS not installed. Run: pip install piper-tts")
        return []
    except Exception as e:
        print(f"\n[ERROR] Piper TTS failed: {e}")
        return []

# ----- TTS Dispatcher & Audio Merging -----

async def synthesize_audio(text: str, lang: str, tmp_dir: Path, method: str) -> List[Path]:
    """Dispatches to the selected TTS method."""
    dispatch = {
        "coqui": tts_coqui,
        "google": tts_google,
        "piper": tts_piper,
        "edge": tts_edge,
    }
    tts_function = dispatch.get(method.lower(), tts_edge)
    return await tts_function(text, lang, tmp_dir)

def merge_audio_parts(parts: List[Path], out_file: Path):
    """Merges multiple audio files into one MP3 using ffmpeg."""
    if not parts:
        raise RuntimeError("No audio parts were generated to merge.")

    concat_list_path = TMP_DIR / "concat_list.txt"
    converted_parts = []
    
    # Convert any WAV files to MP3 to ensure compatibility for concatenation
    for i, part in enumerate(parts):
        if part.suffix.lower() == ".wav":
            mp3_part = TMP_DIR / f"part_{i:03}_converted.mp3"
            convert_cmd = ["ffmpeg", "-y", "-i", str(part), "-ar", "44100", "-q:a", "2", str(mp3_part)]
            subprocess.run(convert_cmd, check=True, capture_output=True, text=True)
            converted_parts.append(mp3_part)
        else:
            converted_parts.append(part)

    with open(concat_list_path, "w", encoding="utf-8") as f:
        for part in converted_parts:
            f.write(f"file '{part.resolve()}'\n")

    merge_cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list_path), "-c", "copy", str(out_file)]
    print("\n[ffmpeg] Merging audio chunks...")
    result = subprocess.run(merge_cmd, check=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg merge failed: {result.stderr}")

    # Cleanup temporary files
    print("[Cleanup] Removing temporary files...")
    concat_list_path.unlink()
    for part in converted_parts + parts:
        if part.exists():
            part.unlink()

# ----- Main Pipeline -----

async def run_tts_test(input_path: Path, tts_method: str):
    """Main function to run the TTS test pipeline."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    original_text = input_path.read_text(encoding="utf-8").strip()
    if not original_text:
        raise ValueError("Input text is empty.")

    overall_lang = detect_lang_safe(original_text)
    print(f"Detected language: {overall_lang}")

    # Generate audio from the raw article text
    audio_parts = await synthesize_audio(original_text, overall_lang, TMP_DIR, tts_method)
    
    if audio_parts:
        output_file = OUTPUT_DIR / f"article_{tts_method}.mp3"
        merge_audio_parts(audio_parts, output_file)
        print("\n" + "="*60)
        print("✓ PIPELINE COMPLETE")
        print(f"  Output Audio File: {output_file}")
        print("="*60 + "\n")
    else:
        print("\n[ERROR] Audio generation failed. No output file was created.")

# ----- CLI -----

def main():
    parser = argparse.ArgumentParser(
        description="TTS testing pipeline for raw article text.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
TTS Methods:
  edge    - Edge TTS (Microsoft) [Default, Free, Fast]
  coqui   - Coqui TTS (Open-Source, High Quality, Voice Cloning)
  google  - Google Cloud TTS (Requires API Key, WaveNet Quality)
  piper   - Piper TTS (Lightweight, Offline, Fast, requires downloaded models)

Examples:
  python %(prog)s input.txt
  python %(prog)s input.txt --tts-method coqui
  python %(prog)s C:\\Users\\user\\Documents\\article.txt --tts-method piper
"""
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the input text file (e.g., input.txt)."
    )
    parser.add_argument(
        "--tts-method",
        choices=["edge", "coqui", "google", "piper"],
        default="edge",
        help="TTS engine to use for audio generation. Default: edge."
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_tts_test(args.input_file, args.tts_method))
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"\n[CRITICAL ERROR] {e}")
    except Exception as e:
        print(f"\n[UNEXPECTED ERROR] An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()