import asyncio
import edge_tts

async def main():
    text = "Hola, soy Arabella. Este es un ejemplo de texto a voz en español."
    voice = "es-ES-ArabellaMultilingualNeural"
    output_file = "output.mp3"

    tts = edge_tts.Communicate(text, voice)
    await tts.save(output_file)

    print(f"✅ Saved speech to {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
