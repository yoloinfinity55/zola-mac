+++
title = "Project Specification for Zola-mac"
date = "2025-11-02"
summary = "This document outlines the specification for the Zola-mac project."
+++

This document outlines the specification for the Zola-mac project.

## Project Overview

Zola-mac is a blog built with the Zola static site generator. It's designed to be a simple, clean, and fast blog that's easy to maintain and deploy.

## Project Structure

The project is organized into the following directories:

- **content:** Contains the markdown files for the blog posts.
- **templates:** Contains the HTML templates for rendering the site.
- **static:** Contains static assets like CSS, images, etc.
- **scripts:** Contains a Python script for generating posts.
- **config.toml:** The main configuration file for the Zola site.

## Content

Blog posts are located in `content/blog` and written in Markdown. Each post has a front matter section with the title, date, and summary.

## Templates

The site uses standard Zola HTML templates located in the `templates` directory. The templates are:

- **base.html:** The main template.
- **index.html:** The template for the homepage.
- **blog.html:** The template for the blog section.
- **page.html:** The template for individual pages.

## Configuration

The main configuration is in `config.toml`, specifying the base URL, title, description, and Markdown options.

## Scripts

There's a Python script in `scripts/generate_posts.py` to generate new blog posts. The script can be used to generate a single post with a title and content.
