# To run this code you need to install the following dependencies:
# pip install google-genai

import argparse
import base64
import logging
import mimetypes
import os
import re
import struct
import subprocess
import sys
import time
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Set up logging
logging.basicConfig(
    filename='gemini_tts.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Load and rotate API keys
keys = [os.environ.get(f"GEMINI_API_KEY_{i+1}") for i in range(3)]
key_index = int(time.time() // 60) % 3  # Rotate every minute
api_key = keys[key_index]

# Load speech configuration parameters
speech_rate = float(os.environ.get("SPEECH_RATE", "1.0"))
pitch = float(os.environ.get("PITCH", "0.0"))
volume_gain_db = float(os.environ.get("VOLUME_GAIN_DB", "0.0"))

# Load voice selection
voices_str = os.environ.get("VOICES", "Algieba")
voices = [voice.strip() for voice in voices_str.split(",")]


def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()
    print(f"File saved to to: {file_name}")

    # Apply FFmpeg post-processing if speech parameters are not default
    if speech_rate != 1.0 or pitch != 0.0 or volume_gain_db != 0.0:
        apply_ffmpeg_effects(file_name)


def apply_ffmpeg_effects(input_file):
    """Apply speech effects using FFmpeg post-processing."""
    logging.info(f"Applying FFmpeg effects to {input_file}: rate={speech_rate}, pitch={pitch}, volume={volume_gain_db}dB")

    # Build FFmpeg filter chain
    filters = []

    # Speed adjustment (atempo)
    if speech_rate != 1.0:
        filters.append(f"atempo={speech_rate}")

    # Pitch adjustment (rubberband)
    if pitch != 0.0:
        # Convert semitones to pitch ratio (2^(semitones/12))
        pitch_ratio = 2 ** (pitch / 12)
        filters.append(f"rubberband=pitch={pitch_ratio}")

    # Volume adjustment
    if volume_gain_db != 0.0:
        # Convert dB to linear gain: gain = 10^(dB/20)
        linear_gain = 10 ** (volume_gain_db / 20)
        filters.append(f"volume={linear_gain}")

    if not filters:
        return  # No effects to apply

    # Combine filters
    filter_chain = ",".join(filters)

    # Create temporary output file
    temp_file = f"{input_file}.temp.wav"

    try:
        # Run FFmpeg command
        cmd = [
            "ffmpeg", "-y",  # Overwrite output files
            "-i", input_file,  # Input file
            "-af", filter_chain,  # Audio filter chain
            "-c:a", "pcm_s16le",  # Output codec (WAV)
            temp_file  # Output file
        ]

        logging.info(f"Running FFmpeg: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            # Replace original file with processed file
            os.replace(temp_file, input_file)
            logging.info(f"Successfully applied FFmpeg effects to {input_file}")
            print(f"Applied audio effects to {input_file}")
        else:
            logging.error(f"FFmpeg failed for {input_file}: {result.stderr}")
            print(f"Warning: Failed to apply audio effects to {input_file}")
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)

    except subprocess.TimeoutExpired:
        logging.error(f"FFmpeg timed out for {input_file}")
        print(f"Warning: FFmpeg timed out for {input_file}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
    except Exception as e:
        logging.error(f"FFmpeg error for {input_file}: {str(e)}")
        print(f"Warning: FFmpeg error for {input_file}: {str(e)}")
        if os.path.exists(temp_file):
            os.remove(temp_file)


def generate(voice_name):
    logging.info(f"Starting generation for voice: {voice_name}")

    # Try each API key in sequence until one works
    for attempt_key_index in range(3):
        attempt_api_key = keys[attempt_key_index]
        logging.info(f"Trying API key index {attempt_key_index} (GEMINI_API_KEY_{attempt_key_index + 1}) for voice {voice_name}")

        try:
            with open("input.txt", "r", encoding="utf-8") as f:
                text = f.read()

            client = genai.Client(
                api_key=attempt_api_key,
            )

            model = "gemini-2.5-flash-preview-tts"
            contents = types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=text),
                ],
            )
            generate_content_config = types.GenerateContentConfig(
                temperature=1,
                response_modalities=[
                    "audio",
                ],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name
                        )
                    )
                ),
            )

            file_index = 0
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                if (
                    chunk.candidates is None
                    or chunk.candidates[0].content is None
                    or chunk.candidates[0].content.parts is None
                ):
                    continue
                if chunk.candidates[0].content.parts[0].inline_data and chunk.candidates[0].content.parts[0].inline_data.data:
                    file_name = f"{voice_name}_{file_index}"
                    file_index += 1
                    inline_data = chunk.candidates[0].content.parts[0].inline_data
                    data_buffer = inline_data.data
                    mime_type = inline_data.mime_type
                    if data_buffer is None or mime_type is None:
                        continue
                    file_extension = mimetypes.guess_extension(mime_type)
                    if file_extension is None:
                        file_extension = ".wav"
                        data_buffer = convert_to_wav(data_buffer, mime_type)
                    save_binary_file(f"{file_name}{file_extension}", data_buffer)
                else:
                    print(chunk.text)

            logging.info(f"Successfully generated audio for voice: {voice_name} using API key index {attempt_key_index}")
            return  # Success, exit the function

        except Exception as e:
            logging.warning(f"Failed with API key index {attempt_key_index} for voice {voice_name}: {str(e)}")
            if attempt_key_index < 2:  # If not the last key, continue to next
                continue
            else:  # All keys failed
                logging.error(f"All API keys failed for voice {voice_name}. Last error: {str(e)}")
                raise

def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """Generates a WAV file header for the given audio data and parameters.

    Args:
        audio_data: The raw audio data as a bytes object.
        mime_type: Mime type of the audio data.

    Returns:
        A bytes object representing the WAV file header.
    """
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk size

    # http://soundfile.sapp.org/doc/WaveFormat/

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",          # ChunkID
        chunk_size,       # ChunkSize (total file size - 8 bytes)
        b"WAVE",          # Format
        b"fmt ",          # Subchunk1ID
        16,               # Subchunk1Size (16 for PCM)
        1,                # AudioFormat (1 for PCM)
        num_channels,     # NumChannels
        sample_rate,      # SampleRate
        byte_rate,        # ByteRate
        block_align,      # BlockAlign
        bits_per_sample,  # BitsPerSample
        b"data",          # Subchunk2ID
        data_size         # Subchunk2Size (size of audio data)
    )
    return header + audio_data

def parse_audio_mime_type(mime_type: str) -> dict[str, int]:
    """Parses bits per sample and rate from an audio MIME type string.

    Assumes bits per sample is encoded like "L16" and rate as "rate=xxxxx".

    Args:
        mime_type: The audio MIME type string (e.g., "audio/L16;rate=24000").

    Returns:
        A dictionary with "bits_per_sample" and "rate" keys. Values will be
        integers if found, otherwise None.
    """
    bits_per_sample = 16
    rate = 24000

    # Extract rate from parameters
    parts = mime_type.split(";")
    for param in parts: # Skip the main type part
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError):
                # Handle cases like "rate=" with no value or non-integer value
                pass # Keep rate as default
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass # Keep bits_per_sample as default if conversion fails

    return {"bits_per_sample": bits_per_sample, "rate": rate}


def load_progress():
    """Load the last processed voice index from progress file."""
    try:
        with open("gemini_tts_progress.json", "r") as f:
            data = json.load(f)
            return data.get("last_index", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0


def save_progress(index):
    """Save the last processed voice index to progress file."""
    data = {"last_index": index}
    with open("gemini_tts_progress.json", "w") as f:
        json.dump(data, f)


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Gemini TTS Generator with speech control')
    parser.add_argument('--reset', '-r', action='store_true', help='Reset progress and start from beginning')
    parser.add_argument('--rate', type=float, help='Speech rate (0.5-2.0, default: 1.0 = normal speed)')
    parser.add_argument('--pitch', type=float, help='Voice pitch in semitones (-10 to +10, default: 0.0)')
    parser.add_argument('--volume', type=float, help='Volume gain in dB (-10 to +10, default: 0.0)')
    parser.add_argument('--voice', help='Voice name (overrides VOICES env var)')

    args = parser.parse_args()

    # Override speech parameters from command line
    if args.rate is not None:
        speech_rate = args.rate
        print(f"Speech rate set to: {speech_rate}")
    if args.pitch is not None:
        pitch = args.pitch
        print(f"Pitch set to: {pitch} semitones")
    if args.volume is not None:
        volume_gain_db = args.volume
        print(f"Volume gain set to: {volume_gain_db} dB")
    if args.voice is not None:
        voices = [args.voice]
        print(f"Voice set to: {args.voice}")

    # Handle reset flag
    if args.reset:
        try:
            os.remove("gemini_tts_progress.json")
            print("Progress reset. Starting from beginning.")
            logging.info("Progress manually reset by user")
        except FileNotFoundError:
            print("No progress file found. Starting fresh.")
        start_index = 0
    else:
        start_index = load_progress()

    logging.info(f"Selected API key index: {key_index}, Key: GEMINI_API_KEY_{key_index + 1}")
    logging.info(f"API key preview: {api_key[:20]}..." if api_key else "API key not found")
    logging.info(f"Speech config - Rate: {speech_rate}, Pitch: {pitch}, Volume: {volume_gain_db}dB")
    logging.info(f"Selected voices: {voices}")
    if args.rate is not None or args.pitch is not None or args.volume is not None:
        logging.info(f"Command-line overrides applied: rate={args.rate}, pitch={args.pitch}, volume={args.volume}")

    logging.info(f"Starting script execution, resuming from voice index: {start_index}")
    print(f"Resuming from voice index: {start_index}")

    i = start_index  # Initialize i for error handling
    try:
        for i in range(start_index, len(voices)):
            voice = voices[i]
            logging.info(f"Processing voice {i}: {voice}")
            print(f"Generating audio for voice: {voice} (index {i})")
            generate(voice)
            save_progress(i + 1)  # Save progress after successful generation
            logging.info(f"Completed voice {i}: {voice}, progress saved to index {i + 1}")
            time.sleep(60)  # Delay to avoid rate limits
    except Exception as e:
        error_msg = f"Error occurred at voice index {i}: {str(e)}"
        logging.error(error_msg)
        print(error_msg)
        print("Progress saved. You can resume later.")
        raise
