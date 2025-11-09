import sys
sys.setrecursionlimit(2000)
from setuptools import setup

APP = ['SPLYT.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['subprocess', 'PyQt6', 'torchaudio', 'soundfile'],
    'includes': ['sys', 'time', 'threading', 're'],
    'excludes': ['Tkinter'],
    'iconfile': 'app_icon.icns',
    'resources': ['resources/yt-dlp','resources/ffmpeg','resources/demucs']
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)