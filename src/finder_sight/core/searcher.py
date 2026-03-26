import io
import heapq
from typing import Any, Optional

from PyQt6.QtCore import QThread, pyqtSignal
from PIL import Image
import imagehash

from src.finder_sight.constants import DEFAULT_MAX_RESULTS, DEFAULT_SIMILARITY_THRESHOLD, HASH_SIZE
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
        target_hash: Any = None,
        target_image_path: Optional[str] = None,
        target_image_bytes: Optional[bytes] = None,
        max_results: int = DEFAULT_MAX_RESULTS,
        similarity_threshold: int = DEFAULT_SIMILARITY_THRESHOLD,
        use_phash: bool = True 
    ) -> None:
        super().__init__()
        self.image_hashes = image_hashes
        self.target_hash = target_hash
        self.target_image_path = target_image_path
        self.target_image_bytes = target_image_bytes
        self.max_results = max_results
        self.similarity_threshold = similarity_threshold
        self.use_phash = use_phash

    def run(self) -> None:
        # Pre-process target hash if not provided
        if self.target_hash is None:
            try:
                if self.target_image_path:
                    logger.info("Computing hash for image path...")
                    with Image.open(self.target_image_path) as img:
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        self.target_hash = imagehash.whash(img, hash_size=HASH_SIZE)
                elif self.target_image_bytes:
                    logger.info("Computing hash for image bytes...")
                    pil_im = Image.open(io.BytesIO(self.target_image_bytes))
                    if pil_im.mode != 'RGB':
                        pil_im = pil_im.convert('RGB')
                    self.target_hash = imagehash.whash(pil_im, hash_size=HASH_SIZE)
                else:
                    raise ValueError("No target provided for search.")
            except Exception as e:
                logger.error(f"Failed to process target image: {e}")
                self.error.emit(str(e))
                return

        results: list[tuple[str, int]] = []
        closest_heap: list[tuple[int, str]] = []  # Max-heap storing (-distance, path)
        total = len(self.image_hashes)

        try:
            for i, (path, h) in enumerate(self.image_hashes.items()):
                if self.isInterruptionRequested():
                    logger.info("Search interrupted by user")
                    return

                try:
                    # Determine distance based on selected hash algorithm
                    dist = h - self.target_hash

                    # 1. Maintain a bounded max-heap of the top closest items
                    if len(closest_heap) < self.max_results:
                        heapq.heappush(closest_heap, (-dist, path))
                    else:
                        # If the heap is full, push only if distance is smaller than the largest in the heap
                        if -dist > closest_heap[0][0]:
                            heapq.heappushpop(closest_heap, (-dist, path))

                    # 2. Check if the distance meets the similarity threshold
                    if self.similarity_threshold >= 0 and dist <= self.similarity_threshold:
                        results.append((path, dist))
                except Exception as e:
                    logger.debug(f"Failed to compare hash for {path}: {e}")
                    continue

                # Emit progress every 50 items
                if (i + 1) % 50 == 0 or i == total - 1:
                    self.progress.emit(i + 1, total)

            # Sort threshold-passed results by distance (ascending)
            results.sort(key=lambda x: x[1])

            # If no results meet the threshold, fallback to the nearest ones we collected in the heap
            if not results and self.similarity_threshold >= 0:
                fallback = [(p, -d) for d, p in closest_heap]
                fallback.sort(key=lambda x: x[1])
                results = fallback

            # Return top N results
            self.finished.emit(results[:self.max_results])
            logger.info(f"Search completed, found {len(results)} fallback/matches")

        except Exception as e:
            logger.error(f"Search failed: {e}")
            self.error.emit(str(e))
