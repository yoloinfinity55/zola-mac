import os
import re
import asyncio
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
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

# ----- Config & Environment -----
load_dotenv()

BASE_CONTENT = Path("content/blog")
BASE_CONTENT.mkdir(parents=True, exist_ok=True)
TMP_DIR = Path("audio_output/tmp")
TMP_DIR.mkdir(parents=True, exist_ok=True)

# ----- Utilities & Text Processing -----

def slugify(text: str) -> str:
    if not text: return "post"
    s = text.strip().lower()
    s = re.sub(r"[^\w\s\-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s[:80].strip('-') or "post"

def detect_lang_safe(text: str, fallback: str = "en") -> str:
    try: return detect(text)
    except Exception:
        logger.warning("Language detection failed, falling back to English.")
        return fallback

def get_simple_title(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if lines and lines[0].startswith("#"):
        return lines[0].lstrip("#").strip()
    return " ".join(text.split()[:10]) + "..."

SENTENCE_END_REGEX = re.compile(r'(?<=[。！？.!?])\s+')

def split_text_into_sentences(text: str) -> List[str]:
    text = text.replace("\r\n", "\n")
    paras = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
    sentences: List[str] = []
    for p in paras:
        parts = SENTENCE_END_REGEX.split(p)
        for part in parts:
            s = part.strip()
            if s: sentences.append(s)
    return sentences if sentences else [text]

def pack_sentences_into_chunks(sentences: List[str], max_words: int = 220) -> List[str]:
    chunks, current_chunk, current_words = [], [], 0
    for s in sentences:
        word_count = len(s.split())
        if current_words + word_count > max_words and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk, current_words = [s], word_count
        else:
            current_chunk.append(s)
            current_words += word_count
    if current_chunk: chunks.append(" ".join(current_chunk))
    return chunks

# ----- TTS Method Implementations -----

async def tts_edge(text: str, lang: str, tmp_dir: Path) -> List[Path]:
    from edge_tts import Communicate, VoicesManager
    
    if lang.startswith("zh"):
        voice_name = "zh-CN-XiaoxiaoNeural"
    else:
        voices = await VoicesManager.create()
        voice_info = voices.find(Language=lang.split('-')[0], Gender="Female")
        voice_name = voice_info[0]["Name"] if voice_info else "en-US-AriaNeural"

    chunks = pack_sentences_into_chunks(split_text_into_sentences(text))
    audio_parts = []
    for i, chunk in enumerate(chunks):
        out_file = tmp_dir / f"edge_part_{i:03}.mp3"
        comm = Communicate(chunk, voice_name)
        await comm.save(str(out_file))
        audio_parts.append(out_file)
    return audio_parts

async def tts_piper(text: str, lang: str, tmp_dir: Path) -> List[Path]:
    from piper.voice import PiperVoice
    import wave
    model_path_str = "models/en_US-lessac-medium.onnx"
    if lang.startswith("zh"): model_path_str = "models/zh_CN-huayan-medium.onnx"
    
    model_path = Path(model_path_str)
    if not model_path.exists():
        logger.error(f"[ERROR] Piper model not found at '{model_path}'. Skipping.")
        return []
        
    voice = PiperVoice.load(str(model_path))
    chunks = pack_sentences_into_chunks(split_text_into_sentences(text))
    audio_parts = []
    for i, chunk in enumerate(chunks):
        out_file = tmp_dir / f"piper_part_{i:03}.wav"
        with wave.open(str(out_file), "wb") as wav_file:
            voice.synthesize(chunk, wav_file)
        audio_parts.append(out_file)
    return audio_parts

# ----- Audio Generation and Merging -----

def merge_audio_parts(parts: List[Path], out_file: Path):
    if not parts: return
    concat_list_path = TMP_DIR / "concat_list.txt"
    converted_parts = []
    for i, part in enumerate(parts):
        if part.suffix.lower() == ".wav":
            mp3_part = TMP_DIR / f"{part.stem}_converted.mp3"
            cmd = ["ffmpeg", "-y", "-i", str(part), "-ar", "44100", "-q:a", "2", str(mp3_part)]
            subprocess.run(cmd, check=True, capture_output=True)
            converted_parts.append(mp3_part)
        else:
            converted_parts.append(part)
    
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for p in converted_parts: f.write(f"file '{p.resolve()}'\n")
        
    merge_cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list_path), "-c", "copy", str(out_file)]
    subprocess.run(merge_cmd, check=True, capture_output=True)
    
    for p in converted_parts + parts:
        if p.exists(): p.unlink()
    if concat_list_path.exists(): concat_list_path.unlink()

async def generate_audio_for_method(method: str, text: str, lang: str, tmp_dir: Path, output_dir: Path) -> Optional[Dict]:
    logger.info(f"\n--- Starting TTS Generation for Method: {method.upper()} ---")
    method_map = {
        "edge": tts_edge,
        "piper": tts_piper,
    }
    
    if method not in method_map:
        logger.warning(f"[Warning] Unknown TTS method '{method}'. Skipping.")
        return None
    
    try:
        audio_parts = await method_map[method](text, lang, tmp_dir)
        if not audio_parts:
            logger.warning(f"[Warning] No audio parts generated for method '{method}'.")
            return None
        
        output_file = output_dir / f"article_{method}.mp3"
        merge_audio_parts(audio_parts, output_file)
        
        display_name = {
            "edge": "Edge TTS (Microsoft)",
            "piper": "Piper TTS (Open-Source)",
        }.get(method, method.upper())
        
        logger.info(f"✓ Successfully created {output_file.name}")
        return {"method": method, "filename": output_file.name, "display_name": display_name}
    except Exception as e:
        logger.error(f"\n[ERROR] Failed to generate audio for method '{method}': {e}")
        for p in tmp_dir.glob(f"{method}_part_*"): p.unlink()
        return None
        
# ----- Zola Markdown Writer -----

def write_zola_index_md(md_path: Path, title: str, slug: str, audio_files: List[Dict], original_text: str):
    front_matter = [
        "+++",
        f'title = "{title.replace("\"", "\\\"")}"',
        f'slug = "{slug}"',
        f'date = "{datetime.now().isoformat()}"',
        'authors = ["auto-generator"]',
        "+++",
    ]
    
    audio_blocks = [
        "## 🎧 Listen: Audio Generated by Different TTS Engines",
        "Below are audio versions of this article generated by various Text-to-Speech engines. You can play them to compare the quality, tone, and naturalness of each provider."
    ]
    
    for audio in sorted(audio_files, key=lambda x: x['method']):
        audio_blocks.append(f"### Audio via {audio['display_name']}")
        audio_blocks.append(f'<audio controls style="width: 100%;"><source src="{audio["filename"]}" type="audio/mpeg">Your browser does not support audio.</audio>')

    content = "\n".join(front_matter) + "\n\n" + "\n\n".join(audio_blocks) + "\n\n---\n\n## Full Article Text\n\n" + original_text
    md_path.write_text(content, encoding="utf-8")
    logger.info(f"\n[Zola] Wrote final markdown file: {md_path}")

# ----- Main Pipeline -----

async def main_pipeline(input_path: Path, methods: List[str]):
    if not input_path.exists(): raise FileNotFoundError(f"Input file not found: {input_path}")
    original_text = input_path.read_text(encoding="utf-8").strip()
    if not original_text: raise ValueError("Input text is empty.")

    logger.info("\n" + "="*60 + "\nZOLA TTS SHOWCASE GENERATOR\n" + "="*60)

    title = get_simple_title(original_text)
    slug = slugify(title)
    post_dir = BASE_CONTENT / slug
    post_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"[Info] Title: {title}")
    logger.info(f"[Info] Output Directory: {post_dir}")
    logger.info(f"[Info] TTS Methods to run: {', '.join(methods)}")

    overall_lang = detect_lang_safe(original_text)
    logger.info(f"[Info] Detected language: {overall_lang}")

    tasks = [generate_audio_for_method(m, original_text, overall_lang, TMP_DIR, post_dir) for m in methods]
    results = await asyncio.gather(*tasks)
    
    successful_generations = [res for res in results if res is not None]
    
    if not successful_generations:
        logger.critical("\n[CRITICAL] No audio files were successfully generated. Aborting.")
        return

    write_zola_index_md(post_dir / "index.md", title, slug, successful_generations, original_text)

    logger.info("\n" + "="*60 + "\n✓ PIPELINE COMPLETE\n" + f"  Blog post created at: {post_dir}\n" + "="*60 + "\n")

# ----- Command-Line Interface -----

def main():
    parser = argparse.ArgumentParser(
        description="Generate a Zola blog post showcasing multiple free TTS engines.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("input_file", type=Path, help="Path to the input text file (e.g., input.txt).")
    parser.add_argument(
        "--methods", nargs='+',
        choices=["edge", "piper"], # REMOVED 'coqui'
        default=["edge"],
        help="A list of TTS engines to use. Example: --methods edge piper"
    )
    args = parser.parse_args()
    
    try:
        asyncio.run(main_pipeline(args.input_file, sorted(list(set(args.methods)))))
    except Exception as e:
        logger.exception(f"\n[FATAL ERROR] An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()