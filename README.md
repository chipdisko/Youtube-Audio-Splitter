# YouTube Audio Splitter

## environment

python 3.12.4

## install packages
```
$ brew install ffmpeg
$ brew install yt-dlp
$ python3 -m venv ../Youtube-Audio-Splitter
$ source ../Youtube-Audio-Splitter/bin/activate
$ pip3 install -r requirements.txt
```
## Execute

### Method 1: Simplified Version (Recommended)
```
$ source ../Youtube-Audio-Splitter/bin/activate
$ python3 main_simple.py
```
**Benefits**: Clean code following DRY/YAGNI/KISS principles

### Method 2: DDD Architecture
```
$ source ../Youtube-Audio-Splitter/bin/activate
$ python3 main.py
```
**Benefits**: Full layered architecture for learning

### Method 3: Legacy Version
```
$ source ../Youtube-Audio-Splitter/bin/activate
$ python3 SPLYT.py
```
**Benefits**: Original monolithic version

## Building macOS App

To rebuild the macOS app bundle:
```
$ source ../Youtube-Audio-Splitter/bin/activate
$ rm -rf build dist
$ python3 setup_ddd.py py2app -A
```

Note: The `-A` flag creates an alias/development build that links to source files.