"""Domain entities for audio processing."""
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class AudioFormat(Enum):
    """Audio format enumeration."""
    WAV = "wav"
    MP3 = "mp3"


class ProcessingStatus(Enum):
    """Processing status enumeration."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    CONVERTING = "converting"
    SPLITTING = "splitting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AudioSource:
    """Represents an audio source (YouTube URL or local file)."""
    url_or_path: str
    is_local: bool

    def __post_init__(self):
        if self.is_local and not Path(self.url_or_path).exists():
            raise ValueError(f"Local file does not exist: {self.url_or_path}")

    @property
    def is_youtube(self) -> bool:
        return not self.is_local

    @classmethod
    def from_youtube_url(cls, url: str) -> 'AudioSource':
        """Create an AudioSource from a YouTube URL."""
        return cls(url_or_path=url, is_local=False)

    @classmethod
    def from_local_file(cls, file_path: str) -> 'AudioSource':
        """Create an AudioSource from a local file path."""
        return cls(url_or_path=file_path, is_local=True)


@dataclass
class AudioFile:
    """Represents an audio file."""
    path: Path
    format: AudioFormat

    def __post_init__(self):
        self.path = Path(self.path)

    @property
    def exists(self) -> bool:
        return self.path.exists()

    @property
    def filename(self) -> str:
        return self.path.name

    @property
    def stem(self) -> str:
        return self.path.stem


@dataclass
class SeparatedAudio:
    """Represents separated audio stems."""
    vocals: Optional[AudioFile] = None
    drums: Optional[AudioFile] = None
    bass: Optional[AudioFile] = None
    other: Optional[AudioFile] = None

    @property
    def all_stems(self) -> list[AudioFile]:
        """Return all available stems."""
        return [stem for stem in [self.vocals, self.drums, self.bass, self.other] if stem is not None]


@dataclass
class ProcessingJob:
    """Represents an audio processing job."""
    source: AudioSource
    output_directory: Path
    download_format: AudioFormat
    should_split: bool
    status: ProcessingStatus = ProcessingStatus.PENDING
    downloaded_file: Optional[AudioFile] = None
    converted_file: Optional[AudioFile] = None
    separated_audio: Optional[SeparatedAudio] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        self.output_directory = Path(self.output_directory)

    def mark_downloading(self):
        """Mark job as downloading."""
        self.status = ProcessingStatus.DOWNLOADING

    def mark_converting(self):
        """Mark job as converting."""
        self.status = ProcessingStatus.CONVERTING

    def mark_splitting(self):
        """Mark job as splitting."""
        self.status = ProcessingStatus.SPLITTING

    def mark_completed(self):
        """Mark job as completed."""
        self.status = ProcessingStatus.COMPLETED

    def mark_failed(self, error_message: str):
        """Mark job as failed."""
        self.status = ProcessingStatus.FAILED
        self.error_message = error_message

    def mark_cancelled(self):
        """Mark job as cancelled."""
        self.status = ProcessingStatus.CANCELLED

    def set_downloaded_file(self, file: AudioFile):
        """Set the downloaded file."""
        self.downloaded_file = file

    def set_converted_file(self, file: AudioFile):
        """Set the converted file."""
        self.converted_file = file

    def set_separated_audio(self, separated: SeparatedAudio):
        """Set the separated audio."""
        self.separated_audio = separated
