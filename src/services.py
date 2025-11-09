"""Simplified service layer - KISS principle."""
import sys
from pathlib import Path
from typing import Optional, Callable

from .domain.models import AudioFile, AudioFormat
from .infrastructure.subprocess_runner import SubprocessRunner


def get_executable_path(name: str) -> str:
    """Get executable path for bundled or dev environment."""
    if getattr(sys, 'frozen', False):
        return str(Path(sys.executable).parent / 'Resources' / name)
    return name


class AudioDownloader:
    """Downloads audio from YouTube."""

    def download(self, url: str, output_dir: Path, format: str) -> AudioFile:
        """Download audio and return the file."""
        yt_dlp = get_executable_path('yt-dlp')
        output_template = str(output_dir / '%(title)s.%(ext)s')

        cmd = [
            yt_dlp, '--format', 'bestaudio/best',
            '--output', output_template,
            '--extract-audio', '--audio-format', format,
            '--no-playlist', url
        ]

        # Get expected filename
        filename = SubprocessRunner.get_output(cmd + ['--get-filename'])
        file_path = Path(filename)

        # Skip if exists
        if file_path.exists():
            print(f"[!] File exists, skipping: {file_path}")
            return AudioFile(file_path, AudioFormat.WAV if format == 'wav' else AudioFormat.MP3)

        # Download
        SubprocessRunner.run(cmd)

        return AudioFile(file_path, AudioFormat.WAV if format == 'wav' else AudioFormat.MP3)


class AudioConverter:
    """Converts audio files."""

    def to_wav(self, input_file: AudioFile, output_dir: Path) -> AudioFile:
        """Convert to WAV format."""
        output_path = output_dir / f'{input_file.stem}.wav'

        # Skip if already WAV in same location
        if input_file.format == AudioFormat.WAV and input_file.path == output_path:
            return input_file

        # Skip if output exists
        if output_path.exists():
            print(f"[!] WAV exists, skipping: {output_path}")
            return AudioFile(output_path, AudioFormat.WAV)

        # Convert
        ffmpeg = get_executable_path('ffmpeg')
        cmd = [
            ffmpeg, '-i', str(input_file.path),
            '-vn', '-acodec', 'pcm_s16le',
            str(output_path)
        ]
        SubprocessRunner.run(cmd)

        return AudioFile(output_path, AudioFormat.WAV)


class AudioSeparator:
    """Separates audio into stems."""

    def separate(self, audio_file: AudioFile, output_dir: Path,
                 on_output: Optional[Callable[[str], None]] = None) -> Path:
        """Separate audio and return output directory."""
        cmd = [
            'python3', '-m', get_executable_path('demucs.separate'),
            '-o', str(output_dir), '-d', 'cpu',
            str(audio_file.path)
        ]

        process = SubprocessRunner.run_streaming(cmd)

        # Stream output
        while True:
            output = process.stdout.readline()
            if output:
                print(output.strip())
                if on_output:
                    on_output(output.strip())

            error = process.stderr.readline()
            if error:
                print(error.strip())

            if process.poll() is not None:
                break

        if process.returncode != 0:
            raise RuntimeError(f"Demucs failed with code {process.returncode}")

        return output_dir / 'htdemucs' / audio_file.stem


class AudioProcessor:
    """Main audio processing orchestrator - KISS."""

    def __init__(self):
        self.downloader = AudioDownloader()
        self.converter = AudioConverter()
        self.separator = AudioSeparator()
        self.cancelled = False

    def process_youtube(self, url: str, output_dir: Path,
                       download_format: str = 'wav',
                       split: bool = True,
                       on_progress: Optional[Callable[[str], None]] = None) -> Path:
        """Process YouTube URL: download → convert → split."""
        output_dir.mkdir(parents=True, exist_ok=True)

        if on_progress:
            on_progress("Downloading...")
        downloaded = self.downloader.download(url, output_dir, download_format)

        if self.cancelled:
            raise InterruptedError("Cancelled")

        if on_progress:
            on_progress("Converting to WAV...")
        wav_file = self.converter.to_wav(downloaded, output_dir)

        if not split:
            return wav_file.path

        if self.cancelled:
            raise InterruptedError("Cancelled")

        if on_progress:
            on_progress("Separating audio...")
        stems_dir = self.separator.separate(wav_file, output_dir)

        return stems_dir

    def process_local(self, file_path: Path, output_dir: Path,
                     on_progress: Optional[Callable[[str], None]] = None) -> Path:
        """Process local file: convert → split."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Detect format
        ext = file_path.suffix.lower().lstrip('.')
        fmt = AudioFormat.WAV if ext == 'wav' else AudioFormat.MP3
        input_file = AudioFile(file_path, fmt)

        if on_progress:
            on_progress("Converting to WAV...")
        wav_file = self.converter.to_wav(input_file, output_dir)

        if self.cancelled:
            raise InterruptedError("Cancelled")

        if on_progress:
            on_progress("Separating audio...")
        stems_dir = self.separator.separate(wav_file, output_dir)

        return stems_dir

    def cancel(self):
        """Cancel current operation."""
        self.cancelled = True
