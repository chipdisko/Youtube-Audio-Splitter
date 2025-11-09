"""Data Transfer Objects for application layer."""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DownloadRequest:
    """Request to download audio."""
    youtube_url: str
    output_directory: Path
    format: str  # 'wav' or 'mp3'


@dataclass
class ProcessRequest:
    """Request to process audio (download and split)."""
    youtube_url: str
    output_directory: Path
    download_format: str  # 'wav' or 'mp3'
    should_split: bool = True


@dataclass
class LocalFileProcessRequest:
    """Request to process a local audio file."""
    file_path: Path
    output_directory: Path


@dataclass
class ProcessingProgress:
    """Progress information for a processing job."""
    status: str
    message: str
    percentage: int = 0


@dataclass
class ProcessingResult:
    """Result of a processing operation."""
    success: bool
    message: str
    output_path: Path | None = None
    error: str | None = None
