---
layout: default
title: User Guide
---

# 📖 Finder Sight User Guide

Welcome to Finder Sight. This document will guide you through the installation, configuration, and efficient usage of this tool.

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Building Index](#2-building-index)
3. [Searching Images](#3-searching-images)
4. [FAQ](#4-faq)

---

## 1. Prerequisites

Finder Sight is a Python desktop application. You need to ensure that a Python environment is installed on your computer.

### System Requirements
- **OS**: macOS (Recommended), Windows/Linux (Core features supported, but Finder integration may be limited)
- **Python Version**: 3.9 or higher

### Installation Steps

1. **Download Source Code**
   If you are familiar with Git:
   ```bash
   git clone https://github.com/smallyunet/finder-sight.git
   ```
   Or click "Download ZIP" on the GitHub page and extract it.

2. **Install Dependencies**
   It is recommended to use a virtual environment to avoid polluting the global environment:
   ```bash
   cd finder-sight
   python3 -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run Application**
   ```bash
   python run.py
   ```

---

## 2. Building Index

Before searching, you need to tell Finder Sight where to look for images.

### Add Directory
1. Click the **"Add Directory"** button in the top-left corner.
2. Select a folder containing images (e.g., `~/Pictures` or your design assets folder).
3. You can add multiple different folders.

### Start Indexing
1. Click the **"Start Indexing"** button.
2. The progress bar will show the current status.
   - *Note: The first indexing might take some time depending on the number of images. The process calculates a "fingerprint" (Hash) for each image.*
3. Once completed, a popup will say "Indexing complete".

> **Tip**: Index data is saved locally in `image_index.json`. You don't need to re-index on the next launch unless you've added new images.

---

## 3. Searching Images

Finder Sight provides two extremely convenient ways to search.

### Method 1: Drag & Drop
If you have an image file (e.g., on your desktop or in a web browser):
1. **Drag** the image file directly into the Finder Sight main window.
2. Release the mouse, and the search starts immediately.

### Method 2: Clipboard Search (Copy & Paste)
This is the most efficient way, especially for web images or screenshots:
1. Take a screenshot (e.g., macOS `Cmd+Shift+4`) or right-click an image on a webpage and select "Copy Image".
2. Switch to the Finder Sight window.
3. Press **`Cmd+V`** (Paste).
4. The app will automatically read the image data from the clipboard and start searching.

### View Results
- **Match Found**:
  - The thumbnail of the original image found will be displayed.
  - A match score is shown. Lower score means less difference (0 means identical).
  - Click the **"Reveal in Finder"** button to automatically open Finder and highlight the file.
  
- **Not Found**:
  - The interface shows "No matching image found".
  - This might mean the original image is not in your indexed folders, or the image is too heavily modified (e.g., excessive cropping).

---

## 4. FAQ

**Q: Which image formats are supported?**  
A: Currently supports `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`.

**Q: I added new images, why can't I find them?**  
A: In the current version, you need to manually click "Start Indexing" to update the index. We are working on an automatic file monitoring feature.

**Q: Is the index file large?**  
A: No. The index only stores image hashes and paths, not the images themselves. An index for 10,000 images is usually only a few MBs.

**Q: Why can't I find an image even if it's the same one?**  
A: Finder Sight uses a crop-resistant hash algorithm, but if the image is significantly rotated (e.g., 90 degrees) or has extreme perspective distortion, matching might fail.
