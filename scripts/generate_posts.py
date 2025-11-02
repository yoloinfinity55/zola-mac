#!/usr/bin/env python3
"""
Enhanced Post Generator for Zola-mac
Generates blog posts from APIs, custom content, or YouTube videos.
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
import yt_dlp  # yt-dlp for robust YouTube metadata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class YouTubeExtractor:
    """Extract and fetch video information from YouTube using yt-dlp."""
    
    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        patterns = [
            r'(?:v=|/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed/)([0-9A-Za-z_-]{11})',
            r'(?:watch\?v=)([0-9A-Za-z_-]{11})',
            r'^([0-9A-Za-z_-]{11})$'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def get_video_info(url: str) -> Optional[Dict]:
        try:
            ydl_opts = {'quiet': True, 'skip_download': True, 'no_warnings': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    "video_id": info.get("id"),
                    "title": info.get("title", "Untitled Video"),
                    "author": info.get("uploader", "Unknown"),
                    "thumbnail_url": info.get("thumbnail"),
                    "description": info.get("description", ""),
                    "url": info.get("webpage_url", url),
                    "duration": info.get("duration"),
                    "view_count": info.get("view_count"),
                    "upload_date": info.get("upload_date"),
                }
        except Exception as e:
            logger.error(f"Failed to fetch YouTube video info using yt-dlp: {e}")
            return None

    @staticmethod
    def generate_post_content(video_info: Dict, include_embed: bool = True) -> str:
        content_parts = []
        if video_info.get('thumbnail_url'):
            content_parts.append(f"![{video_info['title']}]({video_info['thumbnail_url']})\n")
        if include_embed:
            content_parts.append("## Watch Video\n")
            content_parts.append(
                f'<iframe width="100%" height="400" '
                f'src="https://www.youtube.com/embed/{video_info["video_id"]}" '
                f'frameborder="0" allowfullscreen></iframe>\n'
            )
        if video_info.get('description'):
            content_parts.append("## About This Video\n")
            content_parts.append(f"{video_info['description']}\n")
        content_parts.append("## Video Details\n")
        details = []
        if video_info.get('author'):
            details.append(f"- **Channel**: {video_info['author']}")
        if video_info.get('view_count'):
            details.append(f"- **Views**: {video_info['view_count']:,}")
        if video_info.get('duration'):
            minutes = video_info['duration'] // 60
            seconds = video_info['duration'] % 60
            details.append(f"- **Duration**: {minutes}:{seconds:02d}")
        details.append(f"- **Watch on YouTube**: [{video_info['url']}]({video_info['url']})")
        content_parts.append('\n'.join(details))
        return '\n\n'.join(content_parts)


class PostGenerator:
    """Generates Zola-compatible blog posts with automation."""
    
    def __init__(self, content_dir: str = "content/blog", manifest_file: str = ".generated_manifest.json"):
        self.content_dir = Path(content_dir)
        self.content_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = Path(manifest_file)
        self.manifest = self._load_manifest()
        self.youtube = YouTubeExtractor()
    
    def _load_manifest(self) -> Dict:
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning("Invalid manifest file, creating new one")
        return {"posts": {}, "youtube_videos": {}, "generated_at": None}
    
    def _save_manifest(self):
        self.manifest["generated_at"] = datetime.now().isoformat()
        with open(self.manifest_file, 'w') as f:
            json.dump(self.manifest, f, indent=2)
    
    @staticmethod
    def slugify(text: str) -> str:
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text.strip('-')
    
    @staticmethod
    def validate_post_data(data: Dict) -> bool:
        required = ['title', 'content']
        if not all(key in data for key in required):
            logger.error(f"Missing required fields: {required}")
            return False
        if len(data['title']) == 0:
            logger.error("Title cannot be empty")
            return False
        if len(data['content']) < 50:
            logger.warning("Content is very short (< 50 chars)")
        return True
    
    def generate_front_matter(
        self,
        title: str,
        date: Optional[str] = None,
        summary: Optional[str] = None,
        tags: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        draft: bool = False,
        author: Optional[str] = None,
        extra: Optional[Dict] = None
    ) -> str:
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # TOML-safe: triple quotes for multiline strings
        front_matter = f'+++\ntitle = """{title}"""\ndate = "{date}"\n'
        if summary:
            safe_summary = summary.replace('"""', '\\"\\"\\"')
            front_matter += f'summary = """{safe_summary}"""\n'
        if tags:
            tags_str = ', '.join([f'"{tag}"' for tag in tags])
            front_matter += f'tags = [{tags_str}]\n'
        if categories:
            cats_str = ', '.join([f'"{cat}"' for cat in categories])
            front_matter += f'categories = [{cats_str}]\n'
        if author:
            front_matter += f'author = """{author}"""\n'
        if draft:
            front_matter += 'draft = true\n'
        if extra:
            front_matter += '\n[extra]\n'
            for key, value in extra.items():
                if isinstance(value, str):
                    front_matter += f'{key} = """{value}"""\n'
                elif isinstance(value, bool):
                    front_matter += f'{key} = {str(value).lower()}\n'
                else:
                    front_matter += f'{key} = {value}\n'
        front_matter += "+++\n\n"
        return front_matter
    
    def create_post(self, title: str, content: str, filename: Optional[str] = None, **kwargs) -> Optional[Path]:
        if not self.validate_post_data({'title': title, 'content': content}):
            return None
        if filename is None:
            slug = self.slugify(title)
            filename = f"{slug}.md"
        filepath = self.content_dir / filename
        if filepath.exists():
            logger.warning(f"Post already exists: {filepath}")
            if not kwargs.get('overwrite', False):
                logger.info("Skipping (use --overwrite to replace)")
                return None
        front_matter = self.generate_front_matter(title, **kwargs)
        full_content = front_matter + content
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_content)
            logger.info(f"✓ Created post: {filepath}")
            self.manifest["posts"][str(filepath)] = {
                "title": title,
                "created_at": datetime.now().isoformat(),
                "filename": filename
            }
            self._save_manifest()
            return filepath
        except Exception as e:
            logger.error(f"Failed to write post: {e}")
            return None

    def create_youtube_post(self, youtube_url, **kwargs):
        logger.info(f"Fetching info for video: {youtube_url}")
        video_info = YouTubeExtractor.get_video_info(youtube_url)
        if not video_info:
            logger.error("Failed to retrieve YouTube video info.")
            return None

        title = kwargs.get('custom_title') or video_info["title"]
        summary = kwargs.get('custom_summary') or (video_info["description"][:500] if video_info.get("description") else "")
        tags = kwargs.get('tags') or ["youtube", "video", "automation"]

        extra = {
            "video_url": youtube_url,
            "thumbnail": video_info["thumbnail_url"],
            "published": video_info.get("upload_date"),
        }
        extra.update(kwargs.get('extra', {}))

        content = f"""
<!-- Post Header -->
![{title}]({video_info["thumbnail_url"]}){{# This keeps Zola markdown valid and scalable }}

<div class="video-meta" style="margin-top: 1em; margin-bottom: 1em;">
**Author:** {video_info["author"]}  \n
**Published:** {video_info.get("upload_date") or "Unknown"}  
</div>

---

## About This Video
{video_info["description"] or "No description available."}

## Tags
- youtube
- video
- automation

## Watch Video
<iframe width="100%" height="400" 
        src="https://www.youtube.com/embed/{video_info["video_id"]}" 
        frameborder="0" allowfullscreen style="margin-top:1em;"></iframe>
"""





        kwargs_copy = kwargs.copy()
        for key in ["summary", "tags", "author", "extra", "overwrite", "youtube_url", "include_embed", "custom_title", "custom_summary"]:
            kwargs_copy.pop(key, None)

        result = self.create_post(
            title=title,
            content=content,
            summary=summary,
            tags=tags,
            author=video_info.get("author"),
            extra=extra,
            **kwargs_copy
        )

        if result:
            logger.info(f"✓ YouTube post created successfully: {title}")
        return result
    
    def fetch_from_api(self, api_url: str, count: int = 5, **post_kwargs) -> int:
        try:
            logger.info(f"Fetching {count} posts from {api_url}")
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            posts = response.json()[:count]
            created = 0
            for post in posts:
                title = post.get('title', 'Untitled')
                body = post.get('body', '')
                summary = body.split('.')[0][:150] if body else None
                result = self.create_post(title=title, content=body, summary=summary, **post_kwargs)
                if result:
                    created += 1
            logger.info(f"✓ Successfully created {created}/{count} posts")
            return created
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return 0


def main():
    parser = argparse.ArgumentParser(
        description="Generate blog posts for Zola-mac",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--title', help='Post title')
    parser.add_argument('--content', help='Post content')
    parser.add_argument('--filename', help='Custom filename')
    parser.add_argument('--youtube', '--yt', help='YouTube video URL')
    parser.add_argument('--no-embed', action='store_true', help='Do not include video embed')
    parser.add_argument('--date', help='Post date (YYYY-MM-DD)')
    parser.add_argument('--summary', help='Post summary')
    parser.add_argument('--tags', nargs='+', help='Post tags')
    parser.add_argument('--categories', nargs='+', help='Post categories')
    parser.add_argument('--author', help='Post author')
    parser.add_argument('--draft', action='store_true', help='Mark as draft')
    parser.add_argument('--fetch-api', action='store_true', help='Fetch from API')
    parser.add_argument('--api-url', default='https://jsonplaceholder.typicode.com/posts', help='API endpoint')
    parser.add_argument('--count', type=int, default=5, help='Number of posts to fetch')
    parser.add_argument('--content-dir', default='content/blog', help='Content directory')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing posts')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    generator = PostGenerator(content_dir=args.content_dir)
    post_kwargs = {
        'date': args.date,
        'summary': args.summary,
        'tags': args.tags,
        'categories': args.categories,
        'author': args.author,
        'draft': args.draft,
        'overwrite': args.overwrite
    }

    if args.youtube:
        result = generator.create_youtube_post(
            youtube_url=args.youtube,
            include_embed=not args.no_embed,
            custom_title=args.title,
            custom_summary=args.summary,
            **post_kwargs
        )
        sys.exit(0 if result else 1)
    elif args.fetch_api:
        created = generator.fetch_from_api(args.api_url, args.count, **post_kwargs)
        sys.exit(0 if created > 0 else 1)
    elif args.title and args.content:
        result = generator.create_post(title=args.title, content=args.content, filename=args.filename, **post_kwargs)
        sys.exit(0 if result else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
