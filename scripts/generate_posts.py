import os
from datetime import datetime
import requests
import argparse
import json

# Define where to put generated markdown files
CONTENT_DIR = os.path.join("..", "content", "blog")

def fetch_posts(limit):
    """Fetch a specified number of posts from the API."""
    try:
        response = requests.get(f"https://jsonplaceholder.typicode.com/posts?_limit={limit}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching posts: {e}")
        return []

def generate_slug(title):
    """Generate a URL-friendly slug from a title."""
    return title.lower().replace(" ", "-").replace("/", "-")

def ensure_dir(path):
    """Ensure the output directory exists."""
    if not os.path.exists(path):
        os.makedirs(path)

def generate_markdown(post):
    """Generate a markdown file for a single post."""
    slug = generate_slug(post['title'])
    filename = os.path.join(CONTENT_DIR, f"{slug}.md")
    
    # Create a summary from the first 100 characters of the body
    summary = post['body'][:100].replace('\n', ' ') + "..."
    
    front_matter = f"""+++
title = "{post['title']}"
date = "{datetime.now().strftime('%Y-%m-%d')}"
summary = "{summary}"
+++

{post['body']}
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(front_matter)
    print(f"✅ Created: {filename}")

def main():
    """Main function to generate posts."""
    parser = argparse.ArgumentParser(description="Generate blog posts from a placeholder API.")
    parser.add_argument("-n", "--number", type=int, default=5, help="Number of posts to generate.")
    args = parser.parse_args()

    ensure_dir(CONTENT_DIR)
    posts = fetch_posts(args.number)
    
    if not posts:
        print("No posts to generate.")
        return
        
    for post in posts:
        generate_markdown(post)

if __name__ == "__main__":
    main()
