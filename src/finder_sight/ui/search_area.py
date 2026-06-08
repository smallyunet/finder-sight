from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
                             QLabel, QPushButton, QHBoxLayout, QFrame, QSizePolicy, QStackedWidget)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QPixmap, QImageReader
import os
from src.finder_sight.ui.widgets import DropLabel, ResultWidget
from src.finder_sight.constants import THUMBNAIL_SIZE, MAX_HASH_DIST

class EmptyStateWidget(QWidget):
    def __init__(self, icon_text, message_text, sub_text=""):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)
        
        self.icon_lbl = QLabel(icon_text)
        self.icon_lbl.setStyleSheet("font-size: 64px; color: #d1d1d6;")
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.msg_lbl = QLabel(message_text)
        self.msg_lbl.setStyleSheet("font-size: 16px; font-weight: 500; color: #1d1d1f;")
        self.msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.icon_lbl)
        layout.addWidget(self.msg_lbl)
        
        if sub_text:
            self.sub_lbl = QLabel(sub_text)
            self.sub_lbl.setStyleSheet("font-size: 13px; color: #86868b;")
            self.sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.sub_lbl)

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
        
        self.drop_zone = DropLabel("Drag Image Here, Paste (Cmd+V),\nor Click to Browse")
        self.drop_zone.setObjectName("DropZone")
        self.drop_zone.setFixedHeight(200)
        self.drop_zone.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.drop_zone.dropped.connect(self.image_dropped.emit)
        self.drop_zone.cleared.connect(self.clear)
        self.drop_zone.clicked.connect(self.select_file)
        
        layout.addWidget(self.drop_zone)
        
        # --- Results Section ---
        
        # Header / Status
        self.header_layout = QHBoxLayout()
        self.lbl_results_title = QLabel("Matches")
        self.lbl_results_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #1d1d1f;")
        self.header_layout.addWidget(self.lbl_results_title)
        
        self.header_layout.addStretch()
        
        layout.addLayout(self.header_layout)
        
        # Grid and Empty State via Stack
        self.stack = QStackedWidget()
        
        self.empty_state = EmptyStateWidget("🔍", "No Matches Found", "Try adjusting the similarity threshold\nor adding more folders to your library.")
        
        self.result_list = QListWidget()
        self.result_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.result_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.result_list.setSpacing(12)
        self.result_list.setMovement(QListWidget.Movement.Static)
        self.result_list.setIconSize(QSize(120, 140)) # Space for widget
        self.result_list.setFrameShape(QFrame.Shape.NoFrame)
        self.result_list.setStyleSheet("background: transparent;")
        self.result_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.result_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.result_list.customContextMenuRequested.connect(self.show_context_menu)
        
        self.stack.addWidget(self.result_list)
        self.stack.addWidget(self.empty_state)
        
        layout.addWidget(self.stack)
        
    def set_preview(self, path=None, image=None):
        if path:
            self.drop_zone.set_preview_image(file_path=path)
        elif image:
            self.drop_zone.set_preview_image(pixmap=QPixmap.fromImage(image))
            
    def set_searching_state(self, is_searching):
        self.drop_zone.set_searching(is_searching)
        if hasattr(self, 'populate_timer') and self.populate_timer.isActive():
            self.populate_timer.stop()
        if is_searching:
            self.lbl_results_title.setText("Searching...")
            self.result_list.clear()
            self.stack.setCurrentWidget(self.result_list)

    def show_results(self, results):
        """
        results: list of (path, distance) tuples
        """
        self.result_list.clear()
        
        if hasattr(self, 'populate_timer') and self.populate_timer.isActive():
            self.populate_timer.stop()
        
        if not results:
            self.lbl_results_title.setText("No Matches Found")
            self.stack.setCurrentWidget(self.empty_state)
            return
            
        self.stack.setCurrentWidget(self.result_list)
        self.lbl_results_title.setText(f"Found {len(results)} Matches")
        
        self.pending_results = list(results)
        self.populate_timer = QTimer(self)
        self.populate_timer.timeout.connect(self._add_next_result)
        self.populate_timer.start(50) # 50ms stagger
        
    def _add_next_result(self):
        if not self.pending_results:
            self.populate_timer.stop()
            return
            
        path, dist = self.pending_results.pop(0)
        
        # Create Item
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, path)
        
        # Load Thumbnail 
        pixmap = QPixmap()
        reader = QImageReader(path)
        if reader.canRead():
            size = reader.size()
            if size.isValid():
                max_dim = 150
                ratio = min(max_dim / size.width(), max_dim / size.height())
                new_width = int(size.width() * ratio)
                new_height = int(size.height() * ratio)
                reader.setScaledSize(QSize(new_width, new_height))
            else:
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

    def select_file(self):
        from PyQt6.QtWidgets import QFileDialog
        from src.finder_sight.constants import SUPPORTED_EXTENSIONS
        
        filter_str = "Images (" + " ".join([f"*{ext}" for ext in SUPPORTED_EXTENSIONS]) + ")"
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Search Image",
            "",
            filter_str
        )
        if file_path:
            self.image_dropped.emit(file_path)

    def show_context_menu(self, position):
        item = self.result_list.itemAt(position)
        if not item:
            return
            
        path = item.data(Qt.ItemDataRole.UserRole)
        if not path or not os.path.exists(path):
            return
            
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction, QGuiApplication, QPixmap
        
        menu = QMenu()
        reveal_action = menu.addAction("Reveal in Finder")
        open_action = menu.addAction("Open Image")
        copy_path_action = menu.addAction("Copy Path")
        copy_image_action = menu.addAction("Copy Image")
        
        action = menu.exec(self.result_list.viewport().mapToGlobal(position))
        
        if action == reveal_action:
            self.result_double_clicked.emit(path)
        elif action == open_action:
            from PyQt6.QtGui import QDesktopServices
            from PyQt6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        elif action == copy_path_action:
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(path)
        elif action == copy_image_action:
            clipboard = QGuiApplication.clipboard()
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                clipboard.setImage(pixmap.toImage())

    def clear(self):
        self.drop_zone.clear_preview()
        if hasattr(self, 'populate_timer') and self.populate_timer.isActive():
            self.populate_timer.stop()
        self.result_list.clear()
        self.lbl_results_title.setText("Matches")
        self.stack.setCurrentWidget(self.result_list)
