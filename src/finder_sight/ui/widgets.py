from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent, QPixmap

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
        self.default_style = """
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                font-size: 24px;
                color: #555;
                background-color: #f9f9f9;
            }
            QLabel:hover {
                background-color: #f0f0f0;
                border-color: #888;
            }
        """
        self.drag_active_style = """
            QLabel {
                border: 2px dashed #2196F3;
                border-radius: 10px;
                font-size: 24px;
                color: #2196F3;
                background-color: #e3f2fd;
            }
        """
        self.preview_style = """
            QLabel {
                border: 2px solid #4CAF50;
                border-radius: 10px;
                background-color: #f5f5f5;
            }
        """
        self.setStyleSheet(self.default_style)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(self.drag_active_style)

    def dragLeaveEvent(self, event):
        if self._preview_pixmap:
            self.setStyleSheet(self.preview_style)
        else:
            self.setStyleSheet(self.default_style)
            
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
            max_size = min(self.width(), self.height()) - 20
            if max_size < 100:
                max_size = 150
            scaled = pixmap.scaled(
                QSize(max_size, max_size),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self._preview_pixmap = scaled
            self.setPixmap(scaled)
            self.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setStyleSheet(self.preview_style)

    def set_searching(self, searching: bool):
        if searching:
            self.setText("Searching...")
            self._preview_pixmap = None
            self.setStyleSheet("QLabel { background-color: #e6f3ff; border: 2px solid #2196F3; font-size: 24px; }")
        else:
            if self._preview_pixmap:
                self.setPixmap(self._preview_pixmap)
                self.setStyleSheet(self.preview_style)
            else:
                self.setText(self.default_title)
                self.setStyleSheet(self.default_style)

    def clear_preview(self):
        """Clear the preview and restore default state."""
        self._preview_pixmap = None
        self.setText(self.default_title)
        self.setStyleSheet(self.default_style)

