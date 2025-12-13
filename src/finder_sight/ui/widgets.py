from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent

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
        self.setAcceptDrops(True)
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
        self.setStyleSheet(self.default_style)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(self.drag_active_style)

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self.default_style)
            
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet(self.default_style)
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.dropped.emit(file_path)

    def set_searching(self, searching: bool):
        if searching:
            self.setText("Searching...")
            self.setStyleSheet("QLabel { background-color: #e6f3ff; border: 2px solid #2196F3; }")
        else:
            self.setText("Drag & Drop Image Here\nor Paste (Cmd+V)")
            self.setStyleSheet(self.default_style)
