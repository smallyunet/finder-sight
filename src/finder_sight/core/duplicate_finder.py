import os
from collections import defaultdict
from typing import Any, Optional

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
        sorted(paths, key=lambda p: os.path.basename(p).lower())
        for paths in grouped_paths.values()
        if len(paths) > 1
    ]
    duplicate_groups.sort(
        key=lambda group: (-len(group), os.path.basename(group[0]).lower())
    )
    return duplicate_groups


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
