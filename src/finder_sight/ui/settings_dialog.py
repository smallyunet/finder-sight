"""Settings dialog for configuring application preferences."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QSpinBox, QPushButton, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt

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
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the settings dialog UI."""
        layout = QVBoxLayout(self)
        
        # Search Settings Group
        search_group = QGroupBox("Search Settings")
        search_layout = QFormLayout()
        
        # Similarity Threshold
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(0, 100)
        self.threshold_spin.setValue(self.similarity_threshold)
        self.threshold_spin.setSuffix(" (min matches)")
        self.threshold_spin.setToolTip(
            "Minimum number of segment matches required.\n"
            "0 = show all results with any match.\n"
            "Higher values = stricter matching."
        )
        search_layout.addRow("Similarity Threshold:", self.threshold_spin)
        
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
        self.btn_check_update.clicked.connect(self.check_updates)
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
        
    def check_updates(self):
        self.btn_check_update.setEnabled(False)
        self.lbl_update_status.setText("Checking...")
        
        from src.finder_sight.utils.updater_thread import UpdateCheckThread
        self.update_thread = UpdateCheckThread()
        self.update_thread.finished.connect(self.on_update_checked)
        self.update_thread.start()
        
    def on_update_checked(self, available, latest, url):
        self.btn_check_update.setEnabled(True)
        if available:
            self.lbl_update_status.setText(f"New version {latest} available!")
            self.lbl_update_status.setStyleSheet("color: #007AFF; font-weight: bold;")
            # Maybe change button text or add a link
            from PyQt6.QtGui import QDesktopServices
            from PyQt6.QtCore import QUrl
            # We can't easily change the button action dynamically without disconnection
            # For simplicity, open URL if user clicks 'Check' again? No that's confusing.
            # Let's just open the URL immediately? Or show a dialog?
            # User asked for info on interface, not necessarily popup.
            # But let's keep it simple: Text link.
            self.lbl_update_status.setText(f"<a href='{url}'>New version {latest} available!</a>")
            self.lbl_update_status.setOpenExternalLinks(True)
        else:
            self.lbl_update_status.setText("You are up to date.")
            self.lbl_update_status.setStyleSheet("color: #34C759;")

    def get_settings(self) -> dict:
        """Return the current settings from the dialog."""
        return {
            'similarity_threshold': self.threshold_spin.value(),
            'max_results': self.max_results_spin.value()
        }
