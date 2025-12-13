from PyQt6.QtCore import QThread, pyqtSignal

class SearchThread(QThread):
    """
    Background thread for searching to prevent UI freeze
    """
    finished = pyqtSignal(list) # list of (path, matches, distance)
    error = pyqtSignal(str)

    def __init__(self, image_hashes, target_hash, max_results=20):
        super().__init__()
        self.image_hashes = image_hashes
        self.target_hash = target_hash
        self.max_results = max_results

    def run(self):
        results = []

        try:
            for path, h in self.image_hashes.items():
                if self.isInterruptionRequested():
                    return

                try:
                    matches, dist = h.hash_diff(self.target_hash)
                    if matches > 0:
                        results.append((path, matches, dist))
                except:
                    continue
            
            # Sort by matches (desc) then distance (asc)
            results.sort(key=lambda x: (-x[1], x[2]))
            
            # Return top N results
            self.finished.emit(results[:self.max_results])

        except Exception as e:
            self.error.emit(str(e))
