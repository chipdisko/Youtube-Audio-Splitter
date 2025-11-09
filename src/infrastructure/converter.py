"""Audio format converter implementation."""
import subprocess
from pathlib import Path

from ..domain.entities import AudioFile, AudioFormat
from .executable_resolver import ExecutableResolver


class FfmpegConverter:
    """Converts audio files using FFmpeg."""

    def __init__(self):
        self.resolver = ExecutableResolver()

    def convert_to_wav(self, input_file: AudioFile, output_dir: Path) -> AudioFile:
        """Convert audio file to WAV format."""
        # If already WAV, just return it
        if input_file.format == AudioFormat.WAV and input_file.path.parent == output_dir:
            return input_file

        output_file = output_dir / f'{input_file.stem}.wav'

        # Skip if output already exists
        if output_file.exists():
            print(f"[!] WAV file already exists, skipping conversion: {output_file}")
            return AudioFile(path=output_file, format=AudioFormat.WAV)

        ffmpeg_path = self.resolver.get_executable_path('ffmpeg')

        command = [
            ffmpeg_path,
            '-i', str(input_file.path),
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # WAV codec
            str(output_file)
        ]

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

        return AudioFile(path=output_file, format=AudioFormat.WAV)
