from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QSizePolicy, QStyle, QStyleOption
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent, QPixmap, QPainter
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
        self.setObjectName("DropZone") # Ensure object name is set for styling

    def paintEvent(self, event):
        """Override to respect stylesheet backgrounds and borders for custom widgets."""
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, painter, self)
        super().paintEvent(event)
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
        # Main layout - Compact
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(10)
        
        # Thumbnail container (Smaller)
        thumb_container = QLabel()
        thumb_container.setFixedSize(42, 42)
        thumb_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_container.setStyleSheet("""
            background-color: #f0f0f0; 
            border-radius: 4px; 
            border: 1px solid #e0e0e0;
        """)
        
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                QSize(40, 40), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            thumb_container.setPixmap(scaled_pixmap)
        
        layout.addWidget(thumb_container)
        
        # Info container
        info_layout = QVBoxLayout()
        info_layout.setSpacing(0) # Minimal vertical spacing
        info_layout.setContentsMargins(0, 2, 0, 2)
        
        # Top Row: Name + Score
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        
        file_name = os.path.basename(path)
        self.lbl_name = QLabel(file_name)
        self.lbl_name.setStyleSheet("font-size: 13px; font-weight: 600; color: #1d1d1f;")
        
        similarity_text = f"Dist: {distance:.2f}"
        self.lbl_dist = QLabel(similarity_text)
        self.lbl_dist.setStyleSheet("""
            font-size: 11px; 
            font-weight: 500; 
            color: #007AFF; 
            padding: 0px 4px;
        """)
        self.lbl_dist.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        top_row.addWidget(self.lbl_name)
        top_row.addWidget(self.lbl_dist)
        top_row.addStretch()
        
        # Bottom Row: Path
        self.lbl_path = QLabel(path)
        self.lbl_path.setStyleSheet("font-size: 11px; color: #86868b;")
        self.lbl_path.setWordWrap(False)
        self.lbl_path.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        
        info_layout.addLayout(top_row)
        info_layout.addWidget(self.lbl_path)
        
        layout.addLayout(info_layout)

