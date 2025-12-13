# macOS Image Finder

A macOS desktop application for "Reverse Image Search" (finding a local image file using another image).

## Features

- **Indexing**: Select directories to scan for images and build a local index.
- **Search**: Drag and drop an image or paste from clipboard to find the original file.
- **Matching**: Uses Perceptual Hashing (dhash) to find similar images even if they are resized or slightly modified.
- **Action**: Reveal the found image directly in Finder.

## Requirements

- Python 3.9+
- PyQt6
- Pillow
- ImageHash

## Installation

1. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python main.py
   ```

2. Click "Add Directory" to select folders containing your images.
3. Click "Start Indexing" to build the index.
4. Drag an image into the drop zone or paste an image (Cmd+V) to search.
5. If a match is found, click "Reveal in Finder".

## License

MIT
# finder-sight
