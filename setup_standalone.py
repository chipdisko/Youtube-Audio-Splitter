"""Setup script for building standalone macOS app (DDD version)."""
from setuptools import setup

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'packages': ['PyQt6'],
    'includes': ['src', 'src.domain', 'src.application', 'src.infrastructure', 'src.presentation'],
    'iconfile': 'app_icon.icns',
    'plist': {
        'CFBundleName': 'YouTube Audio Splitter',
        'CFBundleDisplayName': 'YouTube Audio Splitter',
        'CFBundleIdentifier': 'com.youtubeaudiosplitter.standalone',
        'CFBundleVersion': '2.0.0',
        'CFBundleShortVersionString': '2.0.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '11.0',
    }
}

setup(
    name='YouTube Audio Splitter',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
