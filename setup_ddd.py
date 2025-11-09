"""Setup script for building macOS app bundle with py2app (DDD version)."""
import sys
sys.setrecursionlimit(2000)
from setuptools import setup

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['PyQt6', 'src'],
    'excludes': ['matplotlib', 'scipy', 'pandas', 'IPython'],
    'iconfile': 'app_icon.icns',
    'strip': True,
    'optimize': 2,
    'plist': {
        'CFBundleName': 'YouTube Audio Splitter',
        'CFBundleDisplayName': 'YouTube Audio Splitter',
        'CFBundleIdentifier': 'com.youtubeaudiosplitter.ddd',
        'CFBundleVersion': '2.0.0',
        'CFBundleShortVersionString': '2.0.0',
        'NSHighResolutionCapable': True,
    }
}

setup(
    name='YouTube Audio Splitter DDD',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
