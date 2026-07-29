# Finder Sight Privacy

Finder Sight is designed to search local images without sending image data to a remote service.

## Local data processing

The following operations happen entirely on the Mac:

- discovering images in user-selected folders;
- computing perceptual hashes and Apple Vision feature prints;
- storing the local image index;
- comparing a query image with indexed images;
- identifying duplicate images; and
- moving user-selected duplicates to the macOS Trash.

Finder Sight does not upload images, thumbnails, feature data, file paths, search queries, or
search results.

## Local storage

Finder Sight stores its settings and image index under:

```text
~/Library/Application Support/FinderSight/
```

The index contains local file paths and derived image features. It remains on the Mac and can be
removed with the app's Clear Index command or by deleting the FinderSight application-support
directory.

## Network access

Finder Sight has no hosted backend and does not make background network requests.

The only application-initiated network request occurs when the user opens Settings and selects
**Check for Updates**. Finder Sight then sends an HTTPS GET request to:

```text
https://api.github.com/repos/smallyunet/finder-sight/releases/latest
```

The request contains the installed Finder Sight version in its User-Agent header. No image data,
file paths, image features, or persistent identifier are included.

Links to GitHub releases and the source repository open in the user's default browser only when
selected.

## Tracking and accounts

Finder Sight contains no:

- analytics or telemetry SDK;
- advertising;
- user account or authentication system;
- crash-reporting service;
- cloud storage integration;
- login item; or
- background daemon or helper service.

## Scope

This document describes the Finder Sight source code and official builds published from this
repository. Operating-system and GitHub privacy behavior are governed by their respective
providers.
