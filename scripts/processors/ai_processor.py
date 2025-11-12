"""
AI Processor Module
Handles AI-powered content processing, summarization, and generation using Groq API.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

import requests

logger = logging.getLogger(__name__)


def summarize_text_with_groq(text: str, groq_api_key: str, summary_ratio: float = 0.2) -> str:
    """
    Summarize text using GROQ API.

    Args:
        text: Text to summarize
        groq_api_key: Groq API key
        summary_ratio: Ratio of original text to keep (0.0-1.0)

    Returns:
        Summarized text or original text if API fails
    """
    if not groq_api_key:
        logger.warning("GROQ_API_KEY not set. Skipping GROQ summarization.")
        return text

    try:
        headers = {"Authorization": f"Bearer {groq_api_key}"}
        data = {"text": text, "summary_ratio": summary_ratio}
        resp = requests.post("https://api.groq.ai/v1/summarize", headers=headers, json=data, timeout=60)
        resp.raise_for_status()
        summary = resp.json().get("summary")
        return summary or text
    except Exception as e:
        logger.error(f"GROQ summarization failed: {e}. Using original text as summary.")
        return text


def generate_ai_summary_and_structure(title: str, summary: str, transcript_text: str, groq_api_key: str) -> Optional[str]:
    """
    Generate structured key points and summary using Groq API.

    Args:
        title: Content title
        summary: Content summary/description
        transcript_text: Full text content
        groq_api_key: Groq API key

    Returns:
        Structured summary text or None if failed
    """
    if not groq_api_key:
        logger.warning("GROQ_API_KEY not set. Skipping AI structure generation.")
        return None

    logger.info("🧠 Generating structured AI summary via Groq...")

    prompt = f"""
    You are an expert content analyzer. Your task is to extract the core value and structure of the following video content. Format your output strictly using the following markdown sections:

    ## 🔍 Step-by-Step Summary
    Provide a numbered list (4-6 items) breaking down the main steps or concepts covered in the video.

    ## 💡 Key Insights
    Provide 4-6 bullet points highlighting the most important takeaways, best practices, or insights.

    Requirements:
    - Use emojis as shown in section headers
    - Be extremely concise and focused on actionable points.

    Video Title: {title}
    Video Description: {summary[:500]}

    Transcript (use as reference):
    {transcript_text[:10000]}

    Generate the structured content now:
    """

    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": "You are a professional content analyst who extracts concise, structured summaries and key takeaways from technical transcripts."
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.5,
        "max_tokens": 1500,
        "top_p": 0.9,
    }

    for attempt in range(3):  # Retry up to 3 times
        try:
            resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=90)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            logger.info("✅ AI structure generated successfully")
            return content
        except requests.RequestException as e:
            logger.warning(f"Groq API (Structure) attempt {attempt + 1}/3 failed: {e}")
            if attempt < 2:
                import time
                time.sleep(2)  # Wait before retry

    logger.error("❌ Groq API (Structure) failed after all retries")
    return None


def generate_final_article(title: str, summary: str, transcript_text: str, ai_structure: str, groq_api_key: str) -> Optional[str]:
    """
    Generate a flowing, human-readable article based on structured summary.

    Args:
        title: Content title
        summary: Content summary/description
        transcript_text: Full text content
        ai_structure: Structured summary from previous step
        groq_api_key: Groq API key

    Returns:
        Human-readable article text or None if failed
    """
    if not groq_api_key:
        logger.warning("GROQ_API_KEY not set. Skipping final article generation.")
        return None

    logger.info("✍️ Generating final human-like article via Groq...")

    prompt = f"""
    You are an experienced, engaging technical blog writer. Write a comprehensive, human-like article based on the provided video content and structured summary.

    ## 🚀 Introduction
    Write a compelling 2-3 paragraph introduction that hooks the reader, sets the context, and explains what they'll learn from the video/article.

    ## ✍️ Full Article Narrative
    Using the steps and insights provided in the AI Structure, write a flowing, detailed narrative. Use multiple paragraphs, subheadings (H3 or H4), and strong transitions. Do NOT include the original structured lists (Step-by-Step Summary, Key Insights) in this section. Instead, weave them naturally into the narrative flow.

    Requirements:
    - Write in an active, conversational, yet professional tone.
    - Total length for the combined sections: 400-600 words.
    - Do NOT use emojis in this final article text.

    Video Title: {title}
    Video Description: {summary[:500]}

    AI Structure (Source Material for Content):
    {ai_structure}

    Transcript (Reference for detail/context):
    {transcript_text[:10000]}

    Write the article now:
    """

    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": "You are a professional technical blog writer focused on creating clear, engaging, human-readable narratives."
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 2500,
        "top_p": 0.9,
    }

    for attempt in range(3):  # Retry up to 3 times
        try:
            resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=90)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            logger.info("✅ Final article generated successfully")
            return content
        except requests.RequestException as e:
            logger.warning(f"Groq API (Article) attempt {attempt + 1}/3 failed: {e}")
            if attempt < 2:
                import time
                time.sleep(2)  # Wait before retry

    logger.error("❌ Groq API (Article) failed after all retries")
    return None


def generate_social_media_post(title: str, summary: str, tags: list, groq_api_key: str) -> Optional[str]:
    """
    Generate a concise, promotional post for social media.

    Args:
        title: Content title
        summary: Content summary
        tags: List of content tags
        groq_api_key: Groq API key

    Returns:
        Social media post text or None if failed
    """
    if not groq_api_key:
        logger.warning("GROQ_API_KEY not set. Skipping social media post generation.")
        return None

    logger.info("🐦 Generating social media post via Groq...")

    # Create hashtags from tags
    hashtags = " ".join([f"#{tag.replace(' ', '').lower()}" for tag in tags[:4]])

    prompt = f"""
    You are a social media marketing expert. Write a single promotional post (tweet) for X.com for a new blog article.

    Requirements:
    - Be catchy and engaging.
    - Maximize character count to use the full space, but DO NOT exceed 280 characters.
    - Use relevant emojis.
    - Include a clear call-to-action to read the full article.
    - You must include the following auto-generated hashtags at the end: {hashtags}

    Blog Title: {title}
    Blog Summary: {summary[:200]}

    Write ONLY the tweet content (no markdown or introductory text):
    """

    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": "You are a social media copywriter who crafts engaging, concise tweets under the 280-character limit."
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.8,
        "max_tokens": 150,  # Set a low max token count to encourage brevity
        "top_p": 0.9,
    }

    for attempt in range(3):  # Retry up to 3 times
        try:
            resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=45)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()

            # Simple check to enforce the limit if the model went slightly over
            if len(content) > 280:
                 content = content[:277] + "..."  # Truncate and add ellipsis
                 logger.warning("⚠️ Social media post truncated to fit 280-character limit.")

            logger.info("✅ Social media post generated successfully")
            return content
        except requests.RequestException as e:
            logger.warning(f"Groq API (Social) attempt {attempt + 1}/3 failed: {e}")
            if attempt < 2:
                import time
                time.sleep(2)  # Wait before retry

    logger.error("❌ Groq API (Social) failed after all retries")
    return None


def transcribe_audio_with_groq(audio_filepath: str, groq_api_key: str, model: str = "whisper-large-v3") -> str:
    """
    Transcribe audio file using Groq API with automatic chunking for large files.

    Args:
        audio_filepath: Path to audio file
        groq_api_key: Groq API key
        model: Whisper model to use

    Returns:
        Transcribed text
    """
    if not groq_api_key:
        logger.error("GROQ_API_KEY not set. Cannot transcribe audio.")
        return "Automatic transcription unavailable due to missing API key."

    from pathlib import Path
    audio_path = Path(audio_filepath)

    # Check file size (Groq limit is ~25MB for whisper-large-v3)
    file_size_mb = audio_path.stat().st_size / (1024 * 1024)
    max_size_mb = 20  # Conservative limit

    if file_size_mb <= max_size_mb:
        # File is small enough, transcribe directly
        return _transcribe_single_file(audio_filepath, groq_api_key, model)
    else:
        # File is too large, try chunking
        logger.info(".1f")
        return _transcribe_chunked_audio(audio_path, groq_api_key, model)


def _transcribe_single_file(audio_filepath: str, groq_api_key: str, model: str) -> str:
    """Transcribe a single audio file."""
    headers = {"Authorization": f"Bearer {groq_api_key}"}
    data = {'model': model}

    for attempt in range(3):  # Retry up to 3 times
        try:
            with open(audio_filepath, 'rb') as audio_file:
                files = {
                    'file': (audio_filepath.split('/')[-1], audio_file, 'audio/mpeg')
                }

                resp = requests.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers=headers,
                    data=data,
                    files=files,
                    timeout=120
                )

            resp.raise_for_status()
            result = resp.json()
            return result.get("text", "")

        except requests.HTTPError as e:
            if e.response.status_code == 413:  # Payload too large
                logger.warning("File too large for direct transcription, will try chunking")
                return "ERROR: File too large for transcription"
            else:
                logger.warning(f"Groq transcription API attempt {attempt + 1}/3 failed: {e}")
        except requests.RequestException as e:
            logger.warning(f"Groq transcription API attempt {attempt + 1}/3 failed: {e}")
            if attempt < 2:
                import time
                time.sleep(2)  # Wait before retry

    return "ERROR: Audio transcription failed after all retries."


def _transcribe_chunked_audio(audio_path: Path, groq_api_key: str, model: str) -> str:
    """Transcribe audio by splitting into chunks."""
    from .youtube_processor import split_audio_file

    try:
        # Split audio into 10-minute chunks
        chunk_files = split_audio_file(audio_path, chunk_duration_minutes=10)

        if not chunk_files:
            return "ERROR: Failed to split audio file for transcription"

        logger.info(f"Transcribing {len(chunk_files)} audio chunks...")

        full_transcript = []
        for i, chunk_path in enumerate(chunk_files):
            logger.info(f"Transcribing chunk {i+1}/{len(chunk_files)}...")
            chunk_transcript = _transcribe_single_file(str(chunk_path), groq_api_key, model)

            if not chunk_transcript.startswith("ERROR:"):
                full_transcript.append(chunk_transcript)
            else:
                logger.warning(f"Failed to transcribe chunk {i+1}")

            # Clean up chunk file
            try:
                chunk_path.unlink()
            except Exception:
                pass

        # Clean up chunks directory
        try:
            chunk_dir = audio_path.parent / "chunks"
            if chunk_dir.exists():
                chunk_dir.rmdir()
        except Exception:
            pass

        if full_transcript:
            combined_transcript = " ".join(full_transcript)
            logger.info(f"Successfully transcribed {len(full_transcript)} chunks")
            return combined_transcript
        else:
            return "ERROR: All audio chunks failed to transcribe"

    except Exception as e:
        logger.error(f"Chunked transcription failed: {e}")
        return "ERROR: Chunked transcription failed"


def check_groq_api_status(groq_api_key: str) -> Dict[str, Any]:
    """
    Check Groq API status and available models.

    Args:
        groq_api_key: Groq API key

    Returns:
        Dictionary with API status information
    """
    status = {
        'api_accessible': False,
        'models_available': [],
        'error': None
    }

    try:
        headers = {"Authorization": f"Bearer {groq_api_key}"}
        resp = requests.get("https://api.groq.com/openai/v1/models", headers=headers, timeout=10)
        resp.raise_for_status()

        data = resp.json()
        status['api_accessible'] = True
        status['models_available'] = [model['id'] for model in data.get('data', [])]

    except Exception as e:
        status['error'] = str(e)
        logger.error(f"Groq API status check failed: {e}")

    return status
