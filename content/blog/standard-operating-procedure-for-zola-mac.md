+++
title = "Standard Operating Procedure for Zola-mac"
date = "2025-11-02"
summary = "This document outlines the standard operating procedure for the Zola-mac project."
+++

This document outlines the standard operating procedure for the Zola-mac project.

## Creating a New Blog Post

There are two ways to create a new blog post: manual creation or automated generation from YouTube videos.

### Option 1: Manual Creation

To create a blog post manually, follow these steps:

1.  **Create a new markdown file:** Create a new markdown file in the `content/blog` directory. The filename should be in the format `your-post-title.md`.
2.  **Add front matter:** Add the following front matter to the top of the file:
    ```
    +++
    title = "Your Post Title"
    date = "YYYY-MM-DD"
    summary = "A short summary of your post."
    +++
    ```
3.  **Write your post:** Write your blog post in Markdown format.
4.  **Build the site:** Run `zola build` to build the site and ensure there are no errors.
5.  **Preview the site:** Run `zola serve` to preview the site locally.
6.  **Commit and push:** Commit your changes and push them to the remote repository.

### Option 2: Automated Generation from YouTube

To generate a blog post automatically from a YouTube video:

1.  **Run the generation script:**
    ```bash
    python scripts/generate_posts.py --youtube "https://www.youtube.com/watch?v=VIDEO_ID"
    ```
2.  **Review the generated post:** The script will create a new Markdown file in `content/blog/` with:
    - AI-generated summary in the front matter and summary section
    - Embedded YouTube video
    - Thumbnail image
    - Full transcript
3.  **Build and preview:** Run `zola build` and `zola serve` to verify the post.
4.  **Commit and push:** Commit the generated files and push to the repository.

**Note:** The automated generation includes transcripts and AI-style summaries created using keyword analysis, requiring no external AI services.
