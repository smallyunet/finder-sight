from PyQt6.QtCore import QThread, pyqtSignal

class SearchThread(QThread):
    """
    Background thread for searching to prevent UI freeze
    """
    finished = pyqtSignal(str, int, float) # path, matches, distance (or None if not found)
    error = pyqtSignal(str)

    def __init__(self, image_hashes, target_hash):
        super().__init__()
        self.image_hashes = image_hashes
        self.target_hash = target_hash

    def run(self):
        best_match_path = None
        max_matches = 0
        min_dist = float('inf')

        try:
            for path, h in self.image_hashes.items():
                if self.isInterruptionRequested():
                    return

                try:
                    matches, dist = h.hash_diff(self.target_hash)
                    if matches > max_matches:
                        max_matches = matches
                        min_dist = dist
                        best_match_path = path
                    elif matches == max_matches and matches > 0:
                        if dist < min_dist:
                            min_dist = dist
                            best_match_path = path
                except:
                    continue
            
            if best_match_path and max_matches > 0:
                self.finished.emit(best_match_path, max_matches, min_dist)
            else:
                self.finished.emit(None, 0, 0.0)

        except Exception as e:
            self.error.emit(str(e))
