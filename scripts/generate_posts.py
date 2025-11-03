#!/usr/bin/env python3
import argparse
import json
import logging
import os
import sys
import re
import urllib.request
from datetime import datetime
from typing import List, Dict, Optional
from collections import Counter
import math

try:
    from slugify import slugify
    import yt_dlp
except ImportError:
    print("Error: Missing required dependencies. Please install them using:")
    print(f"pip install python-slugify yt-dlp")
    sys.exit(1)


class PostGenerator:
    def __init__(self, content_dir="content", post_subdir=None, overwrite=False, verbose=False):
        self.content_dir = content_dir
        self.post_subdir = post_subdir
        self.overwrite = overwrite
        self.verbose = verbose

        os.makedirs(content_dir, exist_ok=True)
        self.full_post_dir = os.path.join(content_dir, post_subdir) if post_subdir else content_dir
        os.makedirs(self.full_post_dir, exist_ok=True)

    def log(self, msg: str):
        if self.verbose:
            print(msg)

    # ------------------------------------------------------------
    # YouTube metadata
    # ------------------------------------------------------------
    def fetch_youtube_info(self, url: str) -> Optional[Dict]:
        """Fetch metadata (and transcript if available) from YouTube."""
        self.log(f"Fetching YouTube info for: {url}")
        try:
            logging.getLogger("yt_dlp").setLevel(logging.ERROR)
            ydl_opts = {
                "quiet": True,
                "skip_download": True,
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": ["en"],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                info["transcript_text"] = self.extract_transcript(info)
                return info
        except Exception as e:
            print(f"Error fetching YouTube info: {e}", file=sys.stderr)
            return None

    # ------------------------------------------------------------
    # Transcript parsing
    # ------------------------------------------------------------
    def extract_transcript(self, info: Dict) -> Optional[str]:
        captions = info.get("subtitles") or info.get("automatic_captions") or {}
        for lang in ["en", "en-US", "en-GB"]:
            if lang in captions:
                sub = captions[lang][0]
                url = sub.get("url")
                if not url:
                    continue
                try:
                    raw = urllib.request.urlopen(url).read().decode("utf-8")
                    return self.clean_transcript(raw)
                except Exception:
                    return None
        return None

    def clean_transcript(self, raw_vtt: str) -> str:
        """Convert VTT to clean, narrative paragraphs."""
        blocks = []
        current_text = []
        last_time = 0.0

        for line in raw_vtt.splitlines():
            if line.startswith("WEBVTT") or not line.strip():
                continue

            # Timestamp pattern
            time_match = re.match(r"(\d{2}):(\d{2}):(\d{2})\.\d+\s-->\s(\d{2}):(\d{2}):(\d{2})", line)
            if time_match:
                h, m, s = map(int, time_match.groups()[:3])
                start_sec = h * 3600 + m * 60 + s
                if start_sec - last_time > 3 and current_text:
                    blocks.append(" ".join(current_text))
                    current_text = []
                last_time = start_sec
                continue

            text = re.sub(r"<[^>]+>", "", line).strip()
            text = re.sub(r"^\d+$", "", text)
            if text:
                current_text.append(text)

        if current_text:
            blocks.append(" ".join(current_text))

        formatted = []
        buffer = ""
        for para in blocks:
            buffer += " " + para
            if re.search(r"[.!?]$", para.strip()):
                formatted.append(buffer.strip())
                buffer = ""
        if buffer.strip():
            formatted.append(buffer.strip())

        return "\n\n".join(formatted)

    # ------------------------------------------------------------
    # Summary extraction
    # ------------------------------------------------------------
    def summarize_transcript(self, transcript: str, num_sentences: int = 3) -> str:
        """Generate an AI-like summary using keyword scoring."""
        if not transcript:
            return ""

        sentences = re.split(r'(?<=[.!?]) +', transcript)
        if len(sentences) <= num_sentences:
            return " ".join(sentences)

        words = re.findall(r'\b[a-zA-Z]{3,}\b', transcript.lower())
        freq = Counter(words)
        total = sum(freq.values())

        # Normalize frequencies
        for w in freq:
            freq[w] /= total

        # Score sentences by keyword frequency
        sentence_scores = {}
        for sent in sentences:
            words_in_sent = re.findall(r'\b[a-zA-Z]{3,}\b', sent.lower())
            score = sum(freq[w] for w in words_in_sent if w in freq)
            if len(words_in_sent) > 0:
                sentence_scores[sent] = score / len(words_in_sent)

        # Pick top N sentences
        top_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:num_sentences]
        summary = " ".join(sorted(top_sentences, key=lambda s: sentences.index(s)))

        return summary.strip()

    # ------------------------------------------------------------
    # Front matter + thumbnail
    # ------------------------------------------------------------
    def _escape(self, s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')

    def generate_front_matter(self, title, date=None, summary=None, tags=None, author=None, extra=None):
        date = date or datetime.now().strftime("%Y-%m-%d")
        lines = [
            "+++",
            f'title = "{self._escape(title)}"',
            f'date = "{date}"',
        ]
        if summary:
            lines.append(f'summary = "{self._escape(summary)}"')
        if tags:
            lines.append(f"tags = [{', '.join(f'\"{self._escape(t)}\"' for t in tags)}]")
        if author:
            lines.append(f'author = "{self._escape(author)}"')
        if extra:
            lines.append("\n[extra]")
            for k, v in extra.items():
                if isinstance(v, str):
                    lines.append(f'{k} = "{self._escape(v)}"')
                else:
                    lines.append(f"{k} = {json.dumps(v)}")
        lines.append("+++\n")
        return "\n".join(lines)

    def download_thumbnail(self, info: Dict, dest_folder: str) -> Optional[str]:
        thumb_url = info.get("thumbnail")
        if not thumb_url:
            return None
        try:
            filename = slugify(info.get("title", "thumbnail")) + os.path.splitext(thumb_url)[-1]
            local_path = os.path.join(dest_folder, filename)
            urllib.request.urlretrieve(thumb_url, local_path)
            return os.path.relpath(local_path, start=self.content_dir)
        except Exception as e:
            self.log(f"Thumbnail download failed: {e}")
            return None

    # ------------------------------------------------------------
    # File writer
    # ------------------------------------------------------------
    def save_post(self, filename, content):
        path = os.path.join(self.full_post_dir, filename)
        if os.path.exists(path) and not self.overwrite:
            print(f"⚠️  File exists, skipping: {path}")
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Saved post: {path}")

    def create_post_from_youtube(self, url):
        info = self.fetch_youtube_info(url)
        if not info:
            print("Failed to fetch metadata.", file=sys.stderr)
            return

        title = info.get("title", "Untitled")
        description = info.get("description", "").strip()
        upload_date = info.get("upload_date")
        date = datetime.strptime(upload_date, "%Y%m%d").strftime("%Y-%m-%d") if upload_date else None
        tags = info.get("tags", [])
        author = info.get("uploader")
        video_id = info.get("id")
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        transcript = info.get("transcript_text")

        # AI-style summary
        summary_text = self.summarize_transcript(transcript)

        # Thumbnail
        thumbnail_rel_path = self.download_thumbnail(info, self.full_post_dir)

        front = self.generate_front_matter(
            title=title,
            date=date,
            summary=summary_text or description.split("\n")[0],
            tags=tags,
            author=author,
            extra={
                "youtube_url": video_url,
                "duration": info.get("duration"),
                "thumbnail": thumbnail_rel_path or info.get("thumbnail"),
            },
        )

        # Build Markdown
        image_block = f"![{title}]({thumbnail_rel_path or info.get('thumbnail')})\n\n" if (thumbnail_rel_path or info.get('thumbnail')) else ""
        summary_section = f"\n## Summary\n\n{summary_text}\n" if summary_text else ""
        transcript_section = f"\n## Transcript\n\n{transcript}" if transcript else ""

        content = f"""{front}
{image_block}
<div class="youtube-embed">
<iframe width="560" height="315" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen></iframe>
</div>

[Watch on YouTube]({video_url})

{summary_section}
{transcript_section}
"""
        filename = f"{slugify(title)}.md"
        self.save_post(filename, content)


def main():
    parser = argparse.ArgumentParser(description="Generate Markdown posts from YouTube videos (with summary + transcript).")
    parser.add_argument("--youtube", help="YouTube video URL")
    parser.add_argument("--content-dir", default="content")
    parser.add_argument("--post-subdir", default="blog")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    generator = PostGenerator(args.content_dir, args.post_subdir, args.overwrite, args.verbose)
    if args.youtube:
        generator.create_post_from_youtube(args.youtube)
    else:
        print("Usage: --youtube <URL>")


if __name__ == "__main__":
    main()
