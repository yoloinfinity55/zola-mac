#!/usr/bin/env python3
"""
fix_thumbnails.py
-----------------
A script to fix existing thumbnails by re-downloading and cropping them to a 16:9 aspect ratio,
adhering to the new content structure where each post has its own folder.
"""

import os
import toml
from pathlib import Path
from generate_posts_v2 import download_thumbnail, logger

CONTENT_DIR = "content/blog"

def fix_existing_thumbnails():
    """
    Iterates through all post directories, finds the index.md,
    extracts the youtube_id, and re-downloads the thumbnail as asset.jpg.
    """
    logger.info("Starting to fix existing thumbnails with the new directory structure...")
    
    content_path = Path(CONTENT_DIR)
    # Look for index.md files in subdirectories
    for md_file in content_path.glob("**/index.md"):
        if md_file.is_file():
            post_dir = md_file.parent
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Find the end of the frontmatter
                frontmatter_end = content.find("+++", 3)
                if frontmatter_end != -1:
                    frontmatter_str = content[3:frontmatter_end].strip()
                    frontmatter = toml.loads(frontmatter_str)
                    
                    if "extra" in frontmatter and "youtube_id" in frontmatter["extra"]:
                        youtube_id = frontmatter["extra"]["youtube_id"]
                        thumb_filename = post_dir / "asset.jpg"
                        
                        logger.info(f"Processing {post_dir.name}...")
                        logger.info(f"  - YouTube ID: {youtube_id}")
                        logger.info(f"  - Thumbnail Path: {thumb_filename}")
                        
                        # Re-download and crop the thumbnail
                        download_thumbnail(youtube_id, str(thumb_filename))
                    else:
                        logger.warning(f"Skipping {md_file.name}: youtube_id not found in frontmatter.")
                else:
                    logger.warning(f"Skipping {md_file.name}: frontmatter not found.")
            except Exception as e:
                logger.error(f"Error processing {md_file.name}: {e}")

    logger.info("Finished fixing thumbnails.")

if __name__ == "__main__":
    fix_existing_thumbnails()
