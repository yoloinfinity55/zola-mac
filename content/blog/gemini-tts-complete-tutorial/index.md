+++
title = "Complete Guide to Gemini TTS Script: Generate AI Voices with Custom Speech Control"
description = "Step-by-step tutorial for using the advanced Gemini TTS script with FFmpeg post-processing, API key rotation, and customizable speech parameters"
date = 2025-11-12T12:56:10-05:00
draft = false

[taxonomies]
tags = ["AI", "TTS", "Gemini", "Python", "FFmpeg", "Automation"]
categories = ["Tutorials", "AI Tools", "Audio Processing"]

[extra]
author = "Your Name"
+++

# Complete Guide to Gemini TTS Script: Generate AI Voices with Custom Speech Control

This comprehensive tutorial covers everything you need to know about using the advanced Gemini TTS script, featuring API key rotation, FFmpeg post-processing, and full speech customization.

## Overview

The Gemini TTS script is a powerful tool that generates high-quality AI voices using Google's Gemini API, with additional features for speech manipulation, automatic API key switching, and progress tracking.

## Features

- 🎯 **Multiple API Key Support**: Automatic rotation through 3 Gemini API keys
- 🎵 **Speech Customization**: Control speed, pitch, and volume via FFmpeg
- 🔄 **Progress Tracking**: Resume interrupted generations
- 🎭 **Voice Selection**: Choose from multiple Gemini voices
- ⚡ **Command-Line Control**: Override settings per run
- 🔧 **Error Handling**: Automatic retry with different keys

## Prerequisites

- Python 3.8+
- FFmpeg installed
- Valid Gemini API keys
- Virtual environment (recommended)

## Installation

### 1. Clone and Setup

```bash
cd /Users/minijohn/Documents/github-repo/zola-mac
source venv311/bin/activate
pip install -r requirements.txt
pip install google-genai
```

### 2. Configure API Keys

Edit your `.env` file:

```bash
# Gemini API Keys (get from Google AI Studio)
GEMINI_API_KEY_1=your_first_api_key_here
GEMINI_API_KEY_2=your_second_api_key_here
GEMINI_API_KEY_3=your_third_api_key_here

# Speech Configuration (optional)
SPEECH_RATE=1.0
PITCH=0.0
VOLUME_GAIN_DB=0.0

# Voice Selection
VOICES=Algieba
```

### 3. Prepare Input Text

Create or edit `input.txt` with your text:

```
Hello world! This is a test of the Gemini TTS system with custom speech parameters.
```

## Basic Usage

### Generate Audio with Default Settings

```bash
python scripts/core/gemini_tts.py
```

This generates audio using:
- Voice: Algieba (from .env)
- Speech rate: 1.0 (normal speed)
- Pitch: 0.0 (original)
- Volume: 0.0dB (no change)

### Command-Line Speech Control

Override settings for specific runs:

```bash
# Fast, high-pitched voice
python scripts/core/gemini_tts.py --rate 1.5 --pitch 2.0 --voice Zephyr

# Slow, deep voice
python scripts/core/gemini_tts.py --rate 0.7 --pitch -3.0 --voice Algieba

# Just change voice
python scripts/core/gemini_tts.py --voice Charon
```

### Reset and Restart

Force generation from the beginning:

```bash
python scripts/core/gemini_tts.py --reset
```

## Speech Parameters Explained

### Speech Rate (SPEECH_RATE / --rate)

Controls playback speed:
- `1.0` = Normal speed (default)
- `0.5` = Half speed (very slow)
- `2.0` = Double speed (very fast)
- `1.2` = 20% faster

### Pitch (PITCH / --pitch)

Adjusts voice pitch in semitones:
- `0.0` = Original pitch (default)
- `2.0` = 2 semitones higher (more energetic)
- `-3.0` = 3 semitones lower (deeper voice)
- `12.0` = One octave higher

### Volume (VOLUME_GAIN_DB / --volume)

Adjusts loudness in decibels:
- `0.0` = No change (default)
- `6.0` = Twice as loud (+6dB)
- `-6.0` = Half as loud (-6dB)

## Advanced Configuration

### Multiple Voices

Process multiple voices in sequence:

```bash
# In .env file
VOICES=Zephyr,Puck,Charon,Algieba

# Or via command line
python scripts/core/gemini_tts.py --voice "Zephyr,Puck,Charon"
```

### Custom Speech Profiles

Create different voice profiles:

```bash
# Energetic presenter
python scripts/core/gemini_tts.py --rate 1.3 --pitch 1.5 --volume 3.0 --voice Zephyr

# Calm narrator
python scripts/core/gemini_tts.py --rate 0.9 --pitch -1.0 --volume 0.0 --voice Algieba

# Child-like voice
python scripts/core/gemini_tts.py --rate 1.1 --pitch 4.0 --volume 2.0 --voice Puck
```

## API Key Management

### How Key Rotation Works

The script automatically tries API keys in order:
1. GEMINI_API_KEY_1
2. GEMINI_API_KEY_2
3. GEMINI_API_KEY_3

If one fails (quota exceeded, invalid key), it automatically switches to the next.

### Monitoring Usage

Check `gemini_tts.log` for detailed information:

```bash
tail -f gemini_tts.log
```

Log shows:
- Which API key was selected
- Success/failure of each generation
- FFmpeg processing details
- Error messages and recovery attempts

## Troubleshooting

### Common Issues

#### 401 UNAUTHENTICATED Error
```
Error: API keys are not supported by this API. Expected OAuth2 access token
```
**Solution**: Some Gemini API keys may not support TTS. Try different keys or check Google AI Studio.

#### 429 RESOURCE_EXHAUSTED Error
```
Error: You exceeded your current quota
```
**Solution**: Wait for quota reset (usually daily) or upgrade your Gemini API plan.

#### FFmpeg Not Found
```
Error: FFmpeg command not found
```
**Solution**: Install FFmpeg:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

### Progress Issues

If the script gets stuck or you want to restart:

```bash
# Delete progress file
rm gemini_tts_progress.json

# Or use reset flag
python scripts/core/gemini_tts.py --reset
```

## Output Files

The script generates:
- `VoiceName_0.wav` - Main audio file
- `gemini_tts.log` - Detailed operation log
- `gemini_tts_progress.json` - Progress tracking

## Performance Tips

### Rate Limiting
- Script includes 60-second delays between generations
- Respect Gemini API quotas (15 requests/day free tier)
- Use multiple API keys to distribute load

### Audio Quality
- Higher speech rates may reduce quality
- Extreme pitch shifts can sound unnatural
- Test parameters incrementally

### Batch Processing
For multiple voices, use comma-separated lists:
```bash
VOICES=Zephyr,Puck,Charon,Algieba,Kore,Fenrir
```

## Examples

### Podcast Voice Variations

```bash
# Host voice - clear and energetic
python scripts/core/gemini_tts.py --rate 1.1 --pitch 0.5 --voice Zephyr

# Guest voice - slightly different tone
python scripts/core/gemini_tts.py --rate 1.0 --pitch -0.5 --voice Algieba

# Narration - slower, more deliberate
python scripts/core/gemini_tts.py --rate 0.9 --pitch -1.0 --voice Charon
```

### Audiobook Production

```bash
# Chapter narration
python scripts/core/gemini_tts.py --rate 0.95 --pitch -0.5 --volume 1.0 --voice Algieba

# Dialogue - more dynamic
python scripts/core/gemini_tts.py --rate 1.05 --pitch 0.0 --volume 2.0 --voice Zephyr
```

## API Key Best Practices

1. **Rotate Keys**: Use different keys for different projects
2. **Monitor Quotas**: Check usage in Google Cloud Console
3. **Backup Keys**: Keep multiple valid keys ready
4. **Rate Limiting**: Space out requests appropriately

## Conclusion

The Gemini TTS script provides professional-grade AI voice generation with extensive customization options. Whether you're creating podcasts, audiobooks, or automated voice content, this tool offers the flexibility and reliability needed for production use.

For questions or issues, check the log files and ensure your API keys are properly configured in Google AI Studio.
