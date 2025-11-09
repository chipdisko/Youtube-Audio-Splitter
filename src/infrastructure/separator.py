"""Audio source separator implementation."""
import subprocess
from pathlib import Path

from ..domain.entities import AudioFile, AudioFormat, SeparatedAudio
from .executable_resolver import ExecutableResolver


class DemucsSeparator:
    """Separates audio into stems using Demucs."""

    def __init__(self):
        self.resolver = ExecutableResolver()

    def separate(self, audio_file: AudioFile, output_dir: Path) -> SeparatedAudio:
        """Separate audio file into vocal, drums, bass, and other stems."""
        demucs_path = self.resolver.get_executable_path('demucs.separate')

        command = [
            'python3', '-m', demucs_path,
            '-o', str(output_dir),
            '-d', 'cpu',
            str(audio_file.path)
        ]

        print(f"[!] Running demucs: {' '.join(command)}")

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Stream output
        while True:
            output = process.stdout.readline()
            if output:
                print(output.strip())

            error = process.stderr.readline()
            if error:
                print(error.strip())

            if process.poll() is not None:
                break

        stdout, stderr = process.communicate()

        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode, command, output=stdout, stderr=stderr
            )

        # Locate separated files
        # Demucs typically outputs to: output_dir/htdemucs/filename/vocals.wav, etc.
        stem_dir = output_dir / 'htdemucs' / audio_file.stem

        vocals_path = stem_dir / 'vocals.wav'
        drums_path = stem_dir / 'drums.wav'
        bass_path = stem_dir / 'bass.wav'
        other_path = stem_dir / 'other.wav'

        separated = SeparatedAudio(
            vocals=AudioFile(path=vocals_path, format=AudioFormat.WAV) if vocals_path.exists() else None,
            drums=AudioFile(path=drums_path, format=AudioFormat.WAV) if drums_path.exists() else None,
            bass=AudioFile(path=bass_path, format=AudioFormat.WAV) if bass_path.exists() else None,
            other=AudioFile(path=other_path, format=AudioFormat.WAV) if other_path.exists() else None,
        )

        print(f"[!] Separation completed. Found {len(separated.all_stems)} stems")

        return separated
