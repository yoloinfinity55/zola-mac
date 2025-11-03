#!/usr/bin/env python3
import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional

try:
    from slugify import slugify
    import yt_dlp
except ImportError:
    print("Error: Missing required dependencies. Please install them using:")
    print(f"pip install -r {os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')}")
    sys.exit(1)


class PostGenerator:
    def __init__(self, content_dir: str = "content", post_subdir: Optional[str] = None, overwrite: bool = False, verbose: bool = False):
        self.content_dir = content_dir
        self.post_subdir = post_subdir
        self.overwrite = overwrite
        self.verbose = verbose

        if not os.path.exists(content_dir):
            os.makedirs(content_dir)
            if self.verbose:
                print(f"Created content directory: {content_dir}")

        if self.post_subdir:
            self.full_post_dir = os.path.join(self.content_dir, self.post_subdir)
            if not os.path.exists(self.full_post_dir):
                os.makedirs(self.full_post_dir)
                if self.verbose:
                    print(f"Created post subdirectory: {self.full_post_dir}")
        else:
            self.full_post_dir = self.content_dir

    def log(self, message: str):
        if self.verbose:
            print(message)

    def fetch_youtube_info(self, url: str) -> Optional[Dict]:
        """Fetch metadata from a YouTube video URL using yt-dlp."""
        self.log(f"Fetching YouTube info for URL: {url}")
        try:
            # Suppress yt-dlp warnings by redirecting its logger to null
            logging.getLogger("yt_dlp").setLevel(logging.ERROR)
            
            ydl_opts = {"quiet": True, "extract_flat": False, "skip_download": True, "no_warnings": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except yt_dlp.utils.DownloadError as e:
            print(f"Error fetching YouTube info: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}", file=sys.stderr)
            return None

    def _escape_toml_string(self, value: str) -> str:
        """Escapes a string for use in TOML."""
        return value.replace("\\", "\\\\").replace('"', '\\"')

    def generate_front_matter(
        self,
        title: str,
        date: Optional[str] = None,
        summary: Optional[str] = None,
        tags: Optional[List[str]] = None,
        author: Optional[str] = None,
        extra: Optional[Dict] = None,
    ) -> str:
        """Generate TOML-style front matter for Zola posts."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        lines = [
            "+++",
            f'title = "{self._escape_toml_string(title)}"',
            f'date = "{date}"',
        ]

        if summary:
            lines.append(f'summary = "{self._escape_toml_string(summary)}"')

        if tags:
            tags_str = ", ".join(f'"{self._escape_toml_string(t)}"' for t in tags)
            lines.append(f"tags = [{tags_str}]")

        if author:
            lines.append(f'author = "{self._escape_toml_string(author)}"')

        if extra:
            clean = {k: v for k, v in extra.items() if v is not None}
            if clean:
                lines.append("\n[extra]")
                for k, v in clean.items():
                    if isinstance(v, str):
                        lines.append(f'{k} = "{self._escape_toml_string(v)}"')
                    elif isinstance(v, bool):
                        lines.append(f"{k} = {str(v).lower()}")
                    else:
                        lines.append(f"{k} = {json.dumps(v)}")

        lines.append("+++\n")
        return "\n".join(lines)

    def save_post(self, filename: str, content: str):
        """Save markdown post to the content directory."""
        path = os.path.join(self.full_post_dir, filename)
        if os.path.exists(path) and not self.overwrite:
            print(f"File already exists, skipping: {path}")
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        self.log(f"Saved post: {path}")

    def create_post_from_youtube(self, url: str):
        """Create a Zola post from a YouTube video."""
        info = self.fetch_youtube_info(url)
        if not info:
            print("Failed to fetch YouTube metadata.", file=sys.stderr)
            return

        title = info.get("title", "Untitled Video")
        description = info.get("description", "")
        
        # Find the first non-empty line of the description for the summary.
        summary = next((line for line in description.split('\n') if line.strip()), "")

        upload_date = info.get("upload_date")
        date = datetime.strptime(upload_date, "%Y%m%d").strftime("%Y-%m-%d") if upload_date else None
        tags = info.get("tags", [])
        author = info.get("uploader")
        video_id = info.get("id")
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        front_matter = self.generate_front_matter(
            title=title,
            date=date,
            summary=summary,
            tags=tags,
            author=author,
            extra={"youtube_url": video_url, "duration": info.get("duration")},
        )

        content = f"""{front_matter}
<div class="youtube-embed">
<iframe width="560" height="315" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
</div>

{description}

[Watch on YouTube]({video_url})
"""
        filename = f"{slugify(title)}.md"
        self.save_post(filename, content)
        print(f"✅ Generated post: {filename}")


def main():
    parser = argparse.ArgumentParser(description="Generate Zola markdown posts.")
    parser.add_argument("--youtube", help="YouTube video URL")
    parser.add_argument("--title", help="Custom title")
    parser.add_argument("--summary", help="Custom summary")
    parser.add_argument("--tags", nargs="+", help="List of tags")
    parser.add_argument("--date", help="Publication date")
    parser.add_argument("--content-dir", default="content", help="Zola content directory")
    parser.add_argument("--post-subdir", default="blog", help="Subdirectory within content_dir to save posts (e.g., 'blog')")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()
    generator = PostGenerator(args.content_dir, args.post_subdir, args.overwrite, args.verbose)

    if args.youtube:
        generator.create_post_from_youtube(args.youtube)
    else:
        title = args.title or "Untitled Post"
        front_matter = generator.generate_front_matter(
            title=title,
            date=args.date,
            summary=args.summary,
            tags=args.tags,
        )
        filename = f"{slugify(title)}.md"
        generator.save_post(filename, f"{front_matter}\n{args.summary or ''}")
        print(f"✅ Generated manual post: {filename}")


if __name__ == "__main__":
    main()
