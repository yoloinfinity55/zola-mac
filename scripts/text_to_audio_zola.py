#!/usr/bin/env python3
# text_to_audio_zola.py
"""
Full pipeline:
 - Read input.txt (supports mixed English + Chinese)
 - Generate AI narration script (asset.txt) — podcast-style (Option A)
 - Generate summary, metadata (GROQ optional)
 - Create two MP3s:
     - article.mp3  -> TTS of original article
     - narration.mp3 -> TTS of AI narration (asset.txt)
 - Insert both audio players at top of content/blog/<slug>/index.md (Choice A layout)
 - Save asset.txt, asset.translated.txt (if available), asset.json (metadata)
 - Supports --dry-run to skip TTS & ffmpeg (inspect narration and front matter)
"""
from __future__ import annotations
import os
import re
import json
import math
import asyncio
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import List

import requests
from dotenv import load_dotenv
from langdetect import detect, LangDetectException
import edge_tts

# ----- Config & environment -----
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # optional but recommended

BASE_CONTENT = Path("content/blog")
BASE_CONTENT.mkdir(parents=True, exist_ok=True)
TMP_DIR = Path("audio_output/tmp")
TMP_DIR.mkdir(parents=True, exist_ok=True)

# ----- Utilities -----

def slugify(text: str) -> str:
    if not text:
        return "post"
    s = text.strip().lower()
    s = re.sub(r"[^\w\s\-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s[:80] or "post"

def detect_lang_safe(text: str, fallback: str = "en") -> str:
    try:
        return detect(text)
    except Exception:
        return fallback

def estimate_read_time(text: str, wpm: int = 200) -> int:
    words = len(text.split())
    return max(1, math.ceil(words / wpm))

def pick_voice_for_lang(lang: str) -> str:
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

# ----- GROQ helper -----

def call_groq_chat(system: str, user: str, max_tokens: int = 900, temperature: float = 0.25) -> str:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set")
    url = "https://api.groq.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "llama-3.1-70b-versatile",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        raise RuntimeError("Unexpected GROQ response: " + str(e) + " -> " + json.dumps(data)[:1200])

# ----- Sentence-aware chunking -----

SENTENCE_END_REGEX = re.compile(r'(?<=[。！？.!?])\s+')

def split_text_into_sentences(text: str) -> List[str]:
    # Split by Japanese/Chinese punctuation and typical English punctuation.
    # Keep newlines as paragraph boundaries first.
    text = text.replace("\r\n", "\n")
    paras = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
    sentences: List[str] = []
    for p in paras:
        # Use our regex to split sentences; fallback to naive split
        parts = SENTENCE_END_REGEX.split(p)
        for part in parts:
            s = part.strip()
            if s:
                sentences.append(s)
    # final fallback: if nothing, split by words
    if not sentences:
        return [text]
    return sentences

def pack_sentences_into_chunks(sentences: List[str], max_words: int = 220) -> List[str]:
    chunks = []
    current = []
    current_words = 0
    for s in sentences:
        w = len(s.split())
        if current_words + w > max_words and current:
            chunks.append(" ".join(current))
            current = [s]
            current_words = w
        else:
            current.append(s)
            current_words += w
    if current:
        chunks.append(" ".join(current))
    return chunks

# ----- Narration generation (Option A) -----

def generate_narration_script_ai(original_text: str, title: str | None = None) -> str:
    """
    Produce a podcast-style narration script. Prefer GROQ if available, else use local heuristic.
    """
    if GROQ_API_KEY:
        system = (
            "You are a professional podcast host and editor. Produce a concise, "
            "engaging narration script suitable for a 2-6 minute audio segment. "
            "Keep sentences short and easy to narrate. Preserve facts, do not invent."
        )
        user = (
            f"TITLE: {title or ''}\n\n"
            "ARTICLE:\n" + original_text +
            "\n\nINSTRUCTIONS:\n"
            "- Produce an intro (1-2 lines), body (3-6 short paragraphs), and outro (1-2 lines).\n"
            "- Keep mixed-language text in original languages (do not translate) but ensure flow.\n"
            "- Avoid listing raw code blocks; summarize code intent when present.\n"
            "- Output only the narration script (no markdown, no extra commentary)."
        )
        try:
            out = call_groq_chat(system, user, max_tokens=1000, temperature=0.35)
            return out.strip()
        except Exception as e:
            print("[GROQ] narration generation failed:", e)

    # Local fallback: assemble friendly spoken script from 3-5 key paragraphs
    sentences = split_text_into_sentences(original_text)
    # pick up to first ~50-250 words worth of content while deduplicating repeated sentences
    chosen = []
    seen = set()
    word_count = 0
    for s in sentences:
        short = s.strip()[:200]
        if short in seen:
            continue
        seen.add(short)
        chosen.append(s.strip())
        word_count += len(s.split())
        if word_count >= 250:
            break
    if not chosen:
        chosen = [original_text.strip()]
    intro = f"Hello — a quick read on {title}." if title else "Hello — here's a quick summary."
    body = []
    for p in chosen[:4]:
        # keep sentences reasonably short for narration
        sents = re.split(r'(?<=[。！？.!?])\s+', p)
        if len(sents) > 3:
            body.append(" ".join(sents[:2]).strip())
        else:
            body.append(p)
    outro = "Thanks for listening. See the article and comments for full details."
    script = "\n\n".join([intro] + body + [outro])
    return script

# ----- Summary, title, metadata (advanced) -----

def generate_smart_summary(original_text: str) -> str:
    if GROQ_API_KEY:
        system = "You are an expert editor. Produce a concise 2-4 paragraph summary suitable for previews and for feeding into narration."
        user = f"ARTICLE:\n{original_text}\n\nINSTRUCTIONS: Output only the summary text."
        try:
            return call_groq_chat(system, user, max_tokens=700, temperature=0.28).strip()
        except Exception as e:
            print("[GROQ] summary failed:", e)
    paras = [p.strip() for p in re.split(r'\n{2,}', original_text) if p.strip()]
    return "\n\n".join(paras[:3])[:3000]

def generate_smart_title(original_text: str) -> str:
    lines = [ln for ln in original_text.splitlines() if ln.strip()]
    if lines and lines[0].startswith("#"):
        return lines[0].lstrip("#").strip()
    if GROQ_API_KEY:
        system = "You are a professional blog editor. Produce a single concise SEO-friendly title (6-14 words). Output only the title."
        user = f"ARTICLE:\n{original_text}\n\nINSTRUCTIONS: Output only the title."
        try:
            return call_groq_chat(system, user, max_tokens=40, temperature=0.6).strip().strip('"')
        except Exception as e:
            print("[GROQ] title generation failed:", e)
    # fallback heuristic
    first_para = next((p for p in re.split(r'\n{2,}', original_text) if p.strip()), "")
    words = first_para.split()
    return " ".join(words[:10]) + ("..." if len(words) > 10 else "")

def generate_advanced_metadata(original_text: str, title: str, lang: str) -> dict:
    fallback = {
        "tags": [],
        "keywords": [],
        "excerpt": (original_text[:280].strip() + ("..." if len(original_text) > 280 else "")),
        "category": "general",
        "read_time_minutes": estimate_read_time(original_text),
        "difficulty": "intermediate",
        "tl_dr": [],
        "key_takeaways": [],
        "related_topics": [],
        "suggested_cta": "Read the full article and subscribe.",
        "diagnostics": {"style": "informative", "tone": "neutral", "content_type": "article"},
        "translations": {}
    }
    if not GROQ_API_KEY:
        return fallback
    system = "You are an expert metadata assistant. Output strictly valid JSON only."
    user = (
        f"TITLE:\n{title}\n\nFULL_TEXT:\n{original_text}\n\nLANG:{lang}\n\n"
        "TASK: Output JSON with keys: tags, keywords, excerpt (30-40 words), category, read_time_minutes, difficulty, "
        "tl_dr (3-6 bullets), key_takeaways (3-6 bullets), related_topics (3-8), suggested_cta, diagnostics (style,tone,content_type), translations (excerpt_en, summary_en, excerpt_orig)."
    )
    try:
        raw = call_groq_chat(system, user, max_tokens=1200, temperature=0.25)
        try:
            meta = json.loads(raw)
        except Exception:
            s = raw.find("{")
            e = raw.rfind("}") + 1
            if s >= 0 and e > s:
                meta = json.loads(raw[s:e])
            else:
                raise
        # ensure keys
        meta.setdefault("tags", [])
        meta.setdefault("keywords", [])
        meta.setdefault("excerpt", fallback["excerpt"])
        meta.setdefault("category", fallback["category"])
        meta.setdefault("read_time_minutes", estimate_read_time(original_text))
        meta.setdefault("difficulty", fallback["difficulty"])
        meta.setdefault("tl_dr", [])
        meta.setdefault("key_takeaways", [])
        meta.setdefault("related_topics", [])
        meta.setdefault("suggested_cta", fallback["suggested_cta"])
        meta.setdefault("diagnostics", fallback["diagnostics"])
        meta.setdefault("translations", {})
        return meta
    except Exception as e:
        print("[GROQ] metadata failed:", e)
        return fallback

# ----- TTS and merge -----

async def synthesize_text_to_mp3_chunks(text: str, default_lang: str, tmp_dir: Path, max_words: int = 220) -> List[Path]:
    sentences = split_text_into_sentences(text)
    chunks = pack_sentences_into_chunks(sentences, max_words=max_words)
    mp3_parts: List[Path] = []
    for i, chunk in enumerate(chunks):
        lang = detect_lang_safe(chunk, fallback=default_lang)
        voice = pick_voice_for_lang(lang)
        out = tmp_dir / f"part_{i:03}.mp3"
        print(f"[TTS] synth chunk {i+1}/{len(chunks)} lang={lang} voice={voice} -> {out}")
        communicator = edge_tts.Communicate(chunk, voice)
        await communicator.save(str(out))
        mp3_parts.append(out)
    return mp3_parts

def merge_mp3_parts(parts: List[Path], out_file: Path):
    concat_txt = TMP_DIR / "concat_list.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for p in parts:
            f.write(f"file '{p.resolve()}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(out_file)]
    print("[ffmpeg] running:", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ----- Zola index.md writer (Choice A layout: dual audio) -----

def write_zola_index_md(md_path: Path, title: str, slug: str, original_text: str, metadata: dict):
    title_escaped = title.replace('"', '\\"')
    front_lines = [
        "+++",
        f'title = "{title_escaped}"',
        f'slug = "{slug}"',
        f'date = "{datetime.now().isoformat()}"',
        'authors = ["auto"]'
    ]
    tags = metadata.get("tags") or []
    if tags:
        tag_list = ", ".join(f'"{t}"' for t in tags[:20])
        front_lines.append(f"tags = [{tag_list}]")
    category = metadata.get("category")
    if category:
        front_lines.append(f'categories = ["{category}"]')
    front_lines.append("+++\n")
    front_text = "\n".join(front_lines)

    # Dual audio blocks as requested (Choice A)
    audio_block = (
        "## 🎧 Listen: Original Article (Raw)\n\n"
        '<audio controls style="width: 100%;">\n'
        '  <source src="article.mp3" type="audio/mpeg">\n'
        '  Your browser does not support the audio element.\n'
        '</audio>\n\n'
        "## 🎙️ Listen: AI Narration (Structured Summary)\n\n"
        '<audio controls style="width: 100%;">\n'
        '  <source src="narration.mp3" type="audio/mpeg">\n'
        '  Your browser does not support the audio element.\n'
        '</audio>\n\n'
    )

    excerpt = metadata.get("excerpt", "")
    tl = metadata.get("tl_dr", []) or []
    tl_block = ""
    if tl:
        tl_block = "\n**TL;DR**\n\n" + "\n".join(f"- {s}" for s in tl) + "\n\n"
    takeaways = metadata.get("key_takeaways", []) or []
    takeaways_block = ""
    if takeaways:
        takeaways_block = "\n**Key takeaways**\n\n" + "\n".join(f"- {s}" for s in takeaways) + "\n\n"

    content = front_text + audio_block
    if excerpt:
        content += f"> {excerpt}\n\n"
    content += tl_block + takeaways_block + original_text

    md_path.write_text(content, encoding="utf-8")
    print("[md] wrote index.md:", md_path)

# ----- Main pipeline -----

async def process_file(input_path: Path, dry_run: bool = False):
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    original_text = input_path.read_text(encoding="utf-8").strip()
    if not original_text:
        raise ValueError("Input text is empty")

    # Title and slug
    title = generate_smart_title(original_text)
    slug = slugify(title)
    post_dir = BASE_CONTENT / slug
    post_dir.mkdir(parents=True, exist_ok=True)

    md_path = post_dir / "index.md"
    article_mp3 = post_dir / "article.mp3"
    narration_mp3 = post_dir / "narration.mp3"
    asset_txt = post_dir / "asset.txt"  # AI narration script
    asset_translated = post_dir / "asset.translated.txt"
    meta_json = post_dir / "asset.json"

    print(f"[post] title={title} slug={slug}")

    # Generate narration script (asset.txt)
    narration = generate_narration_script_ai(original_text, title=title)
    # If too short, expand using summary
    if len(narration.split()) < 30:
        summary = generate_smart_summary(original_text)
        if GROQ_API_KEY:
            try:
                system = ("You are a podcast host writer. Turn the summary into a natural narration script of 150-350 words.")
                user = f"SUMMARY:\n{summary}\n\nINSTRUCTIONS: Output only the narration script."
                narration = call_groq_chat(system, user, max_tokens=700, temperature=0.35).strip()
            except Exception as e:
                print("[GROQ] narration expand failed:", e)
        else:
            narration = "Hello. " + re.sub(r"\s+", " ", summary)

    asset_txt.write_text(narration, encoding="utf-8")
    print("[asset.txt] narration written, words:", len(narration.split()))

    # Metadata
    overall_lang = detect_lang_safe(original_text)
    metadata = generate_advanced_metadata(original_text, title, overall_lang)
    metadata.update({
        "title": title,
        "slug": slug,
        "lang": overall_lang,
        "read_time_minutes": metadata.get("read_time_minutes") or estimate_read_time(original_text),
        "narration_word_count": len(narration.split())
    })

    # Write translated excerpt if available
    translations = metadata.get("translations", {}) or {}
    excerpt_en = translations.get("excerpt_en") or translations.get("excerpt_orig") or ""
    if excerpt_en:
        asset_translated.write_text(excerpt_en, encoding="utf-8")
        print("[translate] wrote asset.translated.txt")

    # If dry-run: write md + metadata and exit (no TTS)
    if dry_run:
        # Write index.md with audio placeholders (files won't exist)
        write_zola_index_md(md_path, title, slug, original_text, metadata)
        meta_json.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        print("[dry-run] Completed. Skipping TTS and ffmpeg.")
        return

    # TTS: produce article.mp3 (raw original) and narration.mp3 (asset.txt)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    # 1) article.mp3 (TTS of original_text)
    print("[TTS] Generating article.mp3 (raw original)")
    article_parts = await synthesize_text_to_mp3_chunks(original_text, overall_lang, TMP_DIR, max_words=220)
    try:
        merge_mp3_parts(article_parts, article_mp3)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffmpeg merge failed for article.mp3: {e}")
    print("[TTS] article.mp3 generated:", article_mp3)

    # 2) narration.mp3 (TTS of narration script)
    print("[TTS] Generating narration.mp3 (AI narration)")
    narration_parts = await synthesize_text_to_mp3_chunks(narration, overall_lang, TMP_DIR, max_words=200)
    try:
        merge_mp3_parts(narration_parts, narration_mp3)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffmpeg merge failed for narration.mp3: {e}")
    print("[TTS] narration.mp3 generated:", narration_mp3)

    # Save metadata and index.md
    meta_json.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[meta] written:", meta_json)
    write_zola_index_md(md_path, title, slug, original_text, metadata)

    # Cleanup temporary parts
    for p in article_parts + narration_parts:
        try:
            p.unlink()
        except Exception:
            pass
    concat_file = TMP_DIR / "concat_list.txt"
    if concat_file.exists():
        concat_file.unlink()

    print("[done] Created post at:", post_dir)

# ----- CLI -----

def main():
    parser = argparse.ArgumentParser(description="Text -> Dual Audio Zola post pipeline")
    parser.add_argument("input", nargs="?", default="input.txt", help="input text file (default input.txt)")
    parser.add_argument("--dry-run", action="store_true", help="generate assets (asset.txt, md, json) but skip TTS & ffmpeg")
    args = parser.parse_args()
    input_path = Path(args.input)
    try:
        asyncio.run(process_file(input_path, dry_run=args.dry_run))
    except Exception as e:
        print("[error]", e)

if __name__ == "__main__":
    main()
