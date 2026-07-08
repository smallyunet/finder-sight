from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QSizePolicy, QStyle, QStyleOption, QPushButton, QGraphicsOpacityEffect, QMenu
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QPropertyAnimation, QEasingCurve, QTimer, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent, QPixmap, QPainter, QDesktopServices, QGuiApplication
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
    clicked = pyqtSignal()

    def __init__(self, title):
        super().__init__(title)
        self.default_title = title
        self.setAcceptDrops(True)
        self._preview_pixmap = None
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setProperty("state", "idle")
        self.setObjectName("DropZone") # Ensure object name is set for styling
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Animations
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)
        
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(1200)
        self.anim.setKeyValueAt(0.0, 1.0)
        self.anim.setKeyValueAt(0.5, 0.4)
        self.anim.setKeyValueAt(1.0, 1.0)
        self.anim.setLoopCount(-1) # Infinite loop
        
        self.search_timer = QTimer(self)
        self.search_timer.timeout.connect(self._update_search_text)
        self.search_dots = 0
        
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

    def _update_search_text(self):
        self.search_dots = (self.search_dots + 1) % 4
        dots = "." * self.search_dots
        self.setText(f"Searching{dots}")

    def on_close_clicked(self):
        self.clear_preview()
        self.cleared.emit()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.btn_close.geometry().contains(event.pos()) or self.btn_close.isHidden():
                self.clicked.emit()
        super().mousePressEvent(event)

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
            self.anim.start()
            self.style().unpolish(self)
            self.style().polish(self)

    def dragLeaveEvent(self, event):
        self.anim.stop()
        self.opacity_effect.setOpacity(1.0)
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
        self.anim.stop()
        self.opacity_effect.setOpacity(1.0)
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
            self.search_dots = 0
            self.setText("Searching")
            self.search_timer.start(400)
            self.setProperty("state", "searching")
            self.btn_close.show() # keep showing to allow cancel/clear
        else:
            self.search_timer.stop()
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

        # Add fade in animation
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)
        
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(400)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.anim.start()


class DuplicateImageWidget(QWidget):
    reveal_requested = pyqtSignal(str)

    def __init__(self, path: str, role_text: str):
        super().__init__()
        self.path = path
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(path)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        thumb = QLabel()
        thumb.setObjectName("ResultThumbnail")
        thumb.setFixedSize(86, 86)
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            thumb.setPixmap(
                pixmap.scaled(
                    QSize(80, 80),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        layout.addWidget(thumb, 0, Qt.AlignmentFlag.AlignCenter)

        name = QLabel(os.path.basename(path))
        name.setFixedWidth(92)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setObjectName("ResultName")
        if len(name.text()) > 13:
            name.setText(name.text()[:10] + "...")
        layout.addWidget(name)

        role = QLabel(role_text)
        role.setAlignment(Qt.AlignmentFlag.AlignCenter)
        role.setStyleSheet("font-size: 10px; color: #86868b;")
        layout.addWidget(role)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.reveal_requested.emit(self.path)
        super().mouseDoubleClickEvent(event)

    def show_context_menu(self, position):
        menu = QMenu()
        reveal_action = menu.addAction("Reveal in Finder")
        open_action = menu.addAction("Open Image")
        copy_path_action = menu.addAction("Copy Path")
        action = menu.exec(self.mapToGlobal(position))

        if action == reveal_action:
            self.reveal_requested.emit(self.path)
        elif action == open_action:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.path))
        elif action == copy_path_action:
            QGuiApplication.clipboard().setText(self.path)


class DuplicateGroupWidget(QWidget):
    reveal_requested = pyqtSignal(str)

    def __init__(self, group_number: int, paths: list[str]):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(8)

        title = QLabel(f"Group {group_number} · {len(paths)} images with the same visual hash")
        title.setStyleSheet("font-size: 13px; font-weight: 600; color: #1d1d1f;")
        layout.addWidget(title)

        folder_hint = QLabel(os.path.dirname(paths[0]) if paths else "")
        folder_hint.setStyleSheet("font-size: 11px; color: #86868b;")
        folder_hint.setWordWrap(True)
        layout.addWidget(folder_hint)

        thumbs_layout = QHBoxLayout()
        thumbs_layout.setContentsMargins(0, 0, 0, 0)
        thumbs_layout.setSpacing(10)

        for index, path in enumerate(paths[:8]):
            role_text = "reference" if index == 0 else "duplicate"
            item = DuplicateImageWidget(path, role_text)
            item.reveal_requested.connect(self.reveal_requested.emit)
            thumbs_layout.addWidget(item)

        if len(paths) > 8:
            more = QLabel(f"+{len(paths) - 8} more")
            more.setStyleSheet("font-size: 12px; color: #86868b;")
            thumbs_layout.addWidget(more)

        thumbs_layout.addStretch()
        layout.addLayout(thumbs_layout)
        self.setToolTip("\n".join(paths))
