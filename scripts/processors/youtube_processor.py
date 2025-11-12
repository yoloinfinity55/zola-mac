"""
YouTube Processor Module
Handles YouTube video processing, metadata extraction, and audio downloading.
"""

import logging
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode

import requests
from yt_dlp import YoutubeDL

logger = logging.getLogger(__name__)


def clean_youtube_url(url: str) -> str:
    """
    Strips playlist parameters (list, index) from a YouTube URL.

    Args:
        url: YouTube URL to clean

    Returns:
        Cleaned URL with only video ID
    """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    # Keep only the 'v' parameter (video ID)
    new_query = {}
    if 'v' in query_params:
        new_query['v'] = query_params['v']

    cleaned_url = urlunparse(
        parsed_url._replace(query=urlencode(new_query, doseq=True))
    )

    if not new_query and 'youtu.be' not in parsed_url.netloc:
        return url

    logger.info(f"Cleaned URL: {cleaned_url}")
    return cleaned_url


def fetch_youtube_info(url: str) -> Optional[Dict[str, Any]]:
    """
    Fetch YouTube video metadata using yt-dlp.

    Args:
        url: YouTube video URL

    Returns:
        Dictionary containing video metadata or None if failed
    """
    clean_url = clean_youtube_url(url)
    logger.info(f"Fetching YouTube info for: {clean_url}")

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "no_warnings": True,
        "writesubtitles": True,  # Enable subtitle extraction
        "writeautomaticsub": True,  # Include auto-generated subtitles
        "subtitleslangs": ['en'],  # Prefer English subtitles
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:  # type: ignore
            info = ydl.extract_info(clean_url, download=False)

        # Extract subtitle information
        subtitles = info.get("subtitles", {})
        automatic_captions = info.get("automatic_captions", {})

        # Check for available subtitles
        available_subs = []
        if 'en' in subtitles:
            available_subs.extend(subtitles['en'])
        if 'en' in automatic_captions:
            available_subs.extend(automatic_captions['en'])

        return {
            "title": info.get("title", "Untitled Video"),
            "description": info.get("description", ""),
            "upload_date": info.get("upload_date"),
            "duration": info.get("duration", 0),
            "thumbnail": info.get("thumbnail"),
            "id": info.get("id"),
            "uploader": info.get("uploader", "Unknown"),
            "webpage_url": info.get("webpage_url"),
            "tags": info.get("tags", []),
            "view_count": info.get("view_count", 0),
            "subtitles": subtitles,
            "automatic_captions": automatic_captions,
            "has_subtitles": bool(available_subs),
        }
    except Exception as e:
        logger.error(f"Failed to fetch YouTube info: {e}")
        return None


def download_youtube_subtitles(video_id: str, output_dir: Path) -> Optional[str]:
    """
    Download YouTube subtitles/captions for a video.

    Args:
        video_id: YouTube video ID
        output_dir: Directory to save subtitle files

    Returns:
        Path to the subtitle file if successful, None otherwise
    """
    logger.info(f"Attempting to download subtitles for video: {video_id}")

    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en'],
        'outtmpl': str(output_dir / 'subtitles'),
        'quiet': True,
        'no_warnings': True,
    }

    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        with YoutubeDL(ydl_opts) as ydl:  # type: ignore
            info = ydl.extract_info(url, download=True)

        # Check for downloaded subtitle files
        subtitle_files = list(output_dir.glob("subtitles*.vtt")) + list(output_dir.glob("subtitles*.srt"))

        if subtitle_files:
            subtitle_file = subtitle_files[0]
            logger.info(f"✅ Downloaded subtitles: {subtitle_file}")

            # Convert to text content
            transcript = extract_text_from_vtt(subtitle_file)
            if transcript:
                return transcript
            else:
                logger.warning("⚠️ Could not extract text from subtitle file")
                return None
        else:
            logger.info("ℹ️ No subtitles available for this video")
            return None

    except Exception as e:
        logger.error(f"❌ Failed to download subtitles: {e}")
        return None


def extract_text_from_vtt(vtt_file: Path) -> Optional[str]:
    """
    Extract plain text from a VTT subtitle file.

    Args:
        vtt_file: Path to the VTT file

    Returns:
        Extracted text content or None if failed
    """
    try:
        with open(vtt_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split into lines
        lines = content.split('\n')
        text_lines = []
        current_text = []

        for line in lines:
            line = line.strip()

            # Skip empty lines, WEBVTT header, timing lines, and metadata
            if (not line or
                line.startswith('WEBVTT') or
                '-->' in line or
                line.startswith('Kind:') or
                line.startswith('Language:') or
                line.isdigit()):
                # If we have accumulated text, add it to our collection
                if current_text:
                    combined_text = ' '.join(current_text)
                    if combined_text.strip():
                        text_lines.append(combined_text.strip())
                    current_text = []
                continue

            # Clean up HTML tags and timing information
            # Remove HTML tags like <c>, </c>, and timing info like <00:00:08.800>
            clean_line = re.sub(r'<[^>]+>', '', line)
            # Remove timing patterns like <00:00:08.800>
            clean_line = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', '', clean_line)
            clean_line = clean_line.strip()

            if clean_line:
                current_text.append(clean_line)

        # Add any remaining text
        if current_text:
            combined_text = ' '.join(current_text)
            if combined_text.strip():
                text_lines.append(combined_text.strip())

        # Join all text lines and clean up
        transcript = ' '.join(text_lines)

        # Clean up extra whitespace and normalize
        transcript = re.sub(r'\s+', ' ', transcript).strip()

        # Remove duplicate phrases that appear due to overlapping captions
        # This is a simple approach - split into sentences and deduplicate
        if len(transcript) > 100:
            # Split on common sentence endings and deduplicate
            sentences = re.split(r'(?<=[.!?])\s+', transcript)
            seen = set()
            unique_sentences = []
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and sentence not in seen:
                    seen.add(sentence)
                    unique_sentences.append(sentence)

            transcript = ' '.join(unique_sentences)

        return transcript if len(transcript.strip()) > 100 else None  # Minimum length check

    except Exception as e:
        logger.error(f"Failed to extract text from VTT file: {e}")
        return None


def download_audio(video_id: str, filepath: Path) -> bool:
    """
    Download audio from YouTube video using multiple fallback methods.

    Args:
        video_id: YouTube video ID
        filepath: Path to save the audio file

    Returns:
        True if download successful, False otherwise
    """
    logger.info(f"Downloading audio to {filepath}")
    minimal_url = f"https://www.youtube.com/watch?v={video_id}"

    # Method 1: yt-dlp with default settings
    if _download_audio_yt_dlp(minimal_url, filepath, "default"):
        return True

    # Method 2: yt-dlp with alternative settings
    if _download_audio_yt_dlp(minimal_url, filepath, "alternative"):
        return True

    # Method 3: pytube fallback
    if _download_audio_pytube(minimal_url, filepath):
        return True

    logger.error("❌ All audio download methods failed")
    return False


def _download_audio_yt_dlp(url: str, filepath: Path, method: str) -> bool:
    """Download audio using yt-dlp with different configurations."""
    try:
        if method == "default":
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': str(filepath.with_suffix('')),
                'quiet': True,
                'no_warnings': True,
            }
        elif method == "alternative":
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': str(filepath.with_suffix('')),
                'quiet': True,
                'no_warnings': True,
                'extractor_args': {'youtube': {'player_skip': ['js']}},
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            }
        else:
            logger.warning(f"⚠️ Unknown yt-dlp method: {method}")
            return False

        logger.info(f"Trying yt-dlp method: {method}")
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Verify the file was created and has content
        if filepath.exists() and filepath.stat().st_size > 0:
            file_size_mb = filepath.stat().st_size / (1024 * 1024)
            logger.info(f"✅ yt-dlp ({method}) succeeded: {file_size_mb:.1f}MB")
            return True
        else:
            logger.warning(f"⚠️ yt-dlp ({method}) created empty or missing file")
            return False

    except Exception as e:
        logger.warning(f"⚠️ yt-dlp ({method}) failed: {e}")
        return False


def _download_audio_pytube(url: str, filepath: Path) -> bool:
    """Download audio using pytube as fallback."""
    try:
        logger.info("Trying pytube fallback")
        from pytube import YouTube

        # Create YouTube object
        yt = YouTube(url)

        # Get the best audio stream
        audio_stream = yt.streams.filter(only_audio=True).first()
        if not audio_stream:
            logger.warning("⚠️ No audio streams found with pytube")
            return False

        # Download the audio
        temp_filepath = filepath.with_suffix('.mp4')  # pytube downloads as mp4
        audio_stream.download(output_path=str(temp_filepath.parent), filename=temp_filepath.name)

        # Convert to mp3 using ffmpeg if available
        if temp_filepath.exists():
            import subprocess
            mp3_output = str(filepath)
            temp_mp4 = str(temp_filepath)

            # Use ffmpeg to convert to mp3
            cmd = [
                'ffmpeg', '-i', temp_mp4, '-vn', '-acodec', 'mp3',
                '-ab', '192k', '-y', mp3_output
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and filepath.exists():
                # Clean up temp file
                temp_filepath.unlink()
                file_size_mb = filepath.stat().st_size / (1024 * 1024)
                logger.info(f"✅ pytube succeeded: {file_size_mb:.1f}MB")
                return True
            else:
                logger.warning(f"⚠️ ffmpeg conversion failed: {result.stderr}")
                # If conversion fails, keep the mp4 file as mp3 (won't be playable but at least exists)
                temp_filepath.rename(filepath)
                logger.info("✅ pytube downloaded file (conversion failed, keeping as-is)")
                return True
        else:
            logger.warning("⚠️ pytube download failed")
            return False

    except ImportError:
        logger.warning("⚠️ pytube not available")
        return False
    except Exception as e:
        logger.warning(f"⚠️ pytube failed: {e}")
        return False


def split_audio_file(audio_filepath: Path, chunk_duration_minutes: int = 15) -> List[Path]:
    """
    Split a large audio file into smaller chunks for processing.

    Args:
        audio_filepath: Path to the audio file
        chunk_duration_minutes: Duration of each chunk in minutes (default 15 for better API efficiency)

    Returns:
        List of chunk file paths
    """
    import subprocess

    chunk_dir = audio_filepath.parent / "chunks"
    chunk_dir.mkdir(exist_ok=True)

    chunk_files = []
    chunk_duration_seconds = chunk_duration_minutes * 60

    try:
        # Get audio duration
        probe_cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", str(audio_filepath)
        ]
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)

        if probe_result.returncode == 0:
            import json
            probe_data = json.loads(probe_result.stdout)
            duration = float(probe_data['format']['duration'])
            duration_minutes = duration / 60

            # Calculate number of chunks needed
            num_chunks = int(duration // chunk_duration_seconds) + 1

            logger.info(f"🎵 Audio duration: {duration_minutes:.1f} minutes ({duration:.1f}s)")
            logger.info(f"📦 Splitting into {num_chunks} chunks of {chunk_duration_minutes}min each")

            for i in range(num_chunks):
                start_time = i * chunk_duration_seconds
                chunk_path = chunk_dir / "06d"

                split_cmd = [
                    "ffmpeg", "-i", str(audio_filepath),
                    "-ss", str(start_time), "-t", str(chunk_duration_seconds),
                    "-c", "copy", "-y", str(chunk_path)
                ]

                logger.info(f"⏳ Creating chunk {i+1}/{num_chunks}...")
                result = subprocess.run(split_cmd, capture_output=True, text=True)
                if result.returncode == 0 and chunk_path.exists():
                    chunk_size_mb = chunk_path.stat().st_size / (1024 * 1024)
                    chunk_files.append(chunk_path)
                    logger.info(f"✅ Created chunk {i+1}/{num_chunks}: {chunk_path.name} ({chunk_size_mb:.1f}MB)")
                else:
                    logger.error(f"❌ Failed to create chunk {i+1}: {result.stderr}")

            logger.info(f"📦 Chunking complete: {len(chunk_files)} chunks created")
        return chunk_files

    except Exception as e:
        logger.error(f"Audio splitting failed: {e}")
        return []


def parse_upload_date(upload_date: str) -> str:
    """
    Convert YYYYMMDD to YYYY-MM-DD format.

    Args:
        upload_date: Date string in YYYYMMDD format

    Returns:
        Date string in YYYY-MM-DD format
    """
    if upload_date and len(upload_date) == 8:
        return f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
    return ""


def format_duration(seconds: int) -> str:
    """
    Convert seconds to human-readable duration.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if not seconds:
        return "Unknown"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def sanitize_text(text: str) -> str:
    """
    Sanitize text for markdown frontmatter.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text safe for frontmatter
    """
    return text.replace('"', '\\"').replace('\n', ' ').strip()


def get_youtube_video_id(url: str) -> Optional[str]:
    """
    Extract video ID from YouTube URL.

    Args:
        url: YouTube URL

    Returns:
        Video ID or None if not found
    """
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname

        # Handle youtu.be short links
        if hostname == 'youtu.be':
            return parsed_url.path[1:]

        # Handle youtube.com domains
        if hostname in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
            path = parsed_url.path

            # Standard watch URLs: /watch?v=VIDEO_ID
            if path == '/watch':
                query = parse_qs(parsed_url.query)
                return query.get('v', [None])[0]

            # Live URLs: /live/VIDEO_ID
            if path.startswith('/live/'):
                video_id = path.split('/live/')[1].split('?')[0]
                if video_id:
                    return video_id

            # Short live URLs: /live/VIDEO_ID?params
            if '/live/' in path:
                video_id = path.split('/live/')[1].split('?')[0].split('&')[0]
                if video_id:
                    return video_id

            # Handle other YouTube URL formats that might contain video IDs
            # Look for 11-character video IDs in the path
            import re
            video_id_match = re.search(r'[a-zA-Z0-9_-]{11}', path)
            if video_id_match:
                return video_id_match.group(0)

        return None
    except Exception:
        return None


def validate_youtube_url(url: str) -> bool:
    """
    Validate if URL is a proper YouTube video URL.

    Args:
        url: URL to validate

    Returns:
        True if valid YouTube video URL
    """
    video_id = get_youtube_video_id(url)
    return video_id is not None and len(video_id) == 11
