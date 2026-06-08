from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
                             QPushButton, QHBoxLayout, QLabel, QFrame, QStyle, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon

import os
import sys
import subprocess

class FolderItemWidget(QWidget):
    def __init__(self, path):
        super().__init__()
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(8)
        
        # Folder Icon
        self.icon_lbl = QLabel()
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        self.icon_lbl.setPixmap(icon.pixmap(20, 20))
        main_layout.addWidget(self.icon_lbl)
        
        # Text layout
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        
        # Primary: Folder Name
        self.lbl_name = QLabel(os.path.basename(path) or path)
        self.lbl_name.setStyleSheet("font-weight: 500; font-size: 13px; color: #1d1d1f;")
        text_layout.addWidget(self.lbl_name)
        
        # Secondary: Full Path
        self.lbl_path = QLabel(path)
        self.lbl_path.setStyleSheet("font-size: 11px; color: #86868b;")
        self.lbl_path.setWordWrap(False)
        text_layout.addWidget(self.lbl_path)
        
        main_layout.addLayout(text_layout, 1)

class Sidebar(QWidget):
    add_folder_clicked = pyqtSignal()
    remove_folder_clicked = pyqtSignal()
    refresh_clicked = pyqtSignal()
    clear_clicked = pyqtSignal()
    info_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setFixedWidth(250)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header (Visual effect background usually handles this, just a spacer or title if needed)
        header = QWidget()
        header.setFixedHeight(40)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)
        lbl_title = QLabel("LIBRARY")
        lbl_title.setStyleSheet("font-size: 11px; font-weight: 600; color: #86868b;")
        header_layout.addWidget(lbl_title)
        layout.addWidget(header)
        
        # Folder List
        self.folder_list = QListWidget()
        self.folder_list.setFrameShape(QFrame.Shape.NoFrame)
        self.folder_list.setStyleSheet("background: transparent;")
        self.folder_list.setFocusPolicy(Qt.FocusPolicy.NoFocus) # Remove focus outline
        self.folder_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.folder_list.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.folder_list, 1)
        
        # Footer (Status + Actions)
        footer = QWidget()
        footer.setObjectName("SidebarFooter")
        footer.setMinimumHeight(80)  # Ensure footer is always visible
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(0, 8, 0, 8)
        footer_layout.setSpacing(6)
        
        # 1. Status Row (Vertical for Progress Bar)
        status_row = QWidget()
        status_layout = QVBoxLayout(status_row)
        status_layout.setContentsMargins(16, 0, 16, 0)
        status_layout.setSpacing(4)
        
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setStyleSheet("font-size: 11px; color: #86868b;")
        status_layout.addWidget(self.lbl_status)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #e5e5e5;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #007AFF;
                border-radius: 2px;
            }
        """)
        self.progress_bar.hide()
        status_layout.addWidget(self.progress_bar)
        
        footer_layout.addWidget(status_row)
        
        # 2. Actions Row
        actions_bar = QWidget()
        actions_bar.setFixedHeight(32)
        actions_layout = QHBoxLayout(actions_bar)
        actions_layout.setContentsMargins(12, 0, 12, 0)
        actions_layout.setSpacing(8)
        
        self.btn_add = QPushButton("+")
        self.btn_add.setToolTip("Add Folder")
        self.btn_add.setFixedSize(24, 24)
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add.setStyleSheet("QPushButton { color: #1d1d1f; font-weight: bold; padding: 0px; font-size: 16px; }")
        self.btn_add.clicked.connect(self.add_folder_clicked)
        
        self.btn_remove = QPushButton("−")
        self.btn_remove.setToolTip("Remove Folder")
        self.btn_remove.setFixedSize(24, 24)
        self.btn_remove.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_remove.setStyleSheet("QPushButton { color: #1d1d1f; font-weight: bold; padding: 0px; font-size: 16px; }")
        self.btn_remove.clicked.connect(self.remove_folder_clicked)
        
        # Spacer
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #c0c0c0;")
        
        self.btn_refresh = QPushButton("⟳")
        self.btn_refresh.setToolTip("Index Now")
        self.btn_refresh.setFixedSize(24, 24)
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.setStyleSheet("QPushButton { color: #1d1d1f; padding: 0px; font-size: 16px; min-height: 20px }")
        self.btn_refresh.clicked.connect(self.refresh_clicked)
        
        self.btn_clear = QPushButton("⌫")
        self.btn_clear.setToolTip("Clear Index")
        self.btn_clear.setFixedSize(24, 24)
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setStyleSheet("QPushButton { color: #d70015; padding: 0px; font-size: 16px; min-height: 20px }")
        self.btn_clear.clicked.connect(self.clear_clicked)
        
        self.btn_info = QPushButton("ⓘ")
        self.btn_info.setToolTip("Index Information")
        self.btn_info.setFixedSize(24, 24)
        self.btn_info.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_info.setStyleSheet("QPushButton { color: #007AFF; padding: 0px; font-size: 16px; min-height: 20px }")
        self.btn_info.clicked.connect(self.info_clicked)
        
        actions_layout.addWidget(self.btn_add)
        actions_layout.addWidget(self.btn_remove)
        actions_layout.addWidget(line)
        actions_layout.addWidget(self.btn_refresh)
        actions_layout.addWidget(self.btn_clear)
        actions_layout.addWidget(self.btn_info)
        actions_layout.addStretch()
        
        footer_layout.addWidget(actions_bar)
        layout.addWidget(footer, 0)
        
    def add_folder(self, path):
        item = QListWidgetItem(self.folder_list)
        item.setData(Qt.ItemDataRole.UserRole, path)
        item.setSizeHint(QSize(0, 50)) # Fixed height for consistency
        
        widget = FolderItemWidget(path)
        self.folder_list.setItemWidget(item, widget)
        
    def get_selected_folder(self):
        items = self.folder_list.selectedItems()
        if items:
            return items[0].data(Qt.ItemDataRole.UserRole)
        return None

    def remove_selected_folder(self):
        for item in self.folder_list.selectedItems():
            self.folder_list.takeItem(self.folder_list.row(item))
            
    def show_context_menu(self, position):
        item = self.folder_list.itemAt(position)
        if not item:
            return
            
        path = item.data(Qt.ItemDataRole.UserRole)
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        
        menu = QMenu()
        reveal_action = menu.addAction("Reveal in Finder")
        remove_action = menu.addAction("Remove Folder")
        
        action = menu.exec(self.folder_list.viewport().mapToGlobal(position))
        
        if action == reveal_action:
            if sys.platform == 'darwin':
                subprocess.run(['open', '-R', path])
            elif os.name == 'nt':
                subprocess.run(['explorer', '/select,', os.path.normpath(path)])
            else:
                subprocess.run(['xdg-open', os.path.dirname(path)])
        elif action == remove_action:
            item.setSelected(True)
            self.remove_folder_clicked.emit()
            
    def set_status(self, text, is_indexing=False):
        self.lbl_status.setText(text)
        self.lbl_status.setToolTip(text) # Show full text on hover
        if is_indexing:
             self.lbl_status.setStyleSheet("font-size: 11px; color: #007AFF;")
        else:
             self.lbl_status.setStyleSheet("font-size: 11px; color: #86868b;")
             self.progress_bar.hide()

    def update_progress(self, current, total, filename):
        self.progress_bar.show()
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.set_status(f"Indexing {current}/{total}", is_indexing=True)
        self.lbl_status.setToolTip(filename)

    def clear(self):
        self.folder_list.clear()
