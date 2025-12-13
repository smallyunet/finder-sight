from typing import Any

from PyQt6.QtCore import QThread, pyqtSignal

from src.finder_sight.constants import DEFAULT_MAX_RESULTS
from src.finder_sight.utils.logger import logger


class SearchThread(QThread):
    """
    Background thread for searching to prevent UI freeze.
    """
    finished = pyqtSignal(list)  # list of (path, matches, distance)
    error = pyqtSignal(str)

    def __init__(
        self,
        image_hashes: dict[str, Any],
        target_hash: Any,
        max_results: int = DEFAULT_MAX_RESULTS
    ) -> None:
        super().__init__()
        self.image_hashes = image_hashes
        self.target_hash = target_hash
        self.max_results = max_results

    def run(self) -> None:
        results: list[tuple[str, int, float]] = []

        try:
            for path, h in self.image_hashes.items():
                if self.isInterruptionRequested():
                    logger.info("Search interrupted by user")
                    return

                try:
                    matches, dist = h.hash_diff(self.target_hash)
                    if matches > 0:
                        results.append((path, matches, dist))
                except Exception as e:
                    logger.debug(f"Failed to compare hash for {path}: {e}")
                    continue

            # Sort by matches (desc) then distance (asc)
            results.sort(key=lambda x: (-x[1], x[2]))

            # Return top N results
            self.finished.emit(results[:self.max_results])
            logger.info(f"Search completed, found {len(results)} matches")

        except Exception as e:
            logger.error(f"Search failed: {e}")
            self.error.emit(str(e))
