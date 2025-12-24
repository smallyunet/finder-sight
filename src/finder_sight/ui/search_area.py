from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
                             QLabel, QPushButton, QHBoxLayout, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QImageReader

import os
from src.finder_sight.ui.widgets import DropLabel, ResultWidget
from src.finder_sight.constants import THUMBNAIL_SIZE

class SearchArea(QWidget):
    # Signals
    image_dropped = pyqtSignal(str) # Path
    image_pasted = pyqtSignal(object) # QImage
    result_double_clicked = pyqtSignal(str) # Path
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # --- Drag & Drop Zone ---
        # Container for relative positioning of the "X" button if needed, 
        # or simplified: The DropLabel itself is the zone.
        
        self.drop_zone = DropLabel("Drag Image Here\nor Paste (Cmd+V)")
        self.drop_zone.setObjectName("DropZone")
        self.drop_zone.setFixedHeight(200)
        self.drop_zone.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.drop_zone.dropped.connect(self.image_dropped.emit)
        
        layout.addWidget(self.drop_zone)
        
        # --- Results Section ---
        
        # Header / Status
        self.header_layout = QHBoxLayout()
        self.lbl_results_title = QLabel("Matches")
        self.lbl_results_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #1d1d1f;")
        self.header_layout.addWidget(self.lbl_results_title)
        
        self.header_layout.addStretch()
        
        layout.addLayout(self.header_layout)
        
        # Grid
        self.result_list = QListWidget()
        self.result_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.result_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.result_list.setSpacing(12)
        self.result_list.setMovement(QListWidget.Movement.Static)
        self.result_list.setIconSize(QSize(120, 140)) # Space for widget
        self.result_list.setFrameShape(QFrame.Shape.NoFrame)
        self.result_list.setStyleSheet("background: transparent;")
        self.result_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        layout.addWidget(self.result_list)
        
    def set_preview(self, path=None, image=None):
        if path:
            self.drop_zone.set_preview_image(file_path=path)
        elif image:
            self.drop_zone.set_preview_image(pixmap=QPixmap.fromImage(image))
            
    def set_searching_state(self, is_searching):
        self.drop_zone.set_searching(is_searching)
        if is_searching:
            self.lbl_results_title.setText("Searching...")
            self.result_list.clear()

    def show_results(self, results):
        """
        results: list of (path, distance) tuples
        """
        self.result_list.clear()
        
        if not results:
            self.lbl_results_title.setText("No Matches Found")
            # Maybe show an empty state graphic here?
            return
            
        self.lbl_results_title.setText(f"Found {len(results)} Matches")
        
        for path, dist in results:
            # Create Item
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, path)
            
            # Load Thumbnail 
            # (Note: In a real heavy app this should be async/lazy, but for now we do it here)
            pixmap = QPixmap()
            reader = QImageReader(path)
            # Request slightly larger than displayed for crispness
            reader.setScaledSize(QSize(150, 150)) 
            img = reader.read()
            if not img.isNull():
                pixmap = QPixmap.fromImage(img)
            
            # Create Widget
            widget = ResultWidget(path, dist, pixmap)
            item.setSizeHint(widget.sizeHint())
            
            self.result_list.addItem(item)
            self.result_list.setItemWidget(item, widget)

    def on_item_double_clicked(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.result_double_clicked.emit(path)

    def clear(self):
        self.drop_zone.clear_preview()
        self.result_list.clear()
        self.lbl_results_title.setText("Matches")
