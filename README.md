# Zola-Mac: AI-Powered Content Automation Platform

An automated static site generator that transforms web content and YouTube videos into multimedia blog posts with AI-generated audio narration. Features advanced Gemini TTS with speech control and FFmpeg post-processing.

## 🎯 Key Features

- **🎵 Advanced Gemini TTS**: Neural voice generation with speed, pitch, and volume control
- **🔄 API Key Rotation**: Automatic fallback through multiple Gemini API keys
- **🎚️ Speech Customization**: FFmpeg-powered audio post-processing effects
- **📝 Web Article Processing**: Convert any web article to blog post with audio
- **🎬 YouTube Integration**: Process videos into transcripts and articles
- **🤖 AI-Powered Content**: Automatic summarization and narration generation
- **🎨 Modern Design**: Responsive static site with beautiful aesthetics
- **⚡ Progress Tracking**: Resume interrupted generations seamlessly

## 📁 Project Structure

```
zola-mac/
├── config.toml              # Zola site configuration
├── content/                 # Blog content (Markdown files)
│   └── blog/               # Blog posts as Page Bundles
├── templates/              # Zola HTML templates
├── static/                 # CSS, JS, and static assets
├── scripts/                # Python automation scripts
│   ├── core/              # Main entry point scripts
│   │   └── gemini_tts.py  # Advanced Gemini TTS script
│   ├── processors/        # Content processing modules
│   └── archive/           # Legacy scripts
├── project-document/       # Comprehensive documentation
├── public/                 # Built site (generated)
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
├── .gitignore             # Git ignore rules
├── .github/               # GitHub Actions workflows
└── README.md              # This file
```

## 🚀 Quick Start

### 1. Set Up Environment
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install system dependencies
brew install ffmpeg zola  # macOS
# OR
sudo apt install ffmpeg   # Ubuntu (Zola: https://www.getzola.org/documentation/getting-started/installation/)
```

### 2. Configure Environment
```bash
# Edit .env with your API keys
nano .env

# Required for Gemini TTS:
GEMINI_API_KEY_1=your_key_here
GEMINI_API_KEY_2=your_key_here
GEMINI_API_KEY_3=your_key_here

# Optional for legacy features:
# GROQ_API_KEY=your_groq_key_here
# UNSPLASH_ACCESS_KEY=your_unsplash_key_here
```

### 3. Test Gemini TTS
```bash
# Generate audio with custom speech parameters
python scripts/core/gemini_tts.py --rate 1.2 --pitch 1.0 --voice Zephyr

# Reset progress and start fresh
python scripts/core/gemini_tts.py --reset

# Build and serve the site
zola build && zola serve
```

## 📖 Documentation

### Core Documentation
- **[PROJECT_SPECIFICATION.md](project-document/PROJECT_SPECIFICATION.md)** - Technical specification and architecture
- **[STANDARD_OPERATING_PROCEDURE.md](project-document/STANDARD_OPERATING_PROCEDURE.md)** - Operational procedures and maintenance
- **[MANUAL_GUIDE.md](project-document/MANUAL_GUIDE.md)** - Step-by-step rebuild instructions
- **[SCRIPTS_ORGANIZATION.md](project-document/SCRIPTS_ORGANIZATION.md)** - Python scripts organization guide
- **[NEXT_STEPS_ROADMAP.md](project-document/NEXT_STEPS_ROADMAP.md)** - Development roadmap and future plans

### User Guides
- **[Complete Gemini TTS Guide](content/blog/gemini-tts-complete-tutorial/)** - Comprehensive tutorial for the advanced TTS features

### Archive Documentation
- **[archive/README.md](archive/README.md)** - Information about archived files

## 🎯 What is Zola-Mac?

Zola-Mac is an automated content creation platform that transforms web articles and YouTube videos into multimedia blog posts with AI-generated audio narration.

### Key Features
- **Web Article Processing**: Convert any web article to a blog post with audio
- **YouTube Integration**: Process YouTube videos into transcripts and articles
- **AI-Powered Content**: Automatic summarization and narration generation
- **Modern Design**: Responsive static site with beautiful aesthetics
- **Modular Architecture**: Clean, maintainable Python codebase

### Technology Stack
- **Static Site Generator**: Zola (Rust-based)
- **Programming Language**: Python 3.8+
- **Primary TTS**: Google Gemini API (neural voices with speech control)
- **Alternative TTS**: Microsoft Edge TTS (neural voices)
- **AI Processing**: Groq API (Llama models for summarization)
- **Audio Processing**: FFmpeg (post-processing effects)
- **Web Scraping**: BeautifulSoup4
- **Image Processing**: Pillow

## 🛠️ Development

### Prerequisites
- Python 3.8+
- FFmpeg (for audio processing)
- Git

### Local Development
```bash
# Clone the repository
git clone <repository-url>
cd zola-mac

# Set up environment (see Quick Start above)

# Run tests
python3 -m pytest  # When test suite is implemented

# Build documentation
# (Documentation is already built as Markdown files)
```

### Project Structure Details

#### `scripts/` Directory
```
scripts/
├── core/                    # Main entry points
│   └── web_to_blog.py      # Web article processor
├── processors/             # Content processing modules
│   ├── content_scraper.py  # Web scraping
│   ├── tts_engine.py      # Text-to-speech
│   ├── image_processor.py # Image handling
│   └── ai_processor.py    # AI operations
├── generators/            # Content generation (expandable)
├── utils/                 # Utilities (expandable)
└── maintenance/           # Maintenance scripts (expandable)
```

#### `archive/` Directory
Contains legacy files, development artifacts, and research materials preserved for historical reference.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Development Guidelines
- Follow the modular architecture in `SCRIPTS_ORGANIZATION.md`
- Add comprehensive documentation for new features
- Include unit tests for new functionality
- Update relevant documentation files

## 📋 Roadmap

See **[NEXT_STEPS_ROADMAP.md](project-document/NEXT_STEPS_ROADMAP.md)** for detailed development plans including:

- **Phase 1**: Core completion (YouTube processing, batch operations)
- **Phase 2**: Infrastructure (CI/CD, Docker, monitoring)
- **Phase 3**: Feature enhancement (AI improvements, media optimization)
- **Phase 4**: Production readiness (security, performance)
- **Phase 5**: Advanced features (API, web interface)

## 📄 License

[Specify your license here]

## 📞 Support

- **Issues**: Use GitHub Issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions and community support
- **Documentation**: Refer to the documentation files in `project-document/`

---

**Built with ❤️ using Zola and Python**
