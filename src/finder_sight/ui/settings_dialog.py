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
    
    def get_settings(self) -> dict:
        """Return the current settings from the dialog."""
        return {
            'similarity_threshold': self.threshold_spin.value(),
            'max_results': self.max_results_spin.value()
        }
