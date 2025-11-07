import os
import asyncio
import edge_tts
from langdetect import detect, LangDetectException

async def text_to_speech_edge_tts(text_file="web_audio.txt", output_file="web_audio.mp3"):
    if not os.path.exists(text_file):
        print(f"{text_file} not found.")
        return

    with open(text_file, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        print(f"{text_file} is empty.")
        return

    try:
        lang = detect(text[:500])
    except LangDetectException:
        lang = "en"
        print("Warning: Language detection failed, using English.")

    # Choose voice based on detected language
    if lang.startswith("zh"):
        voice = "zh-CN-XiaoxiaoNeural"
    elif lang.startswith("ja"):
        voice = "ja-JP-NanamiNeural"
    elif lang.startswith("ko"):
        voice = "ko-KR-SunHiNeural"
    elif lang.startswith("es"):
        voice = "es-ES-ElviraNeural"
    else:
        voice = "en-US-JennyNeural"

    print(f"Detected language: {lang}, using voice: {voice}")

    communicate = edge_tts.Communicate(text, voice=voice)
    await communicate.save(output_file)
    print(f"✅ Audio saved as {output_file}")

def main():
    asyncio.run(text_to_speech_edge_tts())

if __name__ == "__main__":
    main()
