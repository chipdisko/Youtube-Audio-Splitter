"""Main entry point for YouTube Audio Splitter application."""
import sys
from PyQt6.QtWidgets import QApplication

from src.application.use_cases import (
    ProcessAudioUseCase,
    ProcessLocalFileUseCase,
)
from src.infrastructure.converter import FfmpegConverter
from src.infrastructure.downloader import YtDlpDownloader
from src.infrastructure.separator import DemucsSeparator
from src.presentation.main_window import MainWindow


def main():
    """Initialize and run the application."""
    # Initialize infrastructure services
    downloader = YtDlpDownloader()
    converter = FfmpegConverter()
    separator = DemucsSeparator()

    # Initialize use cases
    process_audio_use_case = ProcessAudioUseCase(
        downloader=downloader,
        converter=converter,
        separator=separator
    )

    process_local_file_use_case = ProcessLocalFileUseCase(
        converter=converter,
        separator=separator
    )

    # Initialize and show GUI
    app = QApplication(sys.argv)
    window = MainWindow(
        process_audio_use_case=process_audio_use_case,
        process_local_file_use_case=process_local_file_use_case
    )
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
