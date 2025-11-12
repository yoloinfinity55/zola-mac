# Zola-Mac Standard Operating Procedure (SOP)

## 1. System Setup and Initialization

### 1.1 Environment Preparation
```bash
# Clone the repository
git clone https://github.com/yoloinfinity55/zola-mac.git
cd zola-mac

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install system dependencies
# macOS
brew install ffmpeg

# Linux
sudo apt update && sudo apt install ffmpeg

# Verify FFmpeg installation
ffmpeg -version
```

### 1.2 Configuration Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your API keys
nano .env
```

Required environment variables:
```
GROQ_API_KEY=your_groq_api_key_here
UNSPLASH_ACCESS_KEY=your_unsplash_key_here  # Optional
```

### 1.3 Initial Site Build
```bash
# Build the Zola site
zola build

# Serve locally for testing
zola serve
```

## 2. Content Creation Workflows

### 2.1 Gemini TTS Audio Generation (New Primary Workflow)

#### Command Execution
```bash
# Basic usage with default settings
python scripts/core/gemini_tts.py

# Custom speech parameters
python scripts/core/gemini_tts.py --rate 1.2 --pitch 1.0 --voice Zephyr

# Reset progress and start fresh
python scripts/core/gemini_tts.py --reset --rate 0.8 --voice Algieba
```

#### Process Monitoring
- Script automatically tries multiple API keys if one fails
- Progress is saved after each successful voice generation
- Check `gemini_tts.log` for detailed operation logs
- Monitor current directory for generated `.wav` files

#### Expected Outputs
- `Algieba_0.wav` - Generated audio file with speech effects applied
- `gemini_tts.log` - Comprehensive operation log
- `gemini_tts_progress.json` - Progress tracking file

### 2.2 Web Article to Blog Post (Legacy Workflow)

#### Command Execution
```bash
python scripts/web_to_audio_zola.py "https://example.com/article-url"
```

#### Process Monitoring
- Script will log progress through scraping, AI processing, TTS generation
- Check `audio_output/` for temporary files during processing
- Monitor `content/blog/[slug]/` for generated assets

#### Expected Outputs
- `content/blog/[slug]/index.md` - Zola markdown post
- `content/blog/[slug]/asset.mp3` - Audio narration
- `content/blog/[slug]/asset.jpg` - Generated thumbnail
- `content/blog/[slug]/asset.txt` - Raw extracted text
- `content/blog/[slug]/asset.json` - Processing metadata

### 2.2 YouTube Video to Blog Post

#### Command Execution
```bash
python scripts/generate_posts.py --youtube "https://www.youtube.com/watch?v=VIDEO_ID"
```

#### Process Monitoring
- Audio download progress (may take several minutes for long videos)
- Transcription chunking and processing
- AI article generation phases
- TTS synthesis for final audio

#### Quality Checks
- Verify transcript accuracy in generated markdown
- Test audio playback quality
- Confirm thumbnail relevance

### 2.3 Batch Processing
```bash
# Process multiple URLs
for url in "url1" "url2" "url3"; do
    python scripts/web_to_audio_zola.py "$url"
done
```

## 3. Site Management and Publishing

### 3.1 Local Development
```bash
# Start development server
zola serve

# Access at http://localhost:1111
```

### 3.2 Content Review Process
1. **Automated Generation**: Run content creation scripts
2. **Manual Review**: Check generated posts for:
   - Content accuracy and coherence
   - Audio quality and synchronization
   - Thumbnail appropriateness
   - Metadata completeness
3. **Editing**: Modify `index.md` files as needed
4. **Rebuild**: Run `zola build` to update site

### 3.3 Site Building and Deployment
```bash
# Build for production
zola build

# Deploy to GitHub Pages (if configured)
git add .
git commit -m "Add new content"
git push origin main
```

### 3.4 Content Organization
- Posts are automatically organized in `content/blog/` as Page Bundles
- Each post directory contains all related assets
- Zola handles URL generation based on directory structure

## 4. Maintenance and Troubleshooting

### 4.1 Regular Maintenance Tasks

#### Dependency Updates
```bash
# Update Python packages
pip install --upgrade -r requirements.txt

# Update Zola (if using package manager)
# macOS
brew upgrade zola

# Linux
# Follow Zola installation instructions
```

#### Content Cleanup
```bash
# Remove temporary audio files
rm -rf audio_output/tmp/

# Clean build artifacts
rm -rf public/
```

#### Log Review
- Check script output for errors
- Monitor API rate limits
- Verify disk space availability

### 4.2 Common Issues and Solutions

#### TTS Generation Failures
**Symptoms**: Audio file missing or corrupted
**Solutions**:
- Check internet connection
- Verify Edge TTS service availability
- Reduce text chunk sizes if needed
- Check system audio drivers

#### AI API Errors
**Symptoms**: Groq API request failures
**Solutions**:
- Verify API key in `.env`
- Check API quota/limits
- Implement retry logic (built-in)
- Reduce request frequency

#### Image Processing Issues
**Symptoms**: Thumbnails not generating
**Solutions**:
- Verify Unsplash API key (optional)
- Check Pillow installation
- Ensure write permissions on content directories

#### Zola Build Failures
**Symptoms**: Site not building
**Solutions**:
- Validate markdown syntax in posts
- Check template syntax
- Verify asset file paths
- Run `zola check` for diagnostics

### 4.3 Performance Optimization

#### Processing Speed
- Use SSD storage for faster file operations
- Process content during off-peak hours
- Batch similar content types together

#### Resource Management
- Monitor memory usage during large video processing
- Clean temporary files regularly
- Archive old content to reduce build times

## 5. Quality Assurance Procedures

### 5.1 Content Quality Checks
- **Accuracy**: Verify extracted content matches source
- **Completeness**: Ensure all sections are captured
- **Readability**: Check AI-generated content flows naturally
- **Audio Quality**: Test TTS pronunciation and pacing

### 5.2 Technical Validation
- **Links**: Verify all internal/external links work
- **Media**: Confirm audio and images load properly
- **Responsive Design**: Test on multiple screen sizes
- **SEO**: Check meta tags and structured data

### 5.3 Automated Testing
```bash
# Run basic Zola checks
zola check

# Validate generated markdown
python -c "
import glob
for f in glob.glob('content/blog/*/index.md'):
    with open(f, 'r') as file:
        content = file.read()
        # Add validation logic here
"
```

## 6. Backup and Recovery

### 6.1 Content Backup
```bash
# Backup entire site
tar -czf backup-$(date +%Y%m%d).tar.gz .

# Backup only content
tar -czf content-backup-$(date +%Y%m%d).tar.gz content/
```

### 6.2 Recovery Procedures
1. **Content Loss**: Restore from git history or backups
2. **Configuration Issues**: Recreate `.env` and re-run setup
3. **Build Failures**: Clean rebuild with `rm -rf public/ && zola build`

### 6.3 Version Control Best Practices
- Commit after each successful content generation
- Use descriptive commit messages
- Tag releases for major updates
- Keep sensitive data (API keys) out of repository

## 7. Monitoring and Analytics

### 7.1 Performance Monitoring
- Track processing times for different content types
- Monitor API usage and costs
- Log error rates and failure patterns

### 7.2 Content Analytics
- Track most popular content types
- Analyze engagement metrics
- Monitor content generation success rates

### 7.3 System Health Checks
```bash
# Check disk space
df -h

# Verify Python environment
python --version
pip list | grep -E "(edge-tts|groq|requests)"

# Test API connectivity
curl -H "Authorization: Bearer $GROQ_API_KEY" https://api.groq.com/openai/v1/models
```

## 8. Emergency Procedures

### 8.1 Service Outages
- **AI API Down**: Fall back to manual content creation
- **TTS Service Issues**: Use alternative voices or skip audio
- **Image Service Problems**: Use default thumbnails

### 8.2 Data Loss Response
1. Stop all processing
2. Assess scope of data loss
3. Restore from backups
4. Verify system integrity
5. Resume operations with caution

### 8.3 Security Incidents
1. Rotate compromised API keys
2. Audit recent changes
3. Check for unauthorized access
4. Update security measures

## 9. Training and Documentation

### 9.1 Operator Training
- Review this SOP thoroughly
- Practice with test content
- Understand error handling procedures
- Learn manual override techniques

### 9.2 Documentation Maintenance
- Update SOP for new features
- Document custom modifications
- Maintain troubleshooting guides
- Archive resolved issues

## 10. Compliance and Legal Considerations

### 10.1 Content Rights
- Respect copyright and fair use guidelines
- Obtain permissions for copyrighted material
- Attribute sources appropriately
- Monitor content usage policies

### 10.2 Data Privacy
- Handle personal data responsibly
- Comply with privacy regulations
- Secure API keys and credentials
- Regular security audits

### 10.3 API Usage Compliance
- Adhere to API terms of service
- Monitor usage limits and quotas
- Respect rate limiting requirements
- Maintain ethical AI usage practices
