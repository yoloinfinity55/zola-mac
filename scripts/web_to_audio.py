import urllib.request
from html.parser import HTMLParser
import os
import subprocess
import sys

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []

    def handle_data(self, data):
        self.text.append(data)

    def get_data(self):
        return ''.join(self.text)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter the webpage URL: ").strip()

    try:
        print(f"Fetching content from {url}...")
        with urllib.request.urlopen(url) as response:
            html = response.read().decode('utf-8')

        text = strip_tags(html)
        # Optional: Limit text length to avoid overwhelming the speaker (say handles ~5000 chars well)
        text = text[:5000] + " [Text truncated for brevity.]" if len(text) > 5000 else text

        print("Saving extracted text to file...")
        with open("web_audio.txt", "w", encoding="utf-8") as f:
            f.write(text)
        print("Text saved to web_audio.txt")

        print("Converting to speech and saving to audio file...")
        aiff_file = "web_audio.aiff"
        mp3_file = "web_audio.mp3"
        subprocess.run(['say', '-o', aiff_file], input=text, text=True)
        subprocess.run(['ffmpeg', '-i', aiff_file, '-acodec', 'libmp3lame', mp3_file, '-y'])
        os.remove(aiff_file)
        print(f"Audio saved to {mp3_file}! (Check Terminal for any errors.)")

    except Exception as e:
        print(f"Error: {e}")
        print("Tips: Ensure the URL is valid (e.g., https://example.com). Some sites block scraping.")

if __name__ == "__main__":
    main()
