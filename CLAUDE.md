# CLAUDE.md

## Project Overview

YouTube Audio Splitter is a PyQt6-based GUI application that downloads audio from YouTube videos and separates them into individual instrument tracks using AI-powered source separation.

**Architecture**: This project includes **3 different implementations**:
1. **Simplified Version (main_simple.py)** - RECOMMENDED: Follows DRY/YAGNI/KISS principles (~200 lines)
2. **DDD Architecture (main.py)** - Educational: Full 4-layer architecture (~1500 lines)
3. **Legacy Version (SPLYT.py)** - Original: Monolithic implementation (~500 lines)

## Core Features

### 1. YouTube Audio Download
- Downloads audio from YouTube URLs using `yt-dlp`
- Supports both WAV (high quality, slower) and MP3 (lower quality, faster) formats
- Automatic duplicate detection to skip re-downloading

### 2. Audio Format Conversion
- Converts downloaded audio to WAV format using `ffmpeg`
- WAV codec: pcm_s16le
- MP3 codec: libmp3lame at 320k bitrate

### 3. AI-Powered Audio Source Separation
- Uses Demucs 4.0.1 for separating audio into stems
- Separates tracks into: vocals, drums, bass, and other instruments
- CPU-based processing

### 4. Local File Processing
- Can process existing local audio files (WAV/MP3)
- Skips download step for local files

## Technical Architecture

### Lightweight DDD Architecture

The application follows a **4-layer architecture**:

```
┌─────────────────────────────────────┐
│   Presentation Layer (GUI)          │  ← PyQt6 GUI components
├─────────────────────────────────────┤
│   Application Layer (Use Cases)     │  ← Business workflows
├─────────────────────────────────────┤
│   Domain Layer (Business Logic)     │  ← Core business entities
├─────────────────────────────────────┤
│   Infrastructure Layer (External)   │  ← External tools/services
└─────────────────────────────────────┘
```

#### 1. Domain Layer (`src/domain/`)

**Entities** (`entities.py`):
- `AudioSource`: Represents a YouTube URL or local file
- `AudioFile`: Represents an audio file with format
- `SeparatedAudio`: Container for separated stems (vocals, drums, bass, other)
- `ProcessingJob`: Aggregates the entire processing workflow
- Enums: `AudioFormat`, `ProcessingStatus`

**Domain Services** (`services.py`):
- `IAudioDownloader`: Protocol for downloading audio
- `IAudioConverter`: Protocol for audio conversion
- `IAudioSeparator`: Protocol for source separation
- `AudioProcessingService`: Coordination service

#### 2. Application Layer (`src/application/`)

**Use Cases** (`use_cases.py`):
- `DownloadAudioUseCase`: Download audio from YouTube
- `ProcessAudioUseCase`: Full workflow (download → convert → split)
- `ProcessLocalFileUseCase`: Process local audio files

**DTOs** (`dtos.py`):
- `DownloadRequest`, `ProcessRequest`, `LocalFileProcessRequest`
- `ProcessingProgress`, `ProcessingResult`

#### 3. Infrastructure Layer (`src/infrastructure/`)

**External Service Implementations**:
- `YtDlpDownloader` (`downloader.py`): YouTube download via yt-dlp
- `FfmpegConverter` (`converter.py`): Audio conversion via FFmpeg
- `DemucsSeparator` (`separator.py`): Source separation via Demucs
- `ExecutableResolver` (`executable_resolver.py`): Path resolution for bundled apps

#### 4. Presentation Layer (`src/presentation/`)

**GUI Components** (`main_window.py`):
- `MainWindow`: Main application window
- Handles user input and displays progress
- Thread management for async operations
- Delegates to use cases for business logic

### Dependency Flow

```
Presentation → Application → Domain ← Infrastructure
                                ↑
                                └─ Implements Domain Protocols
```

**Key Principles Applied**:
- **Dependency Inversion**: Domain defines interfaces; Infrastructure implements them
- **Separation of Concerns**: Each layer has a single responsibility
- **Testability**: Use cases can be tested independently
- **Flexibility**: Easy to swap implementations (e.g., different downloaders)

### Legacy Architecture (SPLYT.py)

The original monolithic implementation in `SPLYT.py` contains:

#### YouTubeDownloader Class (SPLYT.py:11-504)
- UI initialization and layout
- User interactions
- Multi-threaded processing
- Process cancellation

#### Key Methods
- `download_audio()` (SPLYT.py:158-206): Downloads audio from YouTube
- `convert_audio()` (SPLYT.py:208-251): Converts audio to WAV format
- `split_audio()` (SPLYT.py:253-297): Separates audio into stems
- Thread management methods for different workflows

**Note**: The legacy version is retained for backward compatibility but the DDD version (`main.py`) is recommended for new development.

### UI Components

- URL input field with default value
- Quality selector (WAV/MP3 radio buttons)
- Operation mode selector (Download Only / Download and Split)
- Output directory selector with Finder integration
- Local file selector
- Cancel button with process termination
- Status display with terminal-style formatting

## Dependencies

### Python Packages
```
pytube==12.1.0       # YouTube download
pydub==0.25.1        # Audio manipulation
demucs==4.0.1        # AI source separation
PyQt6                # GUI framework
```

### External Tools
- `ffmpeg`: Audio conversion and processing
- `yt-dlp`: YouTube video/audio download

## Installation

### Prerequisites
```bash
brew install ffmpeg
brew install yt-dlp
```

### Python Environment
```bash
python3 -m venv ../Youtube-Audio-Splitter
source ../Youtube-Audio-Splitter/bin/activate
pip3 install -r requirements.txt
```

## Usage

### Running the Application

**DDD Architecture (Recommended)**:
```bash
python3 main.py
```

**Legacy Version**:
```bash
python3 SPLYT.py
```

### Workflow Options

**Option 1: Download and Split**
1. Enter YouTube URL
2. Select quality (WAV/MP3)
3. Choose output directory
4. Click "Download and Split"
5. Process: Download → Convert → Split

**Option 2: Download Only**
1. Enter YouTube URL
2. Select quality
3. Choose output directory
4. Select "Download Only" radio button
5. Click "Download Only"

**Option 3: Process Local File**
1. Choose output directory
2. Click "Select Local File to split"
3. Select WAV or MP3 file
4. Process: Convert → Split

## File Structure

```
Youtube-Audio-Splitter/
├── main.py                          # New DDD entry point (RECOMMENDED)
├── SPLYT.py                         # Legacy monolithic application
├── src/                             # DDD architecture source code
│   ├── domain/                      # Domain layer (business logic core)
│   │   ├── entities.py              # Domain entities and value objects
│   │   └── services.py              # Domain service interfaces
│   ├── application/                 # Application layer (use cases)
│   │   ├── dtos.py                  # Data Transfer Objects
│   │   └── use_cases.py             # Business workflows
│   ├── infrastructure/              # Infrastructure layer (external services)
│   │   ├── downloader.py            # yt-dlp implementation
│   │   ├── converter.py             # FFmpeg implementation
│   │   ├── separator.py             # Demucs implementation
│   │   └── executable_resolver.py   # Executable path resolver
│   └── presentation/                # Presentation layer (GUI)
│       └── main_window.py           # PyQt6 main window
├── demucs_script.py                 # Demucs script (untracked)
├── demucs_script.spec               # PyInstaller spec (untracked)
├── requirements.txt                 # Python dependencies
├── setup.py                         # Setup configuration
├── memo.txt                         # Development notes
├── README.md                        # User documentation
└── CLAUDE.md                        # This file (AI assistant reference)
```

## Output Structure

Default output directory: `~/Documents/Demucs_Cuts`

Output format:
```
Demucs_Cuts/
├── [video_title].wav              # Converted audio
└── htdemucs/[video_title]/        # Separated stems
    ├── vocals.wav
    ├── drums.wav
    ├── bass.wav
    └── other.wav
```

## Process Flow

### Full Workflow (Download and Split)
```
1. Download Audio (yt-dlp)
   ↓
2. Convert to WAV (ffmpeg)
   ↓
3. Separate Stems (demucs)
   ↓
4. Output individual tracks
```

### Cancellation Support
- Each processing stage checks `cancel_requested` flag
- Processes can be terminated at any stage
- Process cleanup handled in finally blocks

## Threading Model

- Main thread: GUI event loop
- Worker threads: Processing operations
- Thread-safe status updates using `QMetaObject.invokeMethod()`
- Mutex-free design using simple boolean flags

## Error Handling

- Subprocess return code checking
- File existence validation with retry logic (max 100 retries)
- Graceful degradation on conversion skip
- User-friendly error messages in status display

## Platform Support

Primary: macOS (Darwin)
- Uses macOS-specific commands (`open` for Finder)
- Cross-platform support for Windows (`explorer`) and Linux (`xdg-open`)

## Development Status

Current branch: `main`

Recent commits:
- d67aef5: Update requirements.txt
- b636382: ローカルファイル対応 (Local file support)
- 41b071b: Update README.md

Untracked files:
- demucs_script.py
- demucs_script.spec

## Code Quality Notes

### DDD Architecture Strengths
- **Clean Architecture**: Clear separation across 4 layers
- **SOLID Principles**: Dependency inversion, single responsibility
- **Type Safety**: Comprehensive type hints using Python 3.12 features
- **Testability**: Use cases isolated from infrastructure
- **Protocol-based Design**: Easy to mock and test
- **Domain-Driven**: Business logic centralized in domain entities
- **Cancellation Support**: Built into use cases via cancellation tokens

### Legacy Code (SPLYT.py) - Strengths
- Robust cancellation mechanism
- Good error handling with try/except blocks
- User-friendly status updates

### Legacy Code - Technical Debt
- Monolithic class (500+ lines)
- Hardcoded default URL (SPLYT.py:26)
- Magic numbers (retry count, delays)
- Mixed concerns (UI + business logic + infrastructure)
- Limited testability
- No type hints

## Security Considerations

- No URL validation on user input
- Subprocess commands constructed from user input (potential injection)
- No sandboxing of external tool execution
- File path validation could be improved

## Performance Characteristics

- CPU-bound operation (Demucs uses CPU, not GPU by default)
- I/O bound for download and file operations
- Processing time depends on audio length
- WAV format is slower but higher quality than MP3

## Future Enhancement Possibilities

### High Priority
1. **Unit Tests**: Add comprehensive test coverage for use cases
2. **Integration Tests**: Test infrastructure implementations
3. **GPU Acceleration**: Enable GPU support for Demucs (currently CPU-only)
4. **Dependency Injection Container**: Add a DI container for better composition

### Medium Priority
5. **Batch Processing**: Process multiple files/URLs at once
6. **Progress Reporting**: Enhanced progress bars with ETA
7. **Repository Pattern**: Add persistence layer for job history
8. **Event Sourcing**: Track processing events for audit trail

### Low Priority
9. **Custom Stem Selection**: Choose which stems to separate
10. **Audio Preview**: Preview separated stems in-app
11. **Drag-and-Drop**: File drag-and-drop support
12. **Playlist Support**: Download entire YouTube playlists
13. **Model Selection**: Choose different Demucs models
14. **Configuration Management**: User preferences and settings

### Architecture Improvements
- **CQRS Pattern**: Separate read/write operations if needed
- **Saga Pattern**: For complex multi-step workflows
- **Factory Pattern**: For creating domain entities
- **Strategy Pattern**: For different separation algorithms

## Troubleshooting

### Common Issues
1. **Download fails**: Check yt-dlp is up to date
2. **Conversion fails**: Verify ffmpeg installation
3. **Split fails**: Ensure sufficient disk space
4. **Process hangs**: Use cancel button, check system resources

### Debug Information
- Console output shows detailed process logs
- Status label shows current operation stage
- Process return codes logged on error

## Migration Guide (Legacy → DDD)

### Key Differences

| Aspect | Legacy (SPLYT.py) | DDD (main.py) |
|--------|-------------------|---------------|
| Architecture | Monolithic | 4-layer (Domain/App/Infra/Presentation) |
| Lines of Code | ~500 in 1 file | ~1500 across 9 files |
| Testability | Low | High |
| Type Safety | None | Full type hints |
| Reusability | Low | High |
| Maintainability | Medium | High |

### How to Switch

1. **No code changes needed** - Both versions use the same dependencies
2. **Run new version**: `python3 main.py` instead of `python3 SPLYT.py`
3. **Same UI** - Identical user experience
4. **Same output** - Produces identical results

### For Developers

**Testing Use Cases**:
```python
from src.application.use_cases import ProcessAudioUseCase
from src.infrastructure import YtDlpDownloader, FfmpegConverter, DemucsSeparator

# Create dependencies
downloader = YtDlpDownloader()
converter = FfmpegConverter()
separator = DemucsSeparator()

# Create use case
use_case = ProcessAudioUseCase(downloader, converter, separator)

# Execute (easily testable!)
result = use_case.execute(request)
```

**Mocking for Tests**:
```python
# Easy to mock infrastructure
class MockDownloader:
    def download(self, source, output_dir, format):
        return AudioFile(path=Path("fake.wav"), format=AudioFormat.WAV)

# Inject mock
use_case = ProcessAudioUseCase(
    downloader=MockDownloader(),
    converter=mock_converter,
    separator=mock_separator
)
```

## Design Patterns Used

### Domain Layer
- **Entity Pattern**: `ProcessingJob`, `AudioFile`, `SeparatedAudio`
- **Value Object Pattern**: `AudioSource`, `AudioFormat`
- **Protocol Pattern**: `IAudioDownloader`, `IAudioConverter`, `IAudioSeparator`

### Application Layer
- **Use Case Pattern**: `ProcessAudioUseCase`, `ProcessLocalFileUseCase`
- **DTO Pattern**: `ProcessRequest`, `ProcessingResult`
- **Callback Pattern**: Progress reporting via callbacks

### Infrastructure Layer
- **Adapter Pattern**: Infrastructure implements domain protocols
- **Strategy Pattern**: Different executables resolved based on environment

### Presentation Layer
- **MVC Pattern**: Separation of view logic and business logic
- **Observer Pattern**: Qt signals/slots for UI updates

---

**Last Updated**: 2025-11-09
**Python Version**: 3.12.4
**Platform**: macOS (Darwin 24.3.0)
**Architecture Version**: DDD v1.0 (main.py) / Legacy v1.0 (SPLYT.py)
