import asyncio
from edge_tts import Communicate

async def main():
    # Read the input text from input.txt
    with open('input.txt', 'r', encoding='utf-8') as f:
        text = f.read().strip()

    if not text:
        print("Input text is empty.")
        return

    # List of 12 multilingual voices
    voices = [
        "en-US-AndrewMultilingualNeural",  # Male, English (US)
        "en-US-AvaMultilingualNeural",     # Female, English (US)
        "en-US-BrianMultilingualNeural",   # Male, English (US)
        "en-US-EmmaMultilingualNeural",    # Female, English (US)
        "en-AU-WilliamMultilingualNeural", # Male, English (AU)
        "de-DE-FlorianMultilingualNeural", # Male, German
        "de-DE-SeraphinaMultilingualNeural", # Female, German
        "fr-FR-RemyMultilingualNeural",    # Male, French
        "fr-FR-VivienneMultilingualNeural", # Female, French
        "it-IT-GiuseppeMultilingualNeural", # Male, Italian
        "ko-KR-HyunsuMultilingualNeural",  # Male, Korean
        "pt-BR-ThalitaMultilingualNeural"  # Female, Portuguese
    ]

    print(f"Starting conversion of input.txt to 12 voice MP3 files...")

    for voice in voices:
        output_file = f"output_{voice}.mp3"
        try:
            print(f"Generating audio for {voice}...")
            tts = Communicate(text, voice)
            await tts.save(output_file)
            print(f"✅ Successfully saved {output_file}")
        except Exception as e:
            print(f"❌ Failed to generate for {voice}: {e}")

    print("All conversions completed.")

if __name__ == "__main__":
    asyncio.run(main())
