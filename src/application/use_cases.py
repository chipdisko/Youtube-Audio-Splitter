"""Use cases for audio processing application."""
from pathlib import Path
from typing import Callable, Optional

from ..domain.entities import (
    AudioFile,
    AudioFormat,
    AudioSource,
    ProcessingJob,
    ProcessingStatus,
)
from ..domain.services import IAudioConverter, IAudioDownloader, IAudioSeparator
from .dtos import (
    DownloadRequest,
    LocalFileProcessRequest,
    ProcessRequest,
    ProcessingProgress,
    ProcessingResult,
)


class DownloadAudioUseCase:
    """Use case for downloading audio from YouTube."""

    def __init__(self, downloader: IAudioDownloader):
        self.downloader = downloader

    def execute(
        self,
        request: DownloadRequest,
        on_progress: Optional[Callable[[ProcessingProgress], None]] = None
    ) -> ProcessingResult:
        """Execute the download use case."""
        try:
            if on_progress:
                on_progress(ProcessingProgress(
                    status="downloading",
                    message="Downloading audio...",
                    percentage=0
                ))

            source = AudioSource.from_youtube_url(request.youtube_url)
            audio_format = AudioFormat.WAV if request.format == 'wav' else AudioFormat.MP3

            downloaded_file = self.downloader.download(
                source,
                request.output_directory,
                request.format
            )

            if on_progress:
                on_progress(ProcessingProgress(
                    status="completed",
                    message="Download completed!",
                    percentage=100
                ))

            return ProcessingResult(
                success=True,
                message="Audio downloaded successfully",
                output_path=downloaded_file.path
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                message="Download failed",
                error=str(e)
            )


class ProcessAudioUseCase:
    """Use case for processing audio (download, convert, split)."""

    def __init__(
        self,
        downloader: IAudioDownloader,
        converter: IAudioConverter,
        separator: IAudioSeparator
    ):
        self.downloader = downloader
        self.converter = converter
        self.separator = separator

    def execute(
        self,
        request: ProcessRequest,
        on_progress: Optional[Callable[[ProcessingProgress], None]] = None,
        cancellation_token: Optional[Callable[[], bool]] = None
    ) -> ProcessingResult:
        """Execute the full processing pipeline."""
        try:
            # Create processing job
            source = AudioSource.from_youtube_url(request.youtube_url)
            audio_format = AudioFormat.WAV if request.download_format == 'wav' else AudioFormat.MP3

            job = ProcessingJob(
                source=source,
                output_directory=request.output_directory,
                download_format=audio_format,
                should_split=request.should_split
            )

            # Ensure output directory exists
            job.output_directory.mkdir(parents=True, exist_ok=True)

            # Check cancellation
            if cancellation_token and cancellation_token():
                job.mark_cancelled()
                return ProcessingResult(
                    success=False,
                    message="Process cancelled",
                    error="User cancelled the operation"
                )

            # Step 1: Download
            job.mark_downloading()
            if on_progress:
                on_progress(ProcessingProgress(
                    status="downloading",
                    message="Downloading audio...",
                    percentage=10
                ))

            downloaded_file = self.downloader.download(
                source,
                job.output_directory,
                request.download_format
            )
            job.set_downloaded_file(downloaded_file)

            # Check cancellation
            if cancellation_token and cancellation_token():
                job.mark_cancelled()
                return ProcessingResult(
                    success=False,
                    message="Process cancelled",
                    error="User cancelled the operation"
                )

            # Step 2: Convert to WAV
            job.mark_converting()
            if on_progress:
                on_progress(ProcessingProgress(
                    status="converting",
                    message="Converting to WAV...",
                    percentage=40
                ))

            converted_file = self.converter.convert_to_wav(
                downloaded_file,
                job.output_directory
            )
            job.set_converted_file(converted_file)

            # Check if splitting is needed
            if not request.should_split:
                job.mark_completed()
                if on_progress:
                    on_progress(ProcessingProgress(
                        status="completed",
                        message="Download and conversion completed!",
                        percentage=100
                    ))
                return ProcessingResult(
                    success=True,
                    message="Audio processed successfully",
                    output_path=converted_file.path
                )

            # Check cancellation
            if cancellation_token and cancellation_token():
                job.mark_cancelled()
                return ProcessingResult(
                    success=False,
                    message="Process cancelled",
                    error="User cancelled the operation"
                )

            # Step 3: Separate audio
            job.mark_splitting()
            if on_progress:
                on_progress(ProcessingProgress(
                    status="splitting",
                    message="Separating audio into stems...",
                    percentage=70
                ))

            separated_audio = self.separator.separate(
                converted_file,
                job.output_directory
            )
            job.set_separated_audio(separated_audio)

            # Complete
            job.mark_completed()
            if on_progress:
                on_progress(ProcessingProgress(
                    status="completed",
                    message="All processing completed!",
                    percentage=100
                ))

            return ProcessingResult(
                success=True,
                message="Audio processed and separated successfully",
                output_path=job.output_directory
            )

        except Exception as e:
            if on_progress:
                on_progress(ProcessingProgress(
                    status="failed",
                    message=f"Processing failed: {str(e)}",
                    percentage=0
                ))
            return ProcessingResult(
                success=False,
                message="Processing failed",
                error=str(e)
            )


class ProcessLocalFileUseCase:
    """Use case for processing a local audio file."""

    def __init__(
        self,
        converter: IAudioConverter,
        separator: IAudioSeparator
    ):
        self.converter = converter
        self.separator = separator

    def execute(
        self,
        request: LocalFileProcessRequest,
        on_progress: Optional[Callable[[ProcessingProgress], None]] = None,
        cancellation_token: Optional[Callable[[], bool]] = None
    ) -> ProcessingResult:
        """Execute local file processing."""
        try:
            # Validate file exists
            if not request.file_path.exists():
                return ProcessingResult(
                    success=False,
                    message="File not found",
                    error=f"File does not exist: {request.file_path}"
                )

            # Ensure output directory exists
            request.output_directory.mkdir(parents=True, exist_ok=True)

            # Determine file format
            extension = request.file_path.suffix.lower().lstrip('.')
            audio_format = AudioFormat.WAV if extension == 'wav' else AudioFormat.MP3

            input_file = AudioFile(path=request.file_path, format=audio_format)

            # Check cancellation
            if cancellation_token and cancellation_token():
                return ProcessingResult(
                    success=False,
                    message="Process cancelled",
                    error="User cancelled the operation"
                )

            # Step 1: Convert to WAV
            if on_progress:
                on_progress(ProcessingProgress(
                    status="converting",
                    message="Converting to WAV...",
                    percentage=20
                ))

            converted_file = self.converter.convert_to_wav(
                input_file,
                request.output_directory
            )

            # Check cancellation
            if cancellation_token and cancellation_token():
                return ProcessingResult(
                    success=False,
                    message="Process cancelled",
                    error="User cancelled the operation"
                )

            # Step 2: Separate audio
            if on_progress:
                on_progress(ProcessingProgress(
                    status="splitting",
                    message="Separating audio into stems...",
                    percentage=50
                ))

            separated_audio = self.separator.separate(
                converted_file,
                request.output_directory
            )

            # Complete
            if on_progress:
                on_progress(ProcessingProgress(
                    status="completed",
                    message="Processing completed!",
                    percentage=100
                ))

            return ProcessingResult(
                success=True,
                message="Local file processed successfully",
                output_path=request.output_directory
            )

        except Exception as e:
            if on_progress:
                on_progress(ProcessingProgress(
                    status="failed",
                    message=f"Processing failed: {str(e)}",
                    percentage=0
                ))
            return ProcessingResult(
                success=False,
                message="Processing failed",
                error=str(e)
            )
