+++
title = "SOP: Creating a New Blog Post"
date = 2025-10-30
description = "A step-by-step guide to creating a new blog post for the Zola-mac blog."

[extra]
author = "Gemini"
+++

## Introduction

This document outlines the standard operating procedure (SOP) for creating and publishing a new blog post on the Zola-mac blog. Following these steps will ensure consistency and quality across all our content.

## Prerequisites

*   A local installation of Zola on your macOS machine.
*   A local clone of the Zola-mac blog repository.
*   A text editor (e.g., VS Code, Sublime Text).

## Step-by-Step Procedure

### 1. Create a New Markdown File

All blog posts are created as Markdown files in the `content` directory. To create a new post, follow these steps:

1.  Open your terminal and navigate to the root of the Zola-mac blog repository.
2.  Create a new file in the `content` directory with a descriptive name. The filename will be used to generate the URL for the post. For example:

    ```bash
    touch content/my-new-awesome-post.md
    ```

### 2. Add the Front Matter

Every blog post must begin with a TOML front matter block that contains metadata about the post. The front matter is enclosed in `+++` delimiters.

Here is a template for the front matter:

```toml
+++
title = "Your Post Title"
date = YYYY-MM-DD
description = "A brief description of your post."

[extra]
author = "Your Name"
+++
```

*   **`title`**: The title of your blog post.
*   **`date`**: The publication date of the post in `YYYY-MM-DD` format.
*   **`description`**: A short, one-sentence summary of the post. This is used for SEO and in post previews.
*   **`author`**: Your name.

### 3. Write the Content

Write your blog post content in Markdown below the front matter. You can use all the standard Markdown features, including:

*   Headings (`#`, `##`, `###`)
*   Lists (ordered and unordered)
*   Code blocks (with syntax highlighting)
*   Blockquotes
*   Links
*   Images

For more information on Zola's Markdown support, refer to the [official documentation](https://www.getzola.org/documentation/content/overview/).

### 4. Add Images and Other Assets

If your post includes images or other assets, place them in the `static` directory. You can then reference them in your Markdown using a relative path. For example, to include an image named `my-image.png`, you would use the following Markdown:

```markdown
![My Image](/my-image.png)
```

### 5. Preview Your Post

Before publishing, you should preview your post locally to ensure that it looks correct. To do this:

1.  Open your terminal and navigate to the root of the Zola-mac blog repository.
2.  Run the following command to start the Zola development server:

    ```bash
    zola serve
    ```

3.  Open your web browser and navigate to `http://127.0.0.1:1111`. You should see your new post listed on the homepage.

### 6. Commit and Push Your Changes

Once you are satisfied with your post, you need to commit your changes to the Git repository and push them to GitHub.

1.  Add your new post to the Git staging area:

    ```bash
    git add content/my-new-awesome-post.md
    ```

2.  Commit your changes with a descriptive commit message:

    ```bash
    git commit -m "Add new post: My New Awesome Post"
    ```

3.  Push your changes to the `main` branch on GitHub:

    ```bash
    git push origin main
    ```

### 7. Verify Deployment

The Zola-mac blog is configured with a GitHub Actions workflow that automatically deploys the site to GitHub Pages. After you push your changes, you can monitor the deployment progress in the "Actions" tab of the GitHub repository.

Once the deployment is complete, your new post will be live on the site.
