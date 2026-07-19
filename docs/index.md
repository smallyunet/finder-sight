---
layout: default
---

# Finder Sight

Finder Sight is a native macOS app that finds local images using another image as the query.

[User Guide](./guide) · [GitHub Repository](https://github.com/smallyunet/finder-sight)

## Native macOS experience

- SwiftUI sidebar, unified toolbar, Settings scene, and system menus
- Drag and drop, clipboard search, Finder reveal, and native context menus
- Dark Mode, accent colors, keyboard navigation, and accessibility support

## Private perceptual search

Finder Sight builds a compact 256-bit perceptual hash for each local image. Search and duplicate detection happen entirely on your Mac; images are never uploaded.

## Quick start

1. Download `FinderSight-macOS.dmg` from the latest GitHub Release.
2. Drag Finder Sight into Applications.
3. Add an image folder with `⌘O`.
4. Drop or paste an image to search.

## Build from source

```bash
git clone https://github.com/smallyunet/finder-sight.git
cd finder-sight
make test
make dmg
```

Requires macOS 13 or later and a Swift 6 toolchain.
