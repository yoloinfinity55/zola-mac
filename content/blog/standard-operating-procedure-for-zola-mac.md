+++
title = "Standard Operating Procedure for Zola-mac"
date = "2025-11-02"
summary = "This document outlines the standard operating procedure for the Zola-mac project."
+++

This document outlines the standard operating procedure for the Zola-mac project.

## Creating a New Blog Post

To create a new blog post, follow these steps:

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
