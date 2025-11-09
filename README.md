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

### Method 1: macOS App Bundle (Easiest)
Double-click `YouTube Audio Splitter.app` in the `dist/` folder

Or from terminal:
```
$ open "dist/YouTube Audio Splitter.app"
```

### Method 2: Python Script (DDD Architecture)
```
$ source ../Youtube-Audio-Splitter/bin/activate
$ python3 main.py
```

### Method 3: Legacy Version
```
$ source ../Youtube-Audio-Splitter/bin/activate
$ python3 SPLYT.py
```

## Building macOS App

To rebuild the macOS app bundle:
```
$ source ../Youtube-Audio-Splitter/bin/activate
$ rm -rf build dist
$ python3 setup_ddd.py py2app -A
```

Note: The `-A` flag creates an alias/development build that links to source files.