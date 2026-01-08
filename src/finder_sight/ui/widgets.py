from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QSizePolicy, QStyle, QStyleOption, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent, QPixmap, QPainter
import os
from src.finder_sight.constants import MAX_HASH_DIST

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
    cleared = pyqtSignal()

    def __init__(self, title):
        super().__init__(title)
        self.default_title = title
        self.setAcceptDrops(True)
        self._preview_pixmap = None
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setProperty("state", "idle")
        self.setObjectName("DropZone") # Ensure object name is set for styling
        
        # Close Button
        self.btn_close = QPushButton("✕", self)
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.hide()
        self.btn_close.clicked.connect(self.on_close_clicked)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 0.5);
                color: white;
                border-radius: 12px;
                border: none;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.7);
            }
        """)

    def on_close_clicked(self):
        self.clear_preview()
        self.cleared.emit()

    def resizeEvent(self, event):
        # Position top-right
        self.btn_close.move(self.width() - 32, 8)
        super().resizeEvent(event)

    def paintEvent(self, event):
        """Override to respect stylesheet backgrounds and borders for custom widgets."""
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, painter, self)
        super().paintEvent(event)

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
            self.btn_close.show() # Show button
            self.style().unpolish(self)
            self.style().polish(self)

    def set_searching(self, searching: bool):
        if searching:
            self.clear() # Clear current display (text or pixmap)
            self.setText("🔍 Searching...")
            self.setProperty("state", "searching")
            self.btn_close.show() # keep showing to allow cancel/clear
        else:
            if self._preview_pixmap:
                self.setPixmap(self._preview_pixmap)
                self.setProperty("state", "preview")
                self.btn_close.show()
            else:
                self.setText(self.default_title)
                self.setProperty("state", "idle")
                self.btn_close.hide()
        
        self.style().unpolish(self)
        self.style().polish(self)

    def clear_preview(self):
        """Clear the preview and restore default state."""
        self._preview_pixmap = None
        self.setText(self.default_title)
        self.setProperty("state", "idle")
        self.btn_close.hide()
        self.style().unpolish(self)
        self.style().polish(self)


class ResultWidget(QWidget):
    def __init__(self, path: str, distance: float, pixmap: QPixmap):
        super().__init__()
        # Main layout - Vertical for Grid
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)
        
        # Thumbnail container
        self.thumb_container = QLabel()
        self.thumb_container.setObjectName("ResultThumbnail")
        self.thumb_container.setFixedSize(110, 110) # Slightly larger
        self.thumb_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                QSize(100, 100), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.thumb_container.setPixmap(scaled_pixmap)
        
        layout.addWidget(self.thumb_container, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Info container
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        file_name = os.path.basename(path)
        self.lbl_name = QLabel(file_name)
        self.lbl_name.setObjectName("ResultName")
        self.lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_name.setFixedWidth(110)
        
        # Simple truncation
        if len(file_name) > 16:
            self.lbl_name.setText(file_name[:13] + "...")
        else:
            self.lbl_name.setText(file_name)
            
        # Calculate match percentage
        # Similarity = 1 - (dist / MAX_HASH_DIST)
        percentage = max(0, 1.0 - (distance / MAX_HASH_DIST)) * 100
        
        self.lbl_dist = QLabel(f"{int(percentage)}% Match")
        self.lbl_dist.setObjectName("ResultScore")
        self.lbl_dist.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Color coding for match score
        if percentage >= 95:
             self.lbl_dist.setStyleSheet("color: #34C759; font-weight: bold;")
        elif percentage >= 80:
             self.lbl_dist.setStyleSheet("color: #007AFF;")
        else:
             self.lbl_dist.setStyleSheet("color: #8E8E93;")
        
        info_layout.addWidget(self.lbl_name)
        info_layout.addWidget(self.lbl_dist)
        
        layout.addLayout(info_layout)
        self.setToolTip(f"{path}\nDistance: {distance}")


