import os
from typing import Optional

import imagehash
from PIL import Image
from PyQt6.QtCore import QThread, pyqtSignal
from concurrent.futures import ProcessPoolExecutor, Future

from src.finder_sight.constants import SUPPORTED_EXTENSIONS
from src.finder_sight.utils.logger import logger


def calculate_hash(file_path: str) -> tuple[str, Optional[str]]:
    """
    Top-level function for multiprocessing.
    Calculate perceptual hash for an image file.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Tuple of (file_path, hash_string or None if failed)
    """
    try:
        with Image.open(file_path) as img:
            # crop_resistant_hash is computationally expensive
            h = imagehash.crop_resistant_hash(img)
            return file_path, str(h)
    except Exception as e:
        # Logging happens in main process, just return None
        return file_path, None


class IndexerThread(QThread):
    """
    Background thread: Uses ProcessPoolExecutor for parallel hashing.
    Also validates existing index entries and removes deleted files.
    """
    progress_update = pyqtSignal(int, int, str)  # current, total, current_file
    finished = pyqtSignal(dict)
    deleted_files = pyqtSignal(list)  # list of deleted file paths

    def __init__(
        self,
        directories: list[str],
        existing_index: Optional[dict[str, str]] = None
    ) -> None:
        super().__init__()
        self.directories = directories
        self.existing_index = existing_index or {}
        self.is_running = True

    def run(self) -> None:
        index_data: dict[str, str] = {}
        try:
            image_files: list[str] = []
            deleted_files: list[str] = []
            
            # 1. Validate existing index - remove deleted files
            logger.info("Validating existing index...")
            for path in list(self.existing_index.keys()):
                if not self.is_running:
                    return
                if not os.path.exists(path):
                    deleted_files.append(path)
                    logger.debug(f"File no longer exists: {path}")
            
            if deleted_files:
                logger.info(f"Found {len(deleted_files)} deleted files in index")
                self.deleted_files.emit(deleted_files)
            
            # 2. Scan all files (Fast, IO bound)
            logger.info(f"Scanning {len(self.directories)} directories...")
            for directory in self.directories:
                for root, _, files in os.walk(directory):
                    for file in files:
                        if not self.is_running:
                            return
                        if os.path.splitext(file)[1].lower() in SUPPORTED_EXTENSIONS:
                            full_path = os.path.join(root, file)
                            if full_path not in self.existing_index:
                                image_files.append(full_path)
            
            total_files = len(image_files)
            
            if total_files == 0:
                logger.info("No new files to index")
                return

            logger.info(f"Found {total_files} new files to index")
            
            # 3. Calculate hashes in parallel (CPU bound)
            # Use max_workers=None to let it default to CPU count
            failed_count = 0
            with ProcessPoolExecutor() as executor:
                futures: list[Future[tuple[str, Optional[str]]]] = []
                for file_path in image_files:
                    if not self.is_running:
                        executor.shutdown(wait=False, cancel_futures=True)
                        logger.info("Indexing stopped before starting all tasks")
                        return
                    future = executor.submit(calculate_hash, file_path)
                    futures.append(future)
                
                for i, future in enumerate(futures):
                    if not self.is_running:
                        executor.shutdown(wait=False, cancel_futures=True)
                        logger.info(f"Indexing stopped at task {i+1}/{total_files}")
                        return
                    
                    try:
                        file_path, hash_str = future.result(timeout=30)
                        if hash_str:
                            index_data[file_path] = hash_str
                        else:
                            failed_count += 1
                            logger.debug(f"Failed to hash: {file_path}")
                    except Exception as e:
                        failed_count += 1
                        logger.warning(f"Error processing file: {e}")
                    
                    # Emit progress
                    self.progress_update.emit(i + 1, total_files, image_files[i])

            logger.info(
                f"Indexing complete: {len(index_data)} succeeded, {failed_count} failed"
            )
            
        except Exception as e:
            logger.error(f"Indexer error: {e}")
        finally:
            self.finished.emit(index_data)

    def stop(self) -> None:
        """Stop the indexing thread."""
        self.is_running = False
        logger.info("Indexer stop requested")


class IndexLoaderThread(QThread):
    """
    Background thread to load index from JSON file and parse hashes.
    This prevents UI freeze during startup with large indices.
    """
    finished = pyqtSignal(dict, dict)  # index_data, hash_data
    error = pyqtSignal(str)

    def __init__(self, index_file: str) -> None:
        super().__init__()
        self.index_file = index_file

    def run(self) -> None:
        if not os.path.exists(self.index_file):
            self.finished.emit({}, {})
            return

        try:
            import json
            with open(self.index_file, 'r') as f:
                index_data = json.load(f)
            
            hash_data = {}
            for path, hash_str in index_data.items():
                try:
                    hash_data[path] = imagehash.hex_to_multihash(hash_str)
                except Exception:
                    # Ignore invalid hashes
                    pass
            
            self.finished.emit(index_data, hash_data)
            
        except Exception as e:
            self.error.emit(str(e))
