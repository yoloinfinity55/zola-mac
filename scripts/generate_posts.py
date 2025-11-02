#!/usr/bin/env python3
"""
Zola-mac Post Generator – YouTube → Zola blog post (exact layout)
"""
import argparse
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
import yt_dlp
from slugify import slugify
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# YouTube Helper
# --------------------------------------------------------------------------- #
class YouTubeExtractor:
    @staticmethod
    def _best_thumbnail(thumbnails: list) -> Optional[str]:
        """Return maxresdefault.webp if available, else highest resolution."""
        if not thumbnails:
            return None
        # Prefer webp for smaller size + quality
        for t in thumbnails:
            if t.get("id") == "maxres" and t.get("url", "").endswith(".webp"):
                return t["url"]
        # Fallback to any maxres
        for t in thumbnails:
            if t.get("id") == "maxres":
                return t["url"]
        # Fallback to highest resolution
        return max(thumbnails, key=lambda x: x.get("width", 0)).get("url")

    @staticmethod
    def get_video_info(url: str) -> Optional[Dict]:
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "extract_flat": False,  # Need thumbnails dict
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                info = ydl.extract_info(url, download=False)
                if not info:
                    return None

                thumbnails = info.get("thumbnails") or []
                return {
                    "video_id": info.get("id"),
                    "title": info.get("title", "Untitled Video"),
                    "author": info.get("uploader", "Unknown"),
                    "thumbnail_url": YouTubeExtractor._best_thumbnail(thumbnails),
                    "description": info.get("description", ""),
                    "url": info.get("webpage_url", url),
                    "upload_date": info.get("upload_date"),  # YYYYMMDD
                }
        except Exception as e:
            logger.error(f"yt-dlp error: {e}")
            return None


# --------------------------------------------------------------------------- #
# Post Generator
# --------------------------------------------------------------------------- #
class PostGenerator:
    def __init__(self, content_dir: str = "content/blog", manifest_file: str = ".generated_manifest.json"):
        self.content_dir = Path(content_dir)
        self.content_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = Path(manifest_file)
        self.manifest = self._load_manifest()

        # HTTP session with retry
        self.session = requests.Session()
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.mount("http://", HTTPAdapter(max_retries=retry))

    # ------------------------------------------------------------------- #
    # Manifest
    # ------------------------------------------------------------------- #
    def _load_manifest(self) -> Dict:
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                logger.warning("Corrupted manifest – starting fresh")
        return {"posts": {}, "youtube_videos": {}, "generated_at": None}

    def _save_manifest(self):
        self.manifest["generated_at"] = datetime.now().isoformat()
        try:
            with open(self.manifest_file, "w", encoding="utf-8") as f:
                json.dump(self.manifest, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save manifest: {e}")

    # ------------------------------------------------------------------- #
    # Front Matter (Zola TOML – no null!)
    # ------------------------------------------------------------------- #
    def generate_front_matter(
        self,
        title: str,
        date: Optional[str] = None,
        summary: Optional[str] = None,
        tags: Optional[List[str]] = None,
        author: Optional[str] = None,
        extra: Optional[Dict] = None,
    ) -> str:
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        lines = [
            "+++",
            f'title = """{title.replace('"""', r"\\\"""")}"""',
            f'date = "{date}"',
        ]

        if summary:
            safe = summary.replace('"""', r"\\\"""")
            lines.append(f'summary = """{safe}"""')

        if tags:
            tags_str = ", ".join(f'"{t}"' for t in tags)
            lines.append(f"tags = [{tags_str}]")

        if author:
            lines.append(f'author = """{author.replace('"""', r"\\\"""")}"""')

        # Clean extra: remove None values
        if extra:
            clean = {k: v for k, v in extra.items() if v is not None}
            if clean:
                lines.append("\n[extra]")
                for k, v in clean.items():
                    if isinstance(v, str):
                        safe_v = v.replace('"""', r"\\\"""")
                        lines.append(f'{k} = """{safe_v}"""')
                    elif isinstance(v, bool):
                        lines.append(f"{k} = {str(v).lower()}")
                    else:
                        lines.append(f"{k} = {json.dumps(v)}")

        lines.append("+++\n")
        return "\n".join(lines)

    # ------------------------------------------------------------------- #
    # Create Post
    # ------------------------------------------------------------------- #
    def create_post(self, title: str, content: str, filename: Optional[str] = None, **kwargs) -> Optional[Path]:
        if filename is None:
            slug = slugify(title)
            filename = f"{slug}.md"

        filepath = self.content_dir / filename
        if filepath.exists() and not kwargs.get("overwrite"):
            logger.info(f"Skipping existing: {filepath}")
            return None

        front = self.generate_front_matter(title, **kwargs)
        full = front + content

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(full)
            logger.info(f"Created: {filepath}")

            self.manifest["posts"][str(filepath)] = {
                "title": title,
                "created_at": datetime.now().isoformat(),
                "filename": filename,
            }
            self._save_manifest()
            return filepath
        except Exception as e:
            logger.error(f"Write failed: {e}")
            return None

    # ------------------------------------------------------------------- #
    # YouTube → Zola Post (Exact Match)
    # ------------------------------------------------------------------- #
    def create_youtube_post(
        self,
        youtube_url: str,
        include_embed: bool = True,
        custom_title: Optional[str] = None,
        custom_summary: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs,
    ) -> Optional[Path]:
        logger.info(f"Processing YouTube: {youtube_url}")
        info = YouTubeExtractor.get_video_info(youtube_url)
        if not info:
            logger.error("Failed to extract video info")
            return None

        title = custom_title or info["title"]
        description = info["description"] or ""
        summary = custom_summary or (description[:500] + ("..." if len(description) > 500 else ""))

        # Tags
        final_tags = tags or ["youtube", "video", "automation"]

        # Extra
        extra: Dict = {
            "video_url": youtube_url,
            "published": info.get("upload_date"),
        }
        if info.get("thumbnail_url"):
            extra["thumbnail"] = info["thumbnail_url"]

        # Markdown content (exact match)
        thumb = info.get("thumbnail_url", "")
        content_lines = [
            f"<!-- Post Header -->",
            f"![{title}]({thumb}){{ # This keeps Zola markdown valid and scalable }}",
            '<div class="video-meta" style="margin-top: 1em; margin-bottom: 1em;">',
            f"**Author:** {info['author']}",
            f"**Published:** {info.get('upload_date') or 'Unknown'}",
            "</div>",
            "---",
            "## About This Video",
            description or "No description available.",
            "## Tags",
            *[f"- {t}" for t in final_tags],
        ]

        if include_embed:
            content_lines.extend(
                [
                    "## Watch Video",
                    f'<iframe width="100%" height="400"',
                    f'        src="https://www.youtube.com/embed/{info["video_id"]}"',
                    f'        frameborder="0" allowfullscreen style="margin-top:1em;"></iframe>',
                ]
            )

        content = "\n".join(content_lines) + "\n"

        # Clean kwargs
        clean_kwargs = {k: v for k, v in kwargs.items() if k not in ("tags", "extra", "author", "overwrite")}

        return self.create_post(
            title=title,
            content=content,
            summary=summary,
            tags=final_tags,
            author=info["author"],
            extra=extra,
            **clean_kwargs,
        )


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser(description="YouTube → Zola Blog Post")
    parser.add_argument("--youtube", "--yt", help="YouTube URL")
    parser.add_argument("--no-embed", action="store_true", help="Skip iframe")
    parser.add_argument("--title", help="Custom title")
    parser.add_argument("--summary", help="Custom summary")
    parser.add_argument("--tags", nargs="+", help="Tags")
    parser.add_argument("--date", help="Date (YYYY-MM-DD)")
    parser.add_argument("--content-dir", default="content/blog")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    gen = PostGenerator(content_dir=args.content_dir)

    if not args.youtube:
        parser.print_help()
        sys.exit(1)

    result = gen.create_youtube_post(
        youtube_url=args.youtube,
        include_embed=not args.no_embed,
        custom_title=args.title,
        custom_summary=args.summary,
        tags=args.tags,
        date=args.date,
        overwrite=args.overwrite,
    )
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()