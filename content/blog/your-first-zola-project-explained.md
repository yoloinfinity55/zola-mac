+++
title = "Your First Zola Project: A Beginner's Guide"
date = 2025-11-02
description = "An introduction to your Zola static site project, explaining its structure and how it works."
+++

# Your First Zola Project: A Beginner's Guide

Welcome to your new Zola project! If you're just starting out, this guide will help you understand the basic structure and how everything fits together to create your website.

## What is Zola?

Zola is a **static site generator**. This means it takes simple text files (like the ones you write in Markdown) and combines them with design templates (HTML files) to create a complete, ready-to-publish website. The key here is "static"—once built, your website is a collection of plain HTML, CSS, and JavaScript files that can be hosted anywhere, without needing a complex server or database.

## The Core Idea: Content + Templates = Website

Think of your project like this:

-   **Content:** This is what you want to say—your blog posts, pages, articles. You write this in an easy-to-read format called Markdown.
-   **Templates:** This is how your content looks—the design, layout, and styling of your website. These are HTML files with special placeholders.

Zola takes your content, plugs it into your templates, and *generates* the final HTML files that make up your website.

## Project Folder Structure Explained

Let's look at the main folders in your project:

-   `config.toml`: This is the brain of your Zola site. It's a configuration file that tells Zola important things like your website's title, its main URL (`base_url`), and other global settings. For example, it specifies if you want a search index or if you're using Sass for styling.

-   `content/`: This is where all your actual website content lives. Inside, you'll find:
    -   `_index.md`: This often defines the main page of a section (like your blog's homepage).
    -   `blog/`: This folder contains all your individual blog posts, written in Markdown (`.md`) files. Each file starts with a special section (`+++`) called "front matter" that holds metadata like the post's title, date, and a short description.

-   `templates/`: This folder holds the HTML files that define the look and feel of your site. These are like blueprints for your pages:
    -   `base.html`: This is often the main, overarching template that other templates inherit from. It might contain the header, footer, and navigation that appear on every page.
    -   `index.html`: The template for your website's homepage.
    -   `blog.html`: The template for displaying a list of blog posts.
    -   `page.html`: A general template for individual pages or blog posts.

-   `static/`: This is for any static assets your website needs, like images, custom CSS files, or JavaScript files that don't need processing by Zola.

-   `public/`: **You won't create files here directly!** This folder is where Zola puts the *final generated website* after it processes your content and templates. These are the files you would upload to a web host.

## The Workflow: How You Build Your Site

1.  **Write Content:** You write your blog posts or pages in Markdown files within the `content/` directory.
2.  **Design (Optional):** You can modify the HTML templates in `templates/` to change your site's design.
3.  **Preview Locally:** To see your changes, you run a command like `zola serve` in your terminal. This starts a local development server, and you can view your site in your web browser (usually at `http://127.0.0.1:1111`). As you make changes, Zola automatically rebuilds and refreshes your browser.
4.  **Build for Publication:** When you're happy with your site, you run `zola build`. This command tells Zola to create all the final HTML, CSS, and JavaScript files in the `public/` directory. These are the files you'll upload to a hosting service (like GitHub Pages, Netlify, etc.) to make your website live.

That's the essence of your Zola project! You write content, Zola applies your design, and then you publish the static output. It's a powerful yet simple way to build fast and secure websites.
