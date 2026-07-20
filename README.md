# Finder Sight

A native macOS app for finding local images with another image. Finder Sight indexes perceptual hashes on your Mac, then searches them without uploading anything.

## Features

- Native SwiftUI and AppKit interface
- Drag, choose, or paste an image to search
- Fast 256-bit perceptual hashing and local indexing
- Finder reveal and native context menus
- Exact duplicate groups with quality-aware cleanup to Trash
- Clear separation between true matches and closest fallback results
- Cancellable indexing with skipped-file reporting
- Asynchronous, memory-bounded thumbnail loading
- Dark Mode, macOS accent colors, keyboard shortcuts, and Settings scene
- Fully local processing

## Requirements

- macOS 13 Ventura or later
- Swift 6 toolchain for development

The release app is self-contained and does not require Python or third-party frameworks.

## Development

```bash
# Run focused core tests
make test

# Run the app from source
make run

# Build a native app bundle
make build

# Build the release DMG
make dmg
```

Standard XCTest coverage is also available through `swift test` on a stable Xcode toolchain.

## Keyboard shortcuts

- `⌘O`: Add an image folder
- `⌘I`: Update the index
- `⌘D`: Find duplicates
- `⌘V`: Search the clipboard image
- `⌘,`: Open Settings

## Data and migration

Finder Sight stores configuration and its native index in:

```text
~/Library/Application Support/FinderSight/
```

Version 0.2 reads the folder and search settings from earlier releases. It rebuilds the old Python index once using the new native hashing engine.

## Release

Pushing a `v*` tag runs tests, builds the native `.app`, creates `FinderSight-macOS.dmg`, and attaches it to a GitHub Release.

## License

MIT
