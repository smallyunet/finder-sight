---
layout: default
title: User Guide
description: Learn how to index, search, and clean up local images with Finder Sight.
nav: guide
page_class: guide-page
permalink: /guide/
---

# Finder Sight User Guide

Finder Sight is a native macOS image finder. Every image stays on your Mac.

<div class="guide-callout">
  <strong>New to Finder Sight?</strong>
  Add a folder with <kbd>⌘O</kbd>, then drop an image into the search area.
  <a href="{{ site.download_url }}">Download the latest release</a>.
</div>

## Add your library

Choose **File → Add Folder** (`⌘O`) and select one or more image folders. Finder Sight indexes them immediately. Use **Library → Update Index** (`⌘I`) after adding or changing files.

The sidebar shows indexing progress and the number of indexed images. Your folder list and index persist between launches.

## Search

- Drag an image into the drop zone.
- Click the drop zone and choose an image.
- Copy an image or image file and press `⌘V`.

Matches combine perceptual hashes with local Apple Vision features. Solid borders are trimmed
before visual analysis, and full-image plus overlapping regional features help find an image
from a crop. Select a result to reveal it in Finder. Result cards show the containing folder,
and the context menu provides Open, Reveal, and Copy Path actions.

## Find duplicates

Choose **Library → Find Duplicates** (`⌘D`). Exact perceptual-hash matches are grouped together. Finder Sight ranks the highest-resolution and highest-quality image first.

Each duplicate card shows its dimensions and file size so you can see why Finder Sight selected the highest-quality copy. **Move Duplicates to Trash** keeps the best image in every group and sends the others to the macOS Trash, where they remain recoverable.

## Settings

Open **Finder Sight → Settings** (`⌘,`) to change:

- Minimum match score
- Maximum number of search results
- Manual update checking

## Supported formats

JPEG, PNG, WebP, BMP, GIF, HEIC/HEIF, TIFF, and ICO files supported by the installed macOS ImageIO framework.

## Privacy

Finder Sight stores only file paths, metadata, perceptual hashes, and on-device Apple Vision
feature data. It never uploads your images. The only app network request is a manual update
check against the public GitHub Releases API.

Read the full [privacy details](https://github.com/smallyunet/finder-sight/blob/main/PRIVACY.md)
and [security policy](https://github.com/smallyunet/finder-sight/blob/main/SECURITY.md).

## First launch

Finder Sight is currently ad-hoc signed and is not notarized with an Apple Developer ID.
If macOS blocks the first launch, right-click Finder Sight in Applications, choose **Open**,
then confirm **Open** in the system dialog.
