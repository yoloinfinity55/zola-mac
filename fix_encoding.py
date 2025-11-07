import os

def fix_encoding(file_path):
    """
    Attempts to fix a file with mojibake text, specifically targeting
    UTF-8 bytes that were incorrectly decoded as latin-1 and then saved.
    """
    try:
        # Read the file in binary mode to get the raw bytes
        with open(file_path, 'rb') as f:
            raw_bytes = f.read()

        # Attempt to decode the raw bytes as latin-1, which is a common
        # intermediate step in UTF-8 mojibake.
        # Then, encode these latin-1 characters back to bytes, which should
        # effectively give us the original UTF-8 bytes.
        # Finally, decode these bytes as UTF-8 to get the correct string.
        corrected_text = raw_bytes.decode('latin-1').encode('latin-1').decode('utf-8')

        # Write the corrected text back to the file with UTF-8 encoding.
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(corrected_text)
        print(f"Successfully attempted to fix encoding for {file_path}")
        print("Please check the file content to see if it is readable now.")

    except Exception as e:
        print(f"Error fixing encoding: {e}")

if __name__ == "__main__":
    fix_encoding("web_audio.txt")
