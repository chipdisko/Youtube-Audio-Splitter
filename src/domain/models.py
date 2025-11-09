"""Simplified domain models."""
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class AudioFormat(Enum):
    """Audio format."""
    WAV = "wav"
    MP3 = "mp3"


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
    def stem(self) -> str:
        return self.path.stem
