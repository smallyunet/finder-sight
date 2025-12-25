# Finder Sight (macOS Image Finder)

A macOS desktop application for "Reverse Image Search" that helps you find local image files using another image as a query.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Build Status](https://github.com/smallyunet/finder-sight/actions/workflows/ci.yml/badge.svg)

## Features

- **Smart Indexing**: Select directories to scan for images and build a local index.
- **Visual Search**: Drag and drop an image or paste from clipboard to find the original file.
- **Perceptual Matching**: Uses Perceptual Hashing (dhash) to find similar images even if they are resized, compressed, or slightly modified.
- **Finder Integration**: Reveal the found image directly in macOS Finder with a single click.
- **Privacy Focused**: All processing happens locally on your machine. No images are uploaded to the cloud.

## Download


You can download the latest pre-built version of Finder Sight for macOS from the [Releases](https://github.com/smallyunet/finder-sight/releases) page.


1. Download the `FinderSight-macOS.dmg` file.
2. Open the DMG and drag Finder Sight to your Applications folder.
3. **Note**: Since the app is not signed with an Apple Developer certificate, you may need to right-click the app and select "Open" for the first time.

## Requirements

- macOS (Recommended for Finder integration)
- Python 3.9+
- PyQt6
- Pillow
- ImageHash

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/smallyunet/finder-sight.git
   cd finder-sight
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the application**
   ```bash
   python run.py
   ```

2. **Build Index**
   - Click the "+" button in the Sidebar to add image folders.
   - Indexing starts automatically.
   - Use `File > Index Now` to manually update the index later.

3. **Search**
   - Drag an image file into the search area.
   - Or copy an image to your clipboard and press `Cmd+V`.

4. **Locate**
   - Matching images appear in the results list with similarity scores.
   - **Double-click** a result to reveal it in Finder.

## Development

### Running Tests

This project uses `pytest` for testing.

```bash
# Install test dependencies
pip install pytest pytest-qt

# Run tests
pytest tests/
```

### CI/CD

The project includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that automatically runs tests on every push and pull request to the `main` branch.

## License

MIT
