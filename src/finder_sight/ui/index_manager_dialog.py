from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QDesktopServices
from PyQt6.QtCore import QUrl
import os
import sys
import subprocess

class IndexManagerDialog(QDialog):
    clear_requested = pyqtSignal()
    
    def __init__(self, parent, index_path, count, last_modified):
        super().__init__(parent)
        self.setWindowTitle("Index Manager")
        self.setMinimumWidth(400)
        self.index_path = index_path
        self.count = count
        self.last_modified = last_modified
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Info Group
        info_group = QGroupBox("Index Information")
        form = QFormLayout()
        
        # Path
        lbl_path = QLabel(self.index_path)
        lbl_path.setWordWrap(True)
        lbl_path.setStyleSheet("color: #86868b; font-size: 11px;")
        
        btn_reveal = QPushButton("Reveal in Finder")
        btn_reveal.setFixedWidth(120)
        btn_reveal.clicked.connect(self.reveal_index_file)
        
        path_container = QVBoxLayout()
        path_container.addWidget(lbl_path)
        path_container.addWidget(btn_reveal)
        
        form.addRow("Location:", path_container)
        form.addRow("Images Indexed:", QLabel(str(self.count)))
        form.addRow("Last Modified:", QLabel(self.last_modified or "Never"))
        
        info_group.setLayout(form)
        layout.addWidget(info_group)
        
        # Actions Group
        action_group = QGroupBox("Actions")
        action_layout = QHBoxLayout()
        
        self.btn_clear = QPushButton("Clear Index")
        self.btn_clear.clicked.connect(self.on_clear_clicked)
        self.btn_clear.setStyleSheet("color: red;")
        
        action_layout.addWidget(self.btn_clear)
        action_layout.addStretch()
        
        action_group.setLayout(action_layout)
        layout.addWidget(action_group)
        
        # Close
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, 0, Qt.AlignmentFlag.AlignRight)
        
    def reveal_index_file(self):
        if not os.path.exists(self.index_path):
            QMessageBox.warning(self, "Error", "Index file does not exist yet.")
            return
            
        if sys.platform == 'darwin':
            subprocess.run(['open', '-R', self.index_path])
        elif os.name == 'nt':
            subprocess.run(['explorer', '/select,', os.path.normpath(self.index_path)])
        else:
            subprocess.run(['xdg-open', os.path.dirname(self.index_path)])

    def on_clear_clicked(self):
        reply = QMessageBox.question(
            self, 
            "Confirm Clear", 
            "Are you sure you want to clear the index? You will need to re-index your folders.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.clear_requested.emit()
            self.accept()
