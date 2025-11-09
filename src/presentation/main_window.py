"""Main GUI window for YouTube Audio Splitter."""
import os
import subprocess
import sys
import threading
from pathlib import Path

from PyQt6.QtCore import Q_ARG, QEvent, QMetaObject, Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from ..application.dtos import (
    LocalFileProcessRequest,
    ProcessRequest,
    ProcessingProgress,
)
from ..application.use_cases import (
    ProcessAudioUseCase,
    ProcessLocalFileUseCase,
)


class MainWindow(QWidget):
    """Main application window."""

    def __init__(
        self,
        process_audio_use_case: ProcessAudioUseCase,
        process_local_file_use_case: ProcessLocalFileUseCase,
    ):
        super().__init__()
        self.process_audio_use_case = process_audio_use_case
        self.process_local_file_use_case = process_local_file_use_case

        self.process_thread = None
        self.cancel_requested = False

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()

        # URL input
        self.url_label = QLabel('Enter YouTube URL:', self)
        layout.addWidget(self.url_label)

        self.url_input = QLineEdit(self)
        self.url_input.setText("")  # No default URL
        layout.addWidget(self.url_input)

        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Quality selection
        self.format_label = QLabel('Select Quality and Speed:', self)
        layout.addWidget(self.format_label)

        self.format_layout = QHBoxLayout()
        self.wav_button = QRadioButton("WAV -- HQ! but SLOW...")
        self.mp3_button = QRadioButton("MP3 -- LQ.. but FAST!")
        self.wav_button.setChecked(True)

        self.format_group = QButtonGroup(self)
        self.format_group.addButton(self.wav_button)
        self.format_group.addButton(self.mp3_button)

        self.format_layout.addWidget(self.wav_button)
        self.format_layout.addWidget(self.mp3_button)
        layout.addLayout(self.format_layout)

        self.output_format_label = QLabel('* Output is always .wav', self)
        layout.addWidget(self.output_format_label)

        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Operation mode selection
        self.operation_layout = QHBoxLayout()
        self.download_only_button = QRadioButton("Download Only")
        self.download_and_split_button = QRadioButton("Download and Split")
        self.download_and_split_button.setChecked(True)

        self.operation_group = QButtonGroup(self)
        self.operation_group.addButton(self.download_only_button)
        self.operation_group.addButton(self.download_and_split_button)

        self.operation_layout.addWidget(self.download_only_button)
        self.operation_layout.addWidget(self.download_and_split_button)
        layout.addLayout(self.operation_layout)

        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Output directory selection
        self.output_label = QLabel('Select Output Directory:', self)
        layout.addWidget(self.output_label)

        self.directory_layout = QHBoxLayout()
        self.output_path_display = QLineEdit(self)
        self.output_path_display.setText(os.path.expanduser("~/Documents/Demucs_Cuts"))
        self.directory_layout.addWidget(self.output_path_display)

        self.output_path_button = QPushButton('Select', self)
        self.output_path_button.clicked.connect(self.select_output_directory)
        self.directory_layout.addWidget(self.output_path_button)

        self.view_button = QPushButton('View in Finder', self)
        self.view_button.clicked.connect(self.view_in_finder)
        self.directory_layout.addWidget(self.view_button)

        layout.addLayout(self.directory_layout)

        # Local file selection button
        self.local_file_button = QPushButton('Select Local File to split', self)
        self.local_file_button.clicked.connect(self.select_local_file)
        layout.addWidget(self.local_file_button)

        # Update button text when operation mode changes
        self.download_only_button.toggled.connect(self.update_download_button_text)
        self.download_and_split_button.toggled.connect(self.update_download_button_text)

        # Main action button
        self.download_button = QPushButton('Download and Split', self)
        self.download_button.clicked.connect(self.start_processing)
        layout.addWidget(self.download_button)

        # Cancel button
        self.cancel_button = QPushButton('Cancel', self)
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_process)
        layout.addWidget(self.cancel_button)

        # Status label
        self.status_label = QLabel('', self)
        self.status_label.setStyleSheet(
            "QLabel { background-color: #000; color: #2a2; "
            "font-family: 'Consolas', 'Courier New', monospace; padding: 8px; }"
        )
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.setWindowTitle('YouTube Audio Splitter')
        self.setGeometry(300, 300, 500, 250)

        self.enable_widgets()

    def select_output_directory(self):
        """Open directory selection dialog."""
        options = QFileDialog.Option.DontUseNativeDialog
        selected_directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", options=options
        )
        if selected_directory:
            self.output_path_display.setText(selected_directory)

    def select_local_file(self):
        """Open file selection dialog for local audio files."""
        options = QFileDialog.Option.DontUseNativeDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Local File",
            "",
            "Audio Files (*.wav *.mp3);;All Files (*)",
            options=options
        )
        if file_path:
            self.process_local_file(file_path)

    def start_processing(self):
        """Start the audio processing workflow."""
        try:
            if self.process_thread is not None and self.process_thread.is_alive():
                self.update_status('Error: A process is already running.')
                return

            youtube_url = self.url_input.text().strip()
            if not youtube_url:
                self.update_status('Error: Please enter a YouTube URL.')
                return

            output_directory = self.output_path_display.text().strip()
            if not output_directory:
                self.update_status('Error: Please select an output directory.')
                return

            self.disable_widgets()
            self.cancel_requested = False

            # Start processing in a separate thread
            self.process_thread = threading.Thread(
                target=self._process_youtube_thread,
                args=(youtube_url, output_directory)
            )
            self.process_thread.start()
            self.update_status('Starting...')

        except Exception as e:
            self.update_status(f'Error: {str(e)}')
            self.enable_widgets()

    def _process_youtube_thread(self, youtube_url: str, output_directory: str):
        """Process YouTube audio in a separate thread."""
        try:
            format_choice = 'wav' if self.wav_button.isChecked() else 'mp3'
            should_split = self.download_and_split_button.isChecked()

            request = ProcessRequest(
                youtube_url=youtube_url,
                output_directory=Path(output_directory),
                download_format=format_choice,
                should_split=should_split
            )

            result = self.process_audio_use_case.execute(
                request,
                on_progress=self._on_progress,
                cancellation_token=lambda: self.cancel_requested
            )

            if result.success:
                self.update_status('Completed!')
            else:
                self.update_status(f'Failed: {result.error or result.message}')

        except Exception as e:
            self.update_status(f'Error: {str(e)}')
        finally:
            self.enable_widgets()
            self.cancel_requested = False
            self.process_thread = None

    def process_local_file(self, file_path: str):
        """Process a local audio file."""
        try:
            if self.process_thread is not None and self.process_thread.is_alive():
                self.update_status('Error: A process is already running.')
                return

            output_directory = self.output_path_display.text().strip()
            if not output_directory:
                self.update_status('Error: Please select an output directory.')
                return

            self.disable_widgets()
            self.cancel_requested = False

            # Start processing in a separate thread
            self.process_thread = threading.Thread(
                target=self._process_local_file_thread,
                args=(file_path, output_directory)
            )
            self.process_thread.start()
            self.update_status('Processing local file...')

        except Exception as e:
            self.update_status(f'Error: {str(e)}')
            self.enable_widgets()

    def _process_local_file_thread(self, file_path: str, output_directory: str):
        """Process local file in a separate thread."""
        try:
            request = LocalFileProcessRequest(
                file_path=Path(file_path),
                output_directory=Path(output_directory)
            )

            result = self.process_local_file_use_case.execute(
                request,
                on_progress=self._on_progress,
                cancellation_token=lambda: self.cancel_requested
            )

            if result.success:
                self.update_status('Completed!')
            else:
                self.update_status(f'Failed: {result.error or result.message}')

        except Exception as e:
            self.update_status(f'Error: {str(e)}')
        finally:
            self.enable_widgets()
            self.cancel_requested = False
            self.process_thread = None

    def _on_progress(self, progress: ProcessingProgress):
        """Handle progress updates from use cases."""
        self.update_status(f'[{progress.percentage}%] {progress.message}')

    def cancel_process(self):
        """Cancel the current processing operation."""
        print("[!] Cancellation requested")
        self.cancel_requested = True
        self.cancel_button.setEnabled(False)
        self.cancel_button.setStyleSheet(
            "QPushButton { font-size: 20px; background-color: #555; "
            "color: #888; padding: 8px; margin: 8px; }"
        )
        self.update_status('Cancelling...')

    def view_in_finder(self):
        """Open output directory in file manager."""
        directory = self.output_path_display.text()
        if sys.platform == "darwin":
            subprocess.run(["open", directory])
        elif sys.platform == "win32":
            subprocess.run(["explorer", directory])
        else:
            subprocess.run(["xdg-open", directory])

    def update_status(self, text: str):
        """Update the status label (thread-safe)."""
        QMetaObject.invokeMethod(
            self.status_label,
            "setText",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, text)
        )

    def disable_widgets(self):
        """Disable widgets during processing."""
        self.url_input.setEnabled(False)
        self.output_path_display.setEnabled(False)
        self.output_path_button.setEnabled(False)
        self.wav_button.setEnabled(False)
        self.mp3_button.setEnabled(False)
        self.download_button.setEnabled(False)
        self.local_file_button.setEnabled(False)
        self.download_only_button.setEnabled(False)
        self.download_and_split_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

        self.url_input.setStyleSheet("background-color: #797979; color: #000;")
        self.output_path_display.setStyleSheet("background-color: #797979; color: #000;")
        self.download_button.setStyleSheet(
            "QPushButton { font-size: 20px; background-color: #111; "
            "color: #283; padding: 8px; margin: 8px; }"
        )
        self.download_button.setText("... Processing ...")
        self.cancel_button.setStyleSheet(
            "QPushButton { font-size: 20px; background-color: #bb3333; "
            "color: #fee; padding: 8px; margin: 8px; }"
        )

    def enable_widgets(self):
        """Enable widgets after processing."""
        self.url_input.setEnabled(True)
        self.output_path_display.setEnabled(True)
        self.output_path_button.setEnabled(True)
        self.wav_button.setEnabled(True)
        self.mp3_button.setEnabled(True)
        self.download_button.setEnabled(True)
        self.local_file_button.setEnabled(True)
        self.download_only_button.setEnabled(True)
        self.download_and_split_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

        self.url_input.setStyleSheet("")
        self.output_path_display.setStyleSheet("")
        self.download_button.setStyleSheet(
            "QPushButton { font-size: 20px; background-color: #006400; "
            "color: #f4f4f4; padding: 8px; margin: 8px; }"
        )
        self.update_download_button_text()
        self.cancel_button.setStyleSheet(
            "QPushButton { font-size: 20px; background-color: #555; "
            "color: #888; padding: 8px; margin: 8px; }"
        )

    def update_download_button_text(self):
        """Update download button text based on operation mode."""
        if self.download_only_button.isChecked():
            self.download_button.setText('Download Only')
        else:
            self.download_button.setText('Download and Split')
