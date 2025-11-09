"""Domain services for audio processing."""
from pathlib import Path
from typing import Protocol

from .entities import AudioFile, AudioSource, SeparatedAudio


class IAudioDownloader(Protocol):
    """Interface for audio downloader."""

    def download(self, source: AudioSource, output_dir: Path, format: str) -> AudioFile:
        """Download audio from source."""
        ...


class IAudioConverter(Protocol):
    """Interface for audio converter."""

    def convert_to_wav(self, input_file: AudioFile, output_dir: Path) -> AudioFile:
        """Convert audio file to WAV format."""
        ...


class IAudioSeparator(Protocol):
    """Interface for audio separator."""

    def separate(self, audio_file: AudioFile, output_dir: Path) -> SeparatedAudio:
        """Separate audio into stems."""
        ...


class AudioProcessingService:
    """Domain service for coordinating audio processing."""

    def __init__(
        self,
        downloader: IAudioDownloader,
        converter: IAudioConverter,
        separator: IAudioSeparator
    ):
        self.downloader = downloader
        self.converter = converter
        self.separator = separator

    def should_skip_download(self, file_path: Path) -> bool:
        """Check if download can be skipped (file already exists)."""
        return file_path.exists()

    def should_skip_conversion(self, file: AudioFile) -> bool:
        """Check if conversion can be skipped (already in WAV format)."""
        from .entities import AudioFormat
        return file.format == AudioFormat.WAV
