+++
title = "Standard Operating Procedure for Zola-mac"
date = "2025-11-03"
summary = "This document outlines the standard operating procedure for the Zola-mac project."
+++

This document outlines the standard operating procedure for the Zola-mac project, covering both manual content creation and AI-powered automated workflows.

## Environment Setup

### Prerequisites
- Python 3.8+ installed
- FFmpeg installed for audio processing
- Git for version control
- Zola static site generator

### Initial Setup
1. **Clone the repository:**
   ```bash
   git clone https://github.com/yoloinfinity55/zola-mac.git
   cd zola-mac
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your GROQ_API_KEY for AI features
   ```

4. **Install Zola:**
   ```bash
   # On macOS with Homebrew
   brew install zola
   ```

## Content Creation Workflows

### Workflow 1: Manual Content Creation

For original written content or content not sourced from videos:

1. **Create content structure:**
   - For simple posts: Create `content/blog/post-title.md`
   - For rich media posts: Create `content/blog/post-title/` directory (page bundle)

2. **Add front matter:**
   ```toml
   +++
   title = "Your Post Title"
   date = "2025-11-03"
   tags = ["zola", "tutorial", "jamstack"]
   summary = "Brief description of your post content."
   +++
   ```

3. **Write content in Markdown:**
   - Use standard Markdown syntax
   - Include code blocks, images, and links as needed
   - For page bundles, place assets in the same directory

4. **Build and test:**
   ```bash
   zola build
   zola serve
   ```

5. **Commit changes:**
   ```bash
   git add .
   git commit -m "Add: New blog post - [Post Title]"
   git push
   ```

### Workflow 2: Automated YouTube Content Generation

For creating blog posts from educational YouTube videos:

#### Prerequisites
- Valid `GROQ_API_KEY` in `.env` file
- FFmpeg installed and accessible in PATH

#### Generation Process
1. **Prepare the YouTube URL:**
   ```bash
   # Clean URL (removes playlist parameters automatically)
   python scripts/generate_posts.py --youtube "https://www.youtube.com/watch?v=VIDEO_ID"
   ```

2. **Monitor the process:**
   - Script will download video metadata and thumbnail
   - Audio extraction and chunking (for long videos)
   - AI transcription via Groq API
   - Content generation (summaries, articles, social posts)

3. **Review generated content:**
   - Check `content/blog/[slug]/` directory
   - Verify `index.md` content and structure
   - Confirm `asset.jpg` and `asset.mp3` files
   - Review AI-generated sections

4. **Edit and customize (optional):**
   - Modify AI-generated summaries if needed
   - Add custom tags or adjust front matter
   - Enhance formatting or add additional content

5. **Build and deploy:**
   ```bash
   zola build
   zola serve  # Local preview
   git add .
   git commit -m "Add: YouTube post - [Video Title]"
   git push  # Triggers GitHub Pages deployment
   ```

#### Generated Content Structure
Each automated post includes:
- **Page Bundle:** `content/blog/[slug]/` directory
- **index.md:** Complete post with front matter
- **asset.jpg:** Video thumbnail
- **asset.mp3:** Audio file for offline listening
- **AI Content:** Structured summaries, full articles, transcripts
- **Social Media:** Ready-to-post X/Twitter content

## Development Workflow

### Local Development
```bash
# Start development server with live reload
zola serve

# Build for production
zola build
```

### Content Management
- Use `zola check` to validate links and structure
- Preview changes locally before committing
- Test responsive design and media embeds
- Verify build completes without errors

### Quality Assurance
- Check all internal links work
- Verify images load correctly
- Test audio players and video embeds
- Ensure mobile responsiveness
- Validate HTML output

## Deployment

### GitHub Pages (Automated)
1. Push to main branch triggers automatic deployment
2. Built site available at `https://yoloinfinity55.github.io/zola-mac/`
3. No manual intervention required

### Manual Deployment (Alternative)
```bash
zola build
# Deploy public/ directory to your hosting provider
```

## Maintenance Tasks

### Regular Updates
- Keep Python dependencies updated: `pip install -r requirements.txt --upgrade`
- Update Zola to latest version: `brew upgrade zola`
- Review and update .gitignore as needed

### Content Archiving
- Move outdated content to `scripts/archive/` if needed
- Update `config.toml` ignored_content settings
- Maintain clean, organized content structure

### Performance Monitoring
- Monitor build times and site performance
- Optimize images and media files
- Review and update templates for better SEO

## Troubleshooting

### Common Issues
- **Missing FFmpeg:** Install via `brew install ffmpeg`
- **API Key Issues:** Verify `GROQ_API_KEY` in `.env`
- **Build Failures:** Run `zola check` for validation
- **Audio Processing:** Check file permissions and disk space

### Getting Help
- Check script logs for detailed error messages
- Review GitHub repository issues
- Test with sample YouTube URLs for automation
- Validate environment setup with `python --version` and `zola --version`
