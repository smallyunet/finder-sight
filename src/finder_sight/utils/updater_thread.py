from PyQt6.QtCore import QThread, pyqtSignal
from src.finder_sight.utils.paths import get_user_data_dir
from src.finder_sight.utils.updater import (
    check_for_updates,
    download_update_asset,
    get_release_asset_download_url,
)
from src.finder_sight import __version__ as APP_VERSION

class UpdateCheckThread(QThread):
    finished = pyqtSignal(bool, str, str, str) # update_available, latest_version, url, error_msg

    def run(self):
        # Hardcoded for now
        owner = "smallyunet"
        repo = "finder-sight"
        available, latest, url, error = check_for_updates(APP_VERSION, owner, repo)
        self.finished.emit(available, latest, url, error or "")


class UpdateDownloadThread(QThread):
    progress = pyqtSignal(int, int)  # downloaded, total
    finished = pyqtSignal(str)  # destination path
    error = pyqtSignal(str)

    def __init__(self, latest_version: str, parent=None):
        super().__init__(parent)
        self.latest_version = latest_version

    def run(self):
        try:
            owner = "smallyunet"
            repo = "finder-sight"
            download_url, _ = get_release_asset_download_url(owner, repo, self.latest_version)
            downloads_dir = get_user_data_dir() / "updates"
            destination = downloads_dir / f"FinderSight-{self.latest_version}.dmg"

            def on_progress(downloaded, total):
                if self.isInterruptionRequested():
                    raise RuntimeError("Download cancelled")
                self.progress.emit(downloaded, total)

            download_update_asset(download_url, str(destination), on_progress)
            self.finished.emit(str(destination))
        except Exception as e:
            self.error.emit(str(e))
