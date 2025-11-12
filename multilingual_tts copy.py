import asyncio
from edge_tts import Communicate

async def main():
    with open('input.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    voices = [
        "de-DE-FlorianMultilingualNeural",
        "de-DE-SeraphinaMultilingualNeural",
        "en-AU-WilliamMultilingualNeural",
        "en-US-AndrewMultilingualNeural",
        "en-US-AvaMultilingualNeural",
        "en-US-BrianMultilingualNeural",
        "en-US-EmmaMultilingualNeural",
        "fr-FR-RemyMultilingualNeural",
        "fr-FR-VivienneMultilingualNeural",
        "it-IT-GiuseppeMultilingualNeural",
        "ko-KR-HyunsuMultilingualNeural",
        "pt-BR-ThalitaMultilingualNeural"
    ]

    for voice in voices:
        output_file = f"output_{voice}.mp3"
        try:
            tts = Communicate(text, voice)
            await tts.save(output_file)
            print(f"✅ Saved speech to {output_file}")
        except Exception as e:
            print(f"❌ Failed to generate for {voice}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
