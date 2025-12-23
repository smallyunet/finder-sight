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
        Tuple of (file_path, hash_string or None if failed, mtime or None)
    """
    try:
        # Get mtime first
        mtime = os.path.getmtime(file_path)
        with Image.open(file_path) as img:
            # Convert to RGB to handle various image modes
            if img.mode != 'RGB':
                img = img.convert('RGB')
            # whash is generally more robust for resized/modified images
            h = imagehash.whash(img)
            return file_path, str(h), mtime
    except Exception as e:
        # Logging happens in main process, just return None
        return file_path, None, None


class IndexerThread(QThread):
    """
    Background thread: Uses ProcessPoolExecutor for parallel hashing.
    Also validates existing index entries and removes deleted files.
    """
    progress_update = pyqtSignal(int, int, str)  # current, total, current_file
    progress_update = pyqtSignal(int, int, str)  # current, total, current_file
    finished = pyqtSignal(dict, dict)  # index_data, mtime_data
    deleted_files = pyqtSignal(list)  # list of deleted file paths

    def __init__(
        self,
        directories: list[str],
        existing_index: Optional[dict[str, str]] = None,
        existing_mtimes: Optional[dict[str, float]] = None
    ) -> None:
        super().__init__()
        self.directories = directories
        self.existing_index = existing_index or {}
        self.existing_mtimes = existing_mtimes or {}
        self.is_running = True

    def run(self) -> None:
        index_data: dict[str, str] = {}
        mtime_data: dict[str, float] = {}
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
                elif path in self.existing_mtimes:
                     # Check if modified
                     try:
                         current_mtime = os.path.getmtime(path)
                         if current_mtime != self.existing_mtimes[path]:
                             # File modified, treat as "deleted" from VALID index, so we re-hash it later
                             # We don't remove from self.existing_index here effectively, but we ensure it gets into `image_files` list
                             # Actually, simpler: if modified, we just don't add to valid data, so it gets picked up by scanner?
                             # No, scanner checks "if full_path not in self.existing_index".
                             # So we must REMOVE it from self.existing_index if modified.
                             deleted_files.append(path) # This signals the UI to drop the old hash
                             logger.debug(f"File modified: {path}")
                     except OSError:
                         deleted_files.append(path)
            
            if deleted_files:
                logger.info(f"Found {len(deleted_files)} deleted/modified files in index")
                self.deleted_files.emit(deleted_files)
                # Cleanup local reference to force re-indexing
                for p in deleted_files:
                    if p in self.existing_index:
                        del self.existing_index[p]
            
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
                futures: list[Future[tuple[str, Optional[str], Optional[float]]]] = []
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
                        file_path, hash_str, mtime = future.result(timeout=30)
                        if hash_str and mtime:
                            index_data[file_path] = hash_str
                            mtime_data[file_path] = mtime
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
            self.finished.emit(index_data, mtime_data)

    def stop(self) -> None:
        """Stop the indexing thread."""
        self.is_running = False
        logger.info("Indexer stop requested")


class IndexLoaderThread(QThread):
    """
    Background thread to load index from JSON file and parse hashes.
    This prevents UI freeze during startup with large indices.
    """
    finished = pyqtSignal(dict, dict, dict)  # index_data, hash_data, mtime_data
    error = pyqtSignal(str)

    def __init__(self, index_file: str) -> None:
        super().__init__()
        self.index_file = index_file

    def run(self) -> None:
        if not os.path.exists(self.index_file):
            self.finished.emit({}, {}, {})
            return

        try:
            import json
            with open(self.index_file, 'r') as f:
                data = json.load(f)
            
            # Check version
            from src.finder_sight.constants import INDEX_VERSION
            
            # Support legacy (flat dict) vs new (versioned dict)
            if "version" in data and "data" in data:
                loaded_version = data["version"]
                index_data = data["data"]
                mtime_data = data.get("mtimes", {})
                
                if loaded_version != INDEX_VERSION:
                    logger.warning(f"Index version mismatch: {loaded_version} != {INDEX_VERSION}. Ignoring old index.")
                    self.finished.emit({}, {}, {})
                    return
            else:
                # Legacy file is treated as incompatible if we enforced versioning
                # But for migration we can check. Since we are moving phash -> whash, they are NOT compatible.
                # So we must drop legacy index.
                logger.warning("Legacy index detected. Ignoring incompatible index.")
                self.finished.emit({}, {}, {})
                return

            hash_data = {}
            for path, hash_str in index_data.items():
                try:
                    hash_data[path] = imagehash.hex_to_hash(hash_str)
                except Exception:
                    # Ignore invalid hashes
                    pass
            
            self.finished.emit(index_data, hash_data, mtime_data)
            
        except Exception as e:
            self.error.emit(str(e))
            
        except Exception as e:
            self.error.emit(str(e))
