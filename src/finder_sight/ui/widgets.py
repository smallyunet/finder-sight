from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent, QPixmap
import os

class ClickableLabel(QLabel):

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class DropLabel(QLabel):
    dropped = pyqtSignal(str)

    def __init__(self, title):
        super().__init__(title)
        self.default_title = title
        self.setAcceptDrops(True)
        self._preview_pixmap = None
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setProperty("state", "idle")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("state", "dragging")
            self.style().unpolish(self)
            self.style().polish(self)

    def dragLeaveEvent(self, event):
        if self._preview_pixmap:
            self.setProperty("state", "preview")
        else:
            self.setProperty("state", "idle")
        self.style().unpolish(self)
        self.style().polish(self)
            
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.set_preview_image(file_path)
            self.dropped.emit(file_path)

    def set_preview_image(self, file_path: str = None, pixmap: QPixmap = None):
        """Show preview of the search image."""
        if file_path:
            pixmap = QPixmap(file_path)
        
        if pixmap and not pixmap.isNull():
            # Scale to fit while maintaining aspect ratio
            # Use smaller dimension to ensure it fits well
            max_size = min(self.width(), self.height()) - 40
            if max_size < 100:
                max_size = 150
            scaled = pixmap.scaled(
                QSize(max_size, max_size),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self._preview_pixmap = scaled
            self.setPixmap(scaled)
            self.setProperty("state", "preview")
            self.style().unpolish(self)
            self.style().polish(self)

    def set_searching(self, searching: bool):
        if searching:
            self.clear() # Clear current display (text or pixmap)
            self.setText("🔍 Searching...")
            self.setProperty("state", "searching")
        else:
            if self._preview_pixmap:
                self.setPixmap(self._preview_pixmap)
                self.setProperty("state", "preview")
            else:
                self.setText(self.default_title)
                self.setProperty("state", "idle")
        
        self.style().unpolish(self)
        self.style().polish(self)

    def clear_preview(self):
        """Clear the preview and restore default state."""
        self._preview_pixmap = None
        self.setText(self.default_title)
        self.setProperty("state", "idle")
        self.style().unpolish(self)
        self.style().polish(self)


class ResultWidget(QWidget):
    def __init__(self, path: str, distance: float, pixmap: QPixmap):
        super().__init__()
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(15)
        
        # Thumbnail container
        thumb_container = QLabel()
        thumb_container.setFixedSize(70, 70)
        thumb_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_container.setStyleSheet("""
            background-color: #f0f0f0; 
            border-radius: 6px; 
            border: 1px solid #e0e0e0;
        """)
        
        if not pixmap.isNull():
            # Scale pixmap to fit within container while preserving aspect ratio
            scaled_pixmap = pixmap.scaled(
                QSize(64, 64), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            thumb_container.setPixmap(scaled_pixmap)
        
        layout.addWidget(thumb_container)
        
        # Info container
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        info_layout.setContentsMargins(0, 2, 0, 2)
        
        # Filename
        file_name = os.path.basename(path)
        self.lbl_name = QLabel(file_name)
        self.lbl_name.setStyleSheet("font-size: 14px; font-weight: 600; color: #1d1d1f;")
        
        # Path
        self.lbl_path = QLabel(path)
        self.lbl_path.setStyleSheet("font-size: 12px; color: #86868b;")
        self.lbl_path.setWordWrap(False)
        self.lbl_path.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        # Distance / Score
        similarity_text = f"Similarity Distance: {distance:.2f}"
        self.lbl_dist = QLabel(similarity_text)
        self.lbl_dist.setStyleSheet("""
            font-size: 11px; 
            font-weight: 500; 
            color: #007AFF; 
            background-color: #e3f2fd; 
            border-radius: 4px; 
            padding: 2px 6px;
        """)
        self.lbl_dist.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        info_layout.addWidget(self.lbl_name)
        info_layout.addWidget(self.lbl_path)
        info_layout.addWidget(self.lbl_dist)
        info_layout.addStretch()
        
        layout.addLayout(info_layout)

