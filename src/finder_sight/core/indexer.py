import os
import imagehash
from PIL import Image
from PyQt6.QtCore import QThread, pyqtSignal
from concurrent.futures import ProcessPoolExecutor
from src.finder_sight.constants import SUPPORTED_EXTENSIONS

# Top-level function for multiprocessing
def calculate_hash(file_path):
    try:
        with Image.open(file_path) as img:
            # crop_resistant_hash is computationally expensive
            h = imagehash.crop_resistant_hash(img)
            return file_path, str(h)
    except Exception as e:
        return file_path, None

class IndexerThread(QThread):
    """
    Background thread: Uses ProcessPoolExecutor for parallel hashing
    """
    progress_update = pyqtSignal(int, int, str) # current, total, current_file
    finished = pyqtSignal(dict)

    def __init__(self, directories, existing_index=None):
        super().__init__()
        self.directories = directories
        self.existing_index = existing_index or {}
        self.is_running = True

    def run(self):
        image_files = []
        # 1. Scan all files (Fast, IO bound)
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
        index_data = {}
        
        if total_files == 0:
            self.finished.emit({})
            return

        # 2. Calculate hashes in parallel (CPU bound)
        # Use max_workers=None to let it default to CPU count
        with ProcessPoolExecutor() as executor:
            # Map returns an iterator that yields results as they complete if we iterate, 
            # but here we want to track progress, so we submit tasks.
            futures = []
            for file_path in image_files:
                if not self.is_running:
                    executor.shutdown(wait=False, cancel_futures=True)
                    return
                future = executor.submit(calculate_hash, file_path)
                futures.append(future)
            
            for i, future in enumerate(futures):
                if not self.is_running:
                    executor.shutdown(wait=False, cancel_futures=True)
                    return
                
                file_path, hash_str = future.result()
                if hash_str:
                    index_data[file_path] = hash_str
                
                # Emit progress
                self.progress_update.emit(i + 1, total_files, file_path)

        self.finished.emit(index_data)

    def stop(self):
        self.is_running = False
