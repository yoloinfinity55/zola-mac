import requests
import time
import json
import os
from dotenv import load_dotenv

class MiniMaxTTS:
    def __init__(self, api_key, group_id):
        """
        Initialize MiniMax TTS client

        Args:
            api_key: Your MiniMax API key
            group_id: Your MiniMax group ID
        """
        self.api_key = api_key
        self.group_id = group_id
        self.base_url = "https://api.minimaxi.chat/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def create_task(self, text, model="speech-01-turbo", voice_id="male-qn-qingse", **kwargs):
        """
        Create a text-to-audio task with retry logic for rate limiting

        Args:
            text: Text to synthesize (or file_id if using file input)
            model: Model to use (speech-2.5-hd-preview, speech-2.5-turbo-preview, etc.)
            voice_id: Voice ID to use
            **kwargs: Additional parameters (speed, vol, pitch, audio_sample_rate, bitrate, format)

        Returns:
            task_id: ID of the created task
        """
        url = f"{self.base_url}/text_to_speech"

        payload = {
            "model": model,
            "text": text,
            "voice_id": voice_id,
            **kwargs
        }

        params = {"GroupId": self.group_id}

        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=self.headers, params=params, json=payload)
                response.raise_for_status()

                result = response.json()

                if result.get("base_resp", {}).get("status_code") == 0:
                    return result.get("task_id")
                elif result.get("base_resp", {}).get("status_code") == 1002:  # Rate limit
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        print(f"Rate limited, waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception(f"Rate limit exceeded after {max_retries} attempts: {result}")
                else:
                    raise Exception(f"Failed to create task: {result}")
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Request failed, retrying in {wait_time} seconds: {e}")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Request failed after {max_retries} attempts: {e}")

    def query_task(self, task_id):
        """
        Query the status of a text-to-audio task

        Args:
            task_id: ID of the task to query

        Returns:
            Task status information
        """
        url = f"{self.base_url}/query/text_to_speech"

        params = {
            "GroupId": self.group_id,
            "task_id": task_id
        }

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        return response.json()

    def download_audio(self, file_id, output_path):
        """
        Download the generated audio file

        Args:
            file_id: File ID from completed task
            output_path: Path to save the audio file
        """
        url = f"{self.base_url}/files/retrieve"

        params = {
            "GroupId": self.group_id,
            "file_id": file_id
        }

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        result = response.json()

        if result.get("base_resp", {}).get("status_code") == 0:
            download_url = result.get("file", {}).get("download_url")

            # Download the actual audio file
            audio_response = requests.get(download_url)
            audio_response.raise_for_status()

            with open(output_path, "wb") as f:
                f.write(audio_response.content)

            print(f"Audio saved to {output_path}")
        else:
            raise Exception(f"Failed to retrieve file: {result}")

    def text_to_speech(self, text, output_path, model="speech-01-turbo",
                       voice_id="male-qn-qingse", poll_interval=2, **kwargs):
        """
        Complete workflow: create task, wait for completion, and download audio

        Args:
            text: Text to synthesize
            output_path: Path to save the audio file
            model: Model to use
            voice_id: Voice ID
            poll_interval: Seconds between status checks
            **kwargs: Additional parameters

        Returns:
            Task result information
        """
        # Split long text into chunks to avoid API limits
        chunks = self._split_text(text, max_length=500)

        if len(chunks) == 1:
            # Single chunk
            return self._process_single_chunk(text, output_path, model, voice_id, poll_interval, **kwargs)
        else:
            # Multiple chunks - process each separately
            chunk_files = []

            for i, chunk in enumerate(chunks):
                print(f"Processing chunk {i+1}/{len(chunks)}...")
                chunk_output = f"{output_path.rsplit('.', 1)[0]}_chunk_{i+1}.mp3"
                self._process_single_chunk(chunk, chunk_output, model, voice_id, poll_interval, **kwargs)
                chunk_files.append(chunk_output)

                # Add delay between chunks to avoid rate limiting
                if i < len(chunks) - 1:
                    print("Waiting 5 seconds before next chunk...")
                    time.sleep(5)

            print(f"Generated {len(chunks)} audio chunks:")
            for chunk_file in chunk_files:
                print(f"  - {chunk_file}")

            # Try to combine using ffmpeg if available
            try:
                self._combine_audio_chunks(chunk_files, output_path)
                # Clean up chunk files
                for chunk_file in chunk_files:
                    os.remove(chunk_file)
                print(f"Combined audio saved to {output_path}")
            except Exception as e:
                print(f"Could not combine audio files: {e}")
                print("Individual chunk files remain:")
                for chunk_file in chunk_files:
                    print(f"  - {chunk_file}")

            return {"status": "Success", "chunks_processed": len(chunks), "chunk_files": chunk_files}

    def _split_text(self, text, max_length=500):
        """
        Split text into chunks of maximum length, trying to break at sentence boundaries
        """
        if len(text) <= max_length:
            return [text]

        chunks = []
        current_chunk = ""

        # Split by sentences (Chinese uses 。 for sentence end)
        sentences = text.replace('。', '。\n').replace('！', '！\n').replace('？', '？\n').split('\n')

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(current_chunk + sentence) <= max_length:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _process_single_chunk(self, text, output_path, model, voice_id, poll_interval, **kwargs):
        """
        Process a single chunk of text
        """
        print("Creating TTS task...")
        task_id = self.create_task(text, model, voice_id, **kwargs)
        print(f"Task created with ID: {task_id}")

        print("Waiting for task completion...")
        while True:
            status = self.query_task(task_id)

            if status.get("base_resp", {}).get("status_code") == 0:
                task_status = status.get("status")

                if task_status == "Success":
                    print("Task completed successfully!")
                    file_id = status.get("file_id")

                    print("Downloading audio...")
                    self.download_audio(file_id, output_path)

                    return status
                elif task_status == "Failed":
                    raise Exception(f"Task failed: {status}")
                else:
                    print(f"Task status: {task_status}")
                    time.sleep(poll_interval)
            else:
                raise Exception(f"Query failed: {status}")

    def _combine_audio_chunks(self, chunk_files, output_path):
        """
        Combine multiple audio files using ffmpeg
        """
        import subprocess

        # Create a temporary file list for ffmpeg
        concat_file = output_path + ".txt"
        with open(concat_file, "w") as f:
            for chunk_file in chunk_files:
                f.write(f"file '{chunk_file}'\n")

        # Run ffmpeg to concatenate
        cmd = ["ffmpeg", "-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", output_path]
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Clean up concat file
        os.remove(concat_file)

        if result.returncode != 0:
            raise Exception(f"FFmpeg failed: {result.stderr}")


# Example usage
if __name__ == "__main__":
    # Load environment variables
    load_dotenv()

    # Get credentials from environment
    API_KEY = os.getenv("MINIMAX_API_KEY")
    GROUP_ID = os.getenv("MINIMAX_GROUP_ID")

    if not API_KEY or not GROUP_ID:
        raise ValueError("MINIMAX_API_KEY and MINIMAX_GROUP_ID must be set in .env file")

    # Initialize client
    tts = MiniMaxTTS(API_KEY, GROUP_ID)

    # Read text from input.txt
    with open("input.txt", "r", encoding="utf-8") as f:
        text = f.read().strip()

    # Generate audio from input.txt
    result = tts.text_to_speech(
        text=text,
        output_path="minimax_output.mp3",
        model="speech-01-turbo",
        voice_id="male-qn-qingse"
    )

    print("Audio generation complete!")
