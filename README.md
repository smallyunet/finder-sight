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
   - Click "Add Directory" to select folders containing your images (e.g., your Photos library export or specific work folders).
   - Click "Start Indexing" to scan and build the hash database.

3. **Search**
   - Drag an image file into the drop zone.
   - Or copy an image to your clipboard and press `Cmd+V` in the app.

4. **Locate**
   - If a match is found, a preview and path will be displayed.
   - Click "Reveal in Finder" to open the folder containing the image.

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
