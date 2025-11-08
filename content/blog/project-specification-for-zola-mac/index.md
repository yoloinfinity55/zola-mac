+++
title = "Project Specification for Zola-mac"
date = "2025-11-03"
summary = "This document outlines the specification for the Zola-mac project."
+++

This document outlines the specification for the Zola-mac project.

## Project Overview

Zola-mac is a modern, professional blog focused on building beautiful static sites with the Zola static site generator on macOS. The project combines manual content creation with automated AI-powered content generation from YouTube videos, creating a comprehensive resource for developers learning Zola and Jamstack technologies.

## Project Structure

The project follows Zola's standard directory structure with enhancements for automation:

- **content/:** Contains markdown content organized as page bundles
  - `content/_index.md` - Homepage content
  - `content/blog/` - Blog posts and section index
  - Each post is a page bundle with `index.md`, `asset.jpg`, and `asset.mp3`
- **templates/:** Custom HTML templates using Tera templating
  - `base.html` - Main layout with modern responsive design
  - `index.html` - Homepage template
  - `blog.html` - Blog listing template
  - `page.html` - Individual page template
- **scripts/:** Automation tools
  - `generate_posts.py` - AI-powered YouTube content generator
  - `archive/` - Legacy script versions
- **config.toml:** Zola configuration with taxonomies and build settings
- **requirements.txt:** Python dependencies for automation scripts

## Content Management

The blog supports two content creation workflows:

### Manual Content Creation
- Standard Markdown posts in `content/blog/`
- Front matter with title, date, summary, and tags
- Optional page bundles for rich media content

### Automated Content Generation
- YouTube video processing with AI enhancement
- Generates complete page bundles with multimedia assets
- AI-powered summaries, transcripts, and social media content

## Templates & Design

The site features a modern, clean design optimized for readability:

- **Typography:** Inter font family for professional appearance
- **Layout:** Fixed navigation, responsive grid system
- **Media Support:** YouTube embeds, audio players, image galleries
- **Code Highlighting:** Syntax highlighting for technical content
- **Accessibility:** Semantic HTML, keyboard navigation, screen reader support

## Configuration

Advanced Zola configuration includes:
- GitHub Pages deployment (`https://yoloinfinity55.github.io/zola-mac/`)
- Tag-based taxonomies for content organization
- Markdown processing with code highlighting
- Content pagination (5 posts per page)
- Build optimization settings

## Automation Features

The `scripts/generate_posts.py` script provides comprehensive automation:

### Core Functionality
- YouTube metadata extraction and thumbnail download
- Audio extraction and intelligent chunking for large files
- AI-powered transcription using Groq API
- Multi-step content generation pipeline

### AI-Generated Content
- **Structured Summaries:** Step-by-step breakdowns and key insights
- **Human-like Articles:** Conversational, comprehensive narratives
- **Social Media Posts:** Optimized tweets for promotion
- **Smart Transcripts:** Clean, formatted audio transcripts

### Technical Features
- FFmpeg integration for audio processing
- Error handling and retry logic
- Environment variable configuration
- Progress logging and status updates

## Dependencies

Python requirements for automation:
- `requests` - HTTP client for API calls
- `yt-dlp` - YouTube video processing
- `python-slugify` - URL-friendly slug generation
- `python-dotenv` - Environment variable management
- `pydub` - Audio processing utilities

## Deployment & Maintenance

- **Hosting:** GitHub Pages for free static hosting
- **Build Process:** `zola build` for static site generation
- **Development:** `zola serve` for local development server
- **Version Control:** Git-based workflow with comprehensive .gitignore
- **Content Strategy:** Mix of manual tutorials and automated video content
