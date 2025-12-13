---
layout: default
---

# Finder Sight 🔍

**Finder Sight** is a local "Reverse Image Search" tool designed specifically for macOS. It helps you quickly locate original high-quality images from your massive local library using a blurred, cropped, or compressed query image.

[User Guide](./guide) | [GitHub Repository](https://github.com/smallyunet/finder-sight)

---

## ✨ Key Features

### 1. Privacy First
All indexing and searching processes run entirely locally. No internet connection is required, and your images are never uploaded to the cloud.

### 2. Powerful Perceptual Hashing
Powered by `ImageHash`'s crop-resistant algorithm, Finder Sight can accurately find the original image even if your search query is:
- ✂️ Cropped
- 📉 Compressed or Resized
- 🎨 Slightly Color-Modified

### 3. Seamless Finder Integration
Once an image is found, simply click "Reveal in Finder" to instantly select and highlight the file in macOS Finder.

### 4. Simple & Efficient
- **Drag & Drop**: Drag an image file directly into the window to search.
- **Clipboard Search**: Copy an image or screenshot, then press `Cmd+V` to search instantly.

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/smallyunet/finder-sight.git
cd finder-sight
pip install -r requirements.txt
```

### Run

```bash
python run.py
```

---

## 📸 Demo

> *(Place a GIF here demonstrating the drag-and-drop search process)*

1. **Build Index**: Add your image folders and click "Start Indexing".
2. **Search**: Take a screenshot or copy an image, then paste it into the app.
3. **Get Result**: Instant response with the file path.

---

## 🛠 Tech Stack

- **UI Framework**: PyQt6
- **Image Processing**: Pillow (PIL)
- **Core Algorithm**: ImageHash (Perceptual Hashing)
