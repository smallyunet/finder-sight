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

![Demo Screenshot](assets/screenshot_main.png)

1. **Build Index**: Add folders via the Sidebar ("+") to auto-index your library.
2. **Search**: Drag & drop an image or paste (`Cmd+V`) a screenshot.
3. **Get Result**: Double-click any match to reveal it in Finder.

---

## 🛠 Tech Stack

- **UI Framework**: PyQt6
- **Image Processing**: Pillow (PIL)
- **Core Algorithm**: ImageHash (Perceptual Hashing)
