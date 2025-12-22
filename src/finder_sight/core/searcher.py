from typing import Any

from PyQt6.QtCore import QThread, pyqtSignal

from src.finder_sight.constants import DEFAULT_MAX_RESULTS, DEFAULT_SIMILARITY_THRESHOLD
from src.finder_sight.utils.logger import logger


class SearchThread(QThread):
    """
    Background thread for searching to prevent UI freeze.
    """
    finished = pyqtSignal(list)  # list of (path, distance)
    progress = pyqtSignal(int, int)  # current, total
    error = pyqtSignal(str)

    def __init__(
        self,
        image_hashes: dict[str, Any],
        target_hash: Any,
        max_results: int = DEFAULT_MAX_RESULTS,
        similarity_threshold: int = DEFAULT_SIMILARITY_THRESHOLD,  # Use default similarity threshold
        use_phash: bool = True  # New flag to select hash algorithm
    ) -> None:
        super().__init__()
        self.image_hashes = image_hashes
        self.target_hash = target_hash
        self.max_results = max_results
        self.similarity_threshold = similarity_threshold
        self.use_phash = use_phash

    def run(self) -> None:
        results: list[tuple[str, int]] = []
        total = len(self.image_hashes)

        try:
            for i, (path, h) in enumerate(self.image_hashes.items()):
                if self.isInterruptionRequested():
                    logger.info("Search interrupted by user")
                    return

                try:
                    # Determine distance based on selected hash algorithm
                    if self.use_phash:
                        # h and target_hash are assumed to be ImageHash objects (phash)
                        dist = h - self.target_hash
                    else:
                        # For crop_resistant_hash, use Hamming distance as well (hash objects support subtraction)
                        dist = h - self.target_hash

                    # If similarity_threshold is negative, treat as no-match (skip all results)
                    if self.similarity_threshold < 0:
                        continue

                    # Include only if distance is within the threshold
                    if dist <= self.similarity_threshold:
                        results.append((path, dist))
                except Exception as e:
                    logger.debug(f"Failed to compare hash for {path}: {e}")
                    continue

                # Emit progress every 50 items
                if (i + 1) % 50 == 0 or i == total - 1:
                    self.progress.emit(i + 1, total)

            # Sort by distance (ascending)
            results.sort(key=lambda x: x[1])

            # If no results meet the threshold and the threshold is non-negative, fallback to nearest max_results
            if not results and self.similarity_threshold >= 0:
                # Calculate distances for ALL items to find the nearest ones
                fallback: list[tuple[str, int]] = []
                for path, h in self.image_hashes.items():
                    try:
                        # Determine distance based on selected hash algorithm
                        # We repeat the calculation here to be sure, or we could have stored them.
                        # Since we want to find the BEST fallback, we must check everything.
                        if self.use_phash:
                            dist = h - self.target_hash
                        else:
                            dist = h - self.target_hash
                        fallback.append((path, dist))
                    except Exception as e:
                        # Skip invalid hashes
                        continue
                
                # Sort fallback results by distance
                fallback.sort(key=lambda x: x[1])
                # Take top N
                results = fallback[:self.max_results]



            # Return top N results (already limited by max_results)
            self.finished.emit(results[:self.max_results])
            logger.info(f"Search completed, found {len(results)} matches (including fallback if needed)")

        except Exception as e:
            logger.error(f"Search failed: {e}")
            self.error.emit(str(e))
