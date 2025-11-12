# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
import logging
import mimetypes
import os
import re
import struct
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

logging.info(f"Selected API key index: {key_index}, Key: GEMINI_API_KEY_{key_index + 1}")
logging.info(f"API key preview: {api_key[:20]}..." if api_key else "API key not found")


def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()
    print(f"File saved to to: {file_name}")


def generate(voice_name):
    logging.info(f"Starting generation for voice: {voice_name} using API key index {key_index}")
    try:
        with open("input.txt", "r", encoding="utf-8") as f:
            text = f.read()

        client = genai.Client(
            api_key=api_key,
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

        logging.info(f"Successfully generated audio for voice: {voice_name}")
    except Exception as e:
        logging.error(f"Failed to generate audio for voice {voice_name}: {str(e)}")
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
    voices = [
        "Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda", "Orus", "Aoede", "Callirrhoe",
        "Autonoe", "Enceladus", "Iapetus", "Umbriel", "Algieba", "Despina", "Erinome", "Algenib",
        "Rasalgethi", "Laomedeia", "Achernar", "Alnilam", "Schedar", "Gacrux", "Pulcherrima",
        "Achird", "Zubenelgenubi", "Vindemiatrix", "Sadachbia", "Sadaltager", "Sulafat"
    ]

    start_index = load_progress()
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
