"""Simplified GUI - KISS principle."""
import os
import subprocess
import sys
import threading
from pathlib import Path

from PyQt6.QtCore import Q_ARG, QMetaObject, Qt
from PyQt6.QtWidgets import (
    QButtonGroup, QFileDialog, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QRadioButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget
)

from .services import AudioProcessor


class MainWindow(QWidget):
    """Main application window - simplified."""

    def __init__(self):
        super().__init__()
        self.processor = AudioProcessor()
        self.thread = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()

        # URL input
        layout.addWidget(QLabel('YouTube URL:'))
        self.url_input = QLineEdit()
        layout.addWidget(self.url_input)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Format selection
        layout.addWidget(QLabel('Quality:'))
        format_layout = QHBoxLayout()
        self.wav_btn = QRadioButton("WAV (HQ/Slow)")
        self.mp3_btn = QRadioButton("MP3 (LQ/Fast)")
        self.wav_btn.setChecked(True)
        format_group = QButtonGroup(self)
        format_group.addButton(self.wav_btn)
        format_group.addButton(self.mp3_btn)
        format_layout.addWidget(self.wav_btn)
        format_layout.addWidget(self.mp3_btn)
        layout.addLayout(format_layout)
        layout.addWidget(QLabel('* Output is always WAV'))
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Operation mode
        op_layout = QHBoxLayout()
        self.download_only_btn = QRadioButton("Download Only")
        self.download_split_btn = QRadioButton("Download & Split")
        self.download_split_btn.setChecked(True)
        op_group = QButtonGroup(self)
        op_group.addButton(self.download_only_btn)
        op_group.addButton(self.download_split_btn)
        op_layout.addWidget(self.download_only_btn)
        op_layout.addWidget(self.download_split_btn)
        layout.addLayout(op_layout)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Output directory
        layout.addWidget(QLabel('Output Directory:'))
        dir_layout = QHBoxLayout()
        self.output_path = QLineEdit(os.path.expanduser("~/Documents/Demucs_Cuts"))
        dir_layout.addWidget(self.output_path)
        select_btn = QPushButton('Select')
        select_btn.clicked.connect(self.select_directory)
        dir_layout.addWidget(select_btn)
        view_btn = QPushButton('View')
        view_btn.clicked.connect(self.view_directory)
        dir_layout.addWidget(view_btn)
        layout.addLayout(dir_layout)

        # Local file button
        local_btn = QPushButton('Process Local File')
        local_btn.clicked.connect(self.select_local_file)
        layout.addWidget(local_btn)

        # Process button
        self.process_btn = QPushButton('Download & Split')
        self.process_btn.clicked.connect(self.start_process)
        self.process_btn.setStyleSheet(
            "QPushButton { font-size: 20px; background-color: #006400; "
            "color: #f4f4f4; padding: 8px; margin: 8px; }"
        )
        layout.addWidget(self.process_btn)

        # Update button text when mode changes
        self.download_only_btn.toggled.connect(self.update_button_text)

        # Cancel button
        self.cancel_btn = QPushButton('Cancel')
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel)
        self.cancel_btn.setStyleSheet(
            "QPushButton { font-size: 20px; background-color: #555; "
            "color: #888; padding: 8px; margin: 8px; }"
        )
        layout.addWidget(self.cancel_btn)

        # Status
        self.status = QLabel('')
        self.status.setStyleSheet(
            "QLabel { background-color: #000; color: #2a2; "
            "font-family: 'Monaco', monospace; padding: 8px; }"
        )
        layout.addWidget(self.status)

        self.setLayout(layout)
        self.setWindowTitle('YouTube Audio Splitter')
        self.setGeometry(300, 300, 500, 250)

    def select_directory(self):
        """Select output directory."""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            self.output_path.setText(dir_path)

    def view_directory(self):
        """Open directory in Finder."""
        path = self.output_path.text()
        if sys.platform == "darwin":
            subprocess.run(["open", path])
        elif sys.platform == "win32":
            subprocess.run(["explorer", path])
        else:
            subprocess.run(["xdg-open", path])

    def select_local_file(self):
        """Select and process local file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", "",
            "Audio Files (*.wav *.mp3);;All Files (*)"
        )
        if file_path:
            self.thread = threading.Thread(
                target=self._process_local, args=(file_path,)
            )
            self.thread.start()
            self.set_processing(True)

    def start_process(self):
        """Start YouTube processing."""
        url = self.url_input.text().strip()
        if not url:
            self.update_status("Error: Enter URL")
            return

        output_dir = self.output_path.text().strip()
        if not output_dir:
            self.update_status("Error: Select output directory")
            return

        self.thread = threading.Thread(target=self._process_youtube, args=(url, output_dir))
        self.thread.start()
        self.set_processing(True)

    def _process_youtube(self, url: str, output_dir: str):
        """Process YouTube URL in thread."""
        try:
            format_choice = 'wav' if self.wav_btn.isChecked() else 'mp3'
            split = self.download_split_btn.isChecked()

            self.processor.process_youtube(
                url, Path(output_dir), format_choice, split,
                on_progress=self.update_status
            )
            self.update_status("✓ Completed!")
        except InterruptedError:
            self.update_status("✗ Cancelled")
        except Exception as e:
            self.update_status(f"✗ Error: {e}")
        finally:
            self.set_processing(False)

    def _process_local(self, file_path: str):
        """Process local file in thread."""
        try:
            output_dir = self.output_path.text()
            self.processor.process_local(
                Path(file_path), Path(output_dir),
                on_progress=self.update_status
            )
            self.update_status("✓ Completed!")
        except InterruptedError:
            self.update_status("✗ Cancelled")
        except Exception as e:
            self.update_status(f"✗ Error: {e}")
        finally:
            self.set_processing(False)

    def cancel(self):
        """Cancel processing."""
        self.processor.cancel()
        self.cancel_btn.setEnabled(False)

    def update_status(self, text: str):
        """Update status label (thread-safe)."""
        QMetaObject.invokeMethod(
            self.status, "setText",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, text)
        )

    def set_processing(self, processing: bool):
        """Enable/disable widgets during processing."""
        enabled = not processing
        self.url_input.setEnabled(enabled)
        self.output_path.setEnabled(enabled)
        self.wav_btn.setEnabled(enabled)
        self.mp3_btn.setEnabled(enabled)
        self.download_only_btn.setEnabled(enabled)
        self.download_split_btn.setEnabled(enabled)
        self.process_btn.setEnabled(enabled)
        self.cancel_btn.setEnabled(processing)

        if processing:
            self.process_btn.setText("Processing...")
            self.process_btn.setStyleSheet(
                "QPushButton { font-size: 20px; background-color: #555; "
                "color: #888; padding: 8px; margin: 8px; }"
            )
            self.cancel_btn.setStyleSheet(
                "QPushButton { font-size: 20px; background-color: #b33; "
                "color: #fee; padding: 8px; margin: 8px; }"
            )
        else:
            self.update_button_text()
            self.process_btn.setStyleSheet(
                "QPushButton { font-size: 20px; background-color: #006400; "
                "color: #f4f4f4; padding: 8px; margin: 8px; }"
            )
            self.cancel_btn.setStyleSheet(
                "QPushButton { font-size: 20px; background-color: #555; "
                "color: #888; padding: 8px; margin: 8px; }"
            )

    def update_button_text(self):
        """Update button text based on mode."""
        text = "Download Only" if self.download_only_btn.isChecked() else "Download & Split"
        self.process_btn.setText(text)
