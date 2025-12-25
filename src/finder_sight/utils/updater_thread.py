from PyQt6.QtCore import QThread, pyqtSignal
from src.finder_sight.utils.updater import check_for_updates
from src.finder_sight import __version__ as APP_VERSION

class UpdateCheckThread(QThread):
    finished = pyqtSignal(bool, str, str, str) # update_available, latest_version, url, error_msg

    def run(self):
        # Hardcoded for now
        owner = "smallyunet"
        repo = "finder-sight"
        available, latest, url, error = check_for_updates(APP_VERSION, owner, repo)
        self.finished.emit(available, latest, url, error or "")
