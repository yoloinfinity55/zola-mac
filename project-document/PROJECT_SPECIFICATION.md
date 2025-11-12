# Zola-Mac Project Specification

## Overview
Zola-Mac is an automated static site generator and blogging platform built on Zola that transforms web content and YouTube videos into rich multimedia blog posts with AI-generated audio narration. The system combines web scraping, text-to-speech synthesis, AI content processing, and static site generation to create a seamless content creation pipeline.

## Core Concept
The project automates the conversion of external content sources (web articles and YouTube videos) into engaging blog posts featuring:
- Original content extraction and processing
- AI-powered summarization and article generation
- Neural text-to-speech audio narration
- Automated thumbnail generation with AI analysis
- Responsive static site generation with modern design

## Architecture

### Technology Stack
- **Static Site Generator**: Zola (Rust-based)
- **Programming Language**: Python 3.8+
- **Text-to-Speech**: Google Gemini TTS API (neural voices with speech control)
- **Alternative TTS**: Microsoft Edge TTS (neural voices)
- **AI Processing**: Groq API (Llama models for summarization and content generation)
- **Web Scraping**: BeautifulSoup4 with requests
- **Image Processing**: Pillow (PIL)
- **Video Processing**: yt-dlp
- **Audio Processing**: FFmpeg (post-processing with speech effects)
- **Templating**: Tera (Zola's template engine)

### System Components

#### 1. Content Ingestion Layer
- **Web Content Scraper**: Extracts text, headings, metadata from web articles
- **YouTube Processor**: Downloads audio, extracts metadata, generates transcripts
- **Content Parser**: Handles HTML parsing, text extraction, and metadata collection

#### 2. AI Processing Layer
- **Text Summarization**: Groq API-powered content condensation
- **Article Generation**: AI-written structured articles from transcripts
- **Image Analysis**: AI-driven keyword generation for stock photo search
- **Social Media Content**: Automated tweet generation for promotion

#### 3. Media Generation Layer
- **TTS Engine**: Multi-chunk neural voice synthesis with Edge TTS
- **Audio Processing**: FFmpeg-based audio concatenation and optimization
- **Image Processing**: Unsplash API integration with 16:9 cropping
- **Thumbnail Generation**: Automated cover image creation

#### 4. Content Management Layer
- **Zola Integration**: Markdown post generation with front matter
- **Asset Management**: Organized file structure (Page Bundles)
- **Metadata Storage**: JSON-based content metadata tracking

#### 5. Presentation Layer
- **Responsive Design**: Modern CSS with glassmorphism effects
- **Grid Layout**: Adaptive blog post cards
- **Audio Integration**: HTML5 audio controls with fallback
- **SEO Optimization**: Structured data and meta tags

## Key Features

### Content Automation
- One-command web article to blog post conversion
- YouTube video to transcript to article pipeline
- Automated thumbnail and audio generation
- AI-powered content enhancement

### Multimedia Integration
- Neural TTS with multiple voice options
- Audio chunking for long-form content
- Responsive image handling
- Embedded YouTube player integration

### AI-Powered Features
- Content summarization and restructuring
- Image keyword analysis for visual assets
- Social media post generation
- Multi-language support (English/Chinese)

### Developer Experience
- Docker-ready deployment
- Environment-based configuration
- Comprehensive logging and error handling
- Modular script architecture

## Data Flow

### Web Article Pipeline
1. URL input → Content scraping → Text extraction
2. AI summarization → TTS generation → Audio concatenation
3. Image keyword generation → Unsplash search → Thumbnail processing
4. Zola markdown creation → Asset organization → Site build

### YouTube Video Pipeline
1. Video URL → Audio download → FFmpeg chunking
2. Groq transcription → AI article generation → TTS synthesis
3. Thumbnail extraction → Metadata collection
4. Zola post assembly → Static site generation

## File Structure
```
zola-mac/
├── config.toml              # Zola configuration
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
├── content/
│   └── blog/               # Blog posts (Page Bundles)
│       └── [post-slug]/
│           ├── index.md    # Post content
│           ├── asset.mp3   # Audio narration
│           ├── asset.jpg   # Thumbnail
│           ├── asset.txt   # Raw text
│           └── asset.json  # Metadata
├── templates/              # Zola templates
│   ├── base.html
│   ├── blog.html
│   └── index.html
├── static/                 # Static assets
│   ├── css/
│   └── js/
└── scripts/                # Automation scripts
    ├── web_to_audio_zola.py
    ├── generate_posts.py
    └── utils.py
```

## Dependencies & Requirements

### System Requirements
- Python 3.8+
- FFmpeg (audio processing)
- macOS/Linux/Windows
- 6GB+ RAM (for AI processing)
- Internet connection (for APIs and downloads)

### Python Packages
- Core: requests, python-slugify, python-dotenv
- AI: groq API client
- Media: edge-tts, yt-dlp, Pillow, pydub
- Web: readability-lxml, beautifulsoup4
- Utils: tqdm, langdetect, toml

### External Services
- Groq API (AI processing)
- Unsplash API (image sourcing)
- YouTube (video content)

## Performance Characteristics

### Processing Times
- Web article: 2-5 minutes (scraping + TTS + thumbnail)
- YouTube video: 5-15 minutes (download + transcription + generation)
- Site build: < 30 seconds

### Content Limits
- Text chunks: 250 words for TTS optimization
- Audio files: 25MB max for Groq transcription
- Images: 16:9 aspect ratio, cropped automatically

### Scalability
- Single-threaded processing (sequential operations)
- Memory-efficient chunking for large content
- Rate limiting and retry logic for API calls

## Security Considerations
- API key management via environment variables
- Input validation for URLs and content
- Safe file operations with path sanitization
- HTTPS-only external communications

## Future Enhancements
- Multi-language TTS support expansion
- Video content analysis and summarization
- Social media automation integration
- Plugin architecture for custom processors
- CDN integration for media assets
- Advanced SEO optimization features
