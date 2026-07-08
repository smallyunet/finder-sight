import os
from collections import defaultdict
from typing import Any, Optional

from PIL import Image
from PyQt6.QtCore import QThread, pyqtSignal

from src.finder_sight.utils.logger import logger


def find_duplicate_groups(
    image_hashes: dict[str, Any],
    directories: Optional[list[str]] = None,
) -> list[list[str]]:
    added_directories = [os.path.abspath(d) for d in directories or []]
    grouped_paths: dict[str, list[str]] = defaultdict(list)

    for path, image_hash in image_hashes.items():
        if not os.path.exists(path):
            continue
        if added_directories and not _is_in_added_directory(path, added_directories):
            continue

        grouped_paths[str(image_hash)].append(path)

    duplicate_groups = [
        sort_group_by_quality(paths)
        for paths in grouped_paths.values()
        if len(paths) > 1
    ]
    duplicate_groups.sort(
        key=lambda group: (-len(group), os.path.basename(group[0]).lower())
    )
    return duplicate_groups


def sort_group_by_quality(paths: list[str]) -> list[str]:
    return sorted(paths, key=lambda path: _quality_sort_key(path))


def image_quality_score(path: str) -> tuple[int, int, int, str]:
    """Best-effort quality score: pixels, file size, format priority, stable path."""
    pixel_count = 0
    try:
        with Image.open(path) as img:
            pixel_count = img.width * img.height
    except Exception:
        pixel_count = 0

    try:
        file_size = os.path.getsize(path)
    except OSError:
        file_size = 0

    ext = os.path.splitext(path)[1].lower()
    format_priority = {
        ".tif": 6,
        ".tiff": 6,
        ".png": 5,
        ".heic": 5,
        ".heif": 5,
        ".webp": 4,
        ".jpg": 3,
        ".jpeg": 3,
        ".bmp": 2,
        ".gif": 1,
    }.get(ext, 0)

    return pixel_count, file_size, format_priority, os.path.basename(path).lower()


def _quality_sort_key(path: str) -> tuple[int, int, int, str]:
    pixel_count, file_size, format_priority, name = image_quality_score(path)
    return -pixel_count, -file_size, -format_priority, name


def plan_duplicate_deletions(groups: list[list[str]]) -> tuple[list[str], dict[str, str]]:
    delete_paths: list[str] = []
    keepers: dict[str, str] = {}

    for group in groups:
        existing_paths = [path for path in group if os.path.exists(path)]
        if len(existing_paths) < 2:
            continue

        ranked_paths = sort_group_by_quality(existing_paths)
        keeper = ranked_paths[0]
        keepers[keeper] = keeper
        delete_paths.extend(ranked_paths[1:])

    return delete_paths, keepers


def _is_in_added_directory(path: str, directories: list[str]) -> bool:
    abs_path = os.path.abspath(path)
    for directory in directories:
        try:
            if os.path.commonpath([abs_path, directory]) == directory:
                return True
        except ValueError:
            continue
    return False


class DuplicateFinderThread(QThread):
    """Find visually duplicate images from the loaded index."""

    finished = pyqtSignal(list)  # list of duplicate groups: [[path, ...], ...]
    error = pyqtSignal(str)

    def __init__(
        self,
        image_hashes: dict[str, Any],
        directories: Optional[list[str]] = None,
    ) -> None:
        super().__init__()
        self.image_hashes = image_hashes
        self.directories = directories or []

    def run(self) -> None:
        try:
            duplicate_groups = find_duplicate_groups(self.image_hashes, self.directories)
            if self.isInterruptionRequested():
                logger.info("Duplicate scan interrupted by user")
                return

            logger.info(
                "Duplicate scan complete: %s groups, %s images",
                len(duplicate_groups),
                sum(len(group) for group in duplicate_groups),
            )
            self.finished.emit(duplicate_groups)
        except Exception as e:
            logger.error(f"Duplicate scan failed: {e}")
            self.error.emit(str(e))
