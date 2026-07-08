"""Settings dialog for configuring application preferences."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QSpinBox, QPushButton, QGroupBox, QFormLayout, QSlider
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

from src.finder_sight.constants import DEFAULT_MAX_RESULTS, DEFAULT_SIMILARITY_THRESHOLD


class SettingsDialog(QDialog):
    """Dialog for configuring application settings."""
    
    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(350)
        self.setModal(True)
        
        # Load current settings or use defaults
        settings = current_settings or {}
        self.similarity_threshold = settings.get('similarity_threshold', DEFAULT_SIMILARITY_THRESHOLD)
        self.max_results = settings.get('max_results', DEFAULT_MAX_RESULTS)
        self.available_update = None
        self.downloaded_update_path = None
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the settings dialog UI."""
        layout = QVBoxLayout(self)
        
        # Search Settings Group
        search_group = QGroupBox("Search Settings")
        search_layout = QFormLayout()
        
        # Similarity Threshold (Match Percentage)
        threshold_layout = QHBoxLayout()
        
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(0, 100)
        self.threshold_slider.setValue(self.similarity_threshold)
        self.threshold_slider.setTickInterval(10)
        self.threshold_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(0, 100)
        self.threshold_spin.setValue(self.similarity_threshold)
        self.threshold_spin.setSuffix("%")
        self.threshold_spin.setFixedWidth(70)
        
        # Connect signals to synchronize slider and spinbox
        self.threshold_slider.valueChanged.connect(self.threshold_spin.setValue)
        self.threshold_spin.valueChanged.connect(self.threshold_slider.setValue)
        
        self.threshold_spin.setToolTip(
            "Minimum similarity percentage required.\n"
            "100% = Exact match only.\n"
            "0% = Show all results."
        )
        self.threshold_slider.setToolTip(self.threshold_spin.toolTip())
        
        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(self.threshold_spin)
        search_layout.addRow("Minimum Match Score:", threshold_layout)
        
        # Max Results
        self.max_results_spin = QSpinBox()
        self.max_results_spin.setRange(1, 100)
        self.max_results_spin.setValue(self.max_results)
        self.max_results_spin.setToolTip("Maximum number of search results to display.")
        search_layout.addRow("Max Results:", self.max_results_spin)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # About Group
        about_group = QGroupBox("About")
        about_layout = QVBoxLayout()
        
        # Version Info
        from src.finder_sight import __version__ as APP_VERSION
        version_layout = QHBoxLayout()
        version_layout.addWidget(QLabel(f"Current Version: <b>{APP_VERSION}</b>"))
        version_layout.addStretch()
        about_layout.addLayout(version_layout)
        
        # Update Check
        update_layout = QHBoxLayout()
        self.btn_check_update = QPushButton("Check for Updates")
        self.btn_check_update.clicked.connect(self.on_update_button_clicked)
        self.lbl_update_status = QLabel("")
        self.lbl_update_status.setStyleSheet("color: #86868b; font-size: 11px;")
        
        update_layout.addWidget(self.btn_check_update)
        update_layout.addWidget(self.lbl_update_status)
        update_layout.addStretch()
        
        about_layout.addLayout(update_layout)
        about_group.setLayout(about_layout)
        layout.addWidget(about_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)
        
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setDefault(True)
        self.btn_ok.clicked.connect(self.accept)
        button_layout.addWidget(self.btn_ok)
        
        layout.addLayout(button_layout)
        
    def on_update_button_clicked(self):
        if self.downloaded_update_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.downloaded_update_path))
        elif self.available_update:
            self.download_update(self.available_update)
        else:
            self.check_updates()

    def check_updates(self):
        self.downloaded_update_path = None
        self.btn_check_update.setEnabled(False)
        self.lbl_update_status.setText("Checking...")
        
        from src.finder_sight.utils.updater_thread import UpdateCheckThread
        self.update_thread = UpdateCheckThread()
        self.update_thread.finished.connect(self.on_update_checked)
        self.update_thread.start()
        
    def on_update_checked(self, available, latest, url, error=""):
        self.btn_check_update.setEnabled(True)
        if available:
            self.available_update = latest
            self.btn_check_update.setText("Download Update")
            self.lbl_update_status.setStyleSheet("color: #007AFF; font-weight: bold;")
            self.lbl_update_status.setText(f"New version {latest} available.")
        elif error:
            self.lbl_update_status.setText(f"Update check failed: {error}")
            self.lbl_update_status.setStyleSheet("color: #d70015;")
        else:
            self.lbl_update_status.setText("You are up to date.")
            self.lbl_update_status.setStyleSheet("color: #34C759;")

    def download_update(self, latest):
        self.btn_check_update.setEnabled(False)
        self.lbl_update_status.setText("Downloading...")

        from src.finder_sight.utils.updater_thread import UpdateDownloadThread
        self.download_thread = UpdateDownloadThread(latest, self)
        self.download_thread.progress.connect(self.on_download_progress)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.error.connect(self.on_download_error)
        self.download_thread.start()

    def on_download_progress(self, downloaded, total):
        if total:
            pct = int(downloaded / total * 100)
            self.lbl_update_status.setText(f"Downloading... {pct}%")
        else:
            self.lbl_update_status.setText("Downloading...")

    def on_download_finished(self, dmg_path):
        self.btn_check_update.setEnabled(True)
        self.btn_check_update.setText("Open Installer")
        self.available_update = None
        self.downloaded_update_path = dmg_path
        self.lbl_update_status.setText("Downloaded. Opening installer...")
        QDesktopServices.openUrl(QUrl.fromLocalFile(dmg_path))

    def on_download_error(self, error):
        self.btn_check_update.setEnabled(True)
        self.lbl_update_status.setText(f"Download failed: {error}")
        self.lbl_update_status.setStyleSheet("color: #d70015;")

    def get_settings(self) -> dict:
        """Return the current settings from the dialog."""
        return {
            'similarity_threshold': self.threshold_spin.value(),
            'max_results': self.max_results_spin.value()
        }
