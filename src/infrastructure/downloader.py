"""YouTube audio downloader implementation."""
import os
import subprocess
import time
from pathlib import Path

from ..domain.entities import AudioFile, AudioFormat, AudioSource
from .executable_resolver import ExecutableResolver


class YtDlpDownloader:
    """Downloads audio from YouTube using yt-dlp."""

    def __init__(self):
        self.resolver = ExecutableResolver()

    def download(self, source: AudioSource, output_dir: Path, format: str) -> AudioFile:
        """Download audio from YouTube URL."""
        if source.is_local:
            raise ValueError("YtDlpDownloader can only download from YouTube URLs")

        yt_dlp_path = self.resolver.get_executable_path('yt-dlp')
        output_template = str(output_dir / '%(title)s.%(ext)s')
        codec = format

        command = [
            yt_dlp_path,
            '--format', 'bestaudio/best',
            '--output', output_template,
            '--extract-audio',
            '--audio-format', codec,
            '--no-playlist',
            source.url_or_path
        ]

        # Get expected filename
        process = subprocess.Popen(
            command + ['--get-filename'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode, command, output=stdout, stderr=stderr
            )

        final_path = Path(stdout.strip())

        # Check if file already exists
        if final_path.exists():
            print(f"[!] File already exists, skipping download: {final_path}")
            audio_format = AudioFormat.WAV if format == 'wav' else AudioFormat.MP3
            return AudioFile(path=final_path, format=audio_format)

        # Download the file
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode, command, output=stdout, stderr=stderr
            )

        # Wait for file to be available
        if not self._wait_for_file(final_path):
            raise FileNotFoundError(f"Downloaded file not found: {final_path}")

        audio_format = AudioFormat.WAV if format == 'wav' else AudioFormat.MP3
        return AudioFile(path=final_path, format=audio_format)

    def _wait_for_file(self, file_path: Path, delay: float = 0.5, max_retries: int = 100) -> bool:
        """Wait for a file to become available."""
        retries = 0
        while retries < max_retries:
            if file_path.exists():
                print(f"[!] File found: {file_path}")
                return True
            else:
                print(f"[!] Waiting for file: {retries}/{max_retries} - {file_path}")
            time.sleep(delay)
            retries += 1
        return False
