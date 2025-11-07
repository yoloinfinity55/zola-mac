import requests
from bs4 import BeautifulSoup
import os
import sys
import subprocess
import re
from readability import Document
from langdetect import detect, DetectorFactory

# Ensure consistent language detection results
DetectorFactory.seed = 0

def get_say_voice(text):
    """
    Detects the language of the text and returns an appropriate macOS 'say' voice.
    """
    try:
        lang = detect(text)
        if lang == 'zh-cn' or lang == 'zh-tw': # Simplified or Traditional Chinese
            return 'Mei-Jia' # A common Chinese voice on macOS
        elif lang == 'en':
            return 'Samantha' # A common English voice on macOS
        # Add more language mappings as needed
        else:
            return 'Samantha' # Default to English voice
    except Exception:
        return 'Samantha' # Default in case of detection error

def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter the webpage URL: ").strip()

    try:
        print(f"Fetching content from {url}...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an error for bad status codes
        response.encoding = response.apparent_encoding # Detect and set the correct encoding

        # Use readability-lxml to extract the main article content
        doc = Document(response.text)
        summary_html = doc.summary()

        # Use BeautifulSoup to get plain text from the summary HTML
        soup = BeautifulSoup(summary_html, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)

        # --- Post-processing to remove unwanted patterns ---
        # Remove initial navigation/boilerplate (adjust pattern as needed)
        text = re.sub(r'首页\s*资讯\s*(?:\*\s*股票\s*|\*\s*债券\s*|\*\s*商品\s*|\*\s*外汇\s*|\*\s*公司\s*|\*\s*硬AI\s*)*快讯\s*会员\s*(?:\*\s*VIP会员\s*|\*\s*大师课\s*)*法律信息\s*(?:\*\s*版权声明\s*|\*\s*用户协议\s*|\*\s*付费内容订阅协议\s*|\*\s*隐私政策\s*)*华尔街见闻\s*(?:\*\s*关于我们\s*|\*\s*广告投放\s*|\*\s*版权和商务合作\s*|\*\s*联系方式\s*|\*\s*意见反馈\s*)*', '', text, flags=re.DOTALL)

        # Remove "相关文章" section and everything after it
        text = re.split(r'相关文章', text, 1)[0]

        # Remove "打开APP阅读"
        text = re.sub(r'打开APP阅读', '', text)
        # --- End of post-processing ---

        # Optional: Limit text length to avoid overwhelming the speaker
        if len(text) > 5000:
            text = text[:5000] + " [Text truncated for brevity.]"

        print("Saving extracted text to file...")
        with open("web_audio.txt", "w", encoding="utf-8") as f:
            f.write(text)
        print("Text saved to web_audio.txt")

        print("Converting to speech and saving to audio file...")
        aiff_file = "web_audio.aiff"
        mp3_file = "web_audio.mp3"

        # Detect language and get appropriate voice
        voice = get_say_voice(text)

        # Use subprocess.run for safer command execution with detected voice
        subprocess.run(['say', '-v', voice, '-o', aiff_file, text], check=True)
        subprocess.run(['ffmpeg', '-i', aiff_file, '-acodec', 'libmp3lame', '-q:a', '2', mp3_file, '-y'], check=True)

        os.remove(aiff_file)
        print(f"Audio saved to {mp3_file}! (Check Terminal for any errors.)")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
    except subprocess.CalledProcessError as e:
        print(f"Error during audio conversion: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        print("Tips: Ensure the URL is valid (e.g., https://example.com). Some sites block scraping.")

if __name__ == "__main__":
    main()
