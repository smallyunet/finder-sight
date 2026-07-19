---
layout: default
title: User Guide
---

# Finder Sight User Guide

Finder Sight is a native macOS image finder. Every image stays on your Mac.

## Add your library

Choose **File → Add Folder** (`⌘O`) and select one or more image folders. Finder Sight indexes them immediately. Use **Library → Update Index** (`⌘I`) after adding or changing files.

The sidebar shows indexing progress and the number of indexed images. Your folder list and index persist between launches.

## Search

- Drag an image into the drop zone.
- Click the drop zone and choose an image.
- Copy an image or image file and press `⌘V`.

Matches are ranked by perceptual similarity. Double-click a result to reveal it in Finder. Right-click for Open, Reveal, and Copy Path actions.

## Find duplicates

Choose **Library → Find Duplicates** (`⌘D`). Exact perceptual-hash matches are grouped together. Finder Sight ranks the highest-resolution and highest-quality image first.

**Move Duplicates to Trash** keeps the best image in every group and sends the others to the macOS Trash, where they remain recoverable.

## Settings

Open **Finder Sight → Settings** (`⌘,`) to change:

- Minimum match score
- Maximum number of search results
- Update checking

## Supported formats

JPEG, PNG, WebP, BMP, GIF, HEIC/HEIF, TIFF, and ICO files supported by the installed macOS ImageIO framework.

## Privacy

Finder Sight stores only file paths, metadata, and small perceptual hashes. It never uploads your images.
