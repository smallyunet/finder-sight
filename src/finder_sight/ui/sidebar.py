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


class SidebarActionButton(QPushButton):
    def __init__(self, icon_text, label, tooltip):
        super().__init__(f"{icon_text}  {label}")
        self.setToolTip(tooltip)
        self.setMinimumHeight(28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            "QPushButton { text-align: left; padding: 4px 8px; font-size: 12px; "
            "font-weight: 500; color: #1d1d1f; }"
        )


class Sidebar(QWidget):
    add_folder_clicked = pyqtSignal()
    remove_folder_clicked = pyqtSignal()
    refresh_clicked = pyqtSignal()
    duplicates_clicked = pyqtSignal()
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
        footer.setMinimumHeight(172)
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(12, 8, 12, 10)
        footer_layout.setSpacing(8)
        
        # 1. Status Row (Vertical for Progress Bar)
        status_row = QWidget()
        status_layout = QVBoxLayout(status_row)
        status_layout.setContentsMargins(0, 0, 0, 0)
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
        
        library_label = QLabel("LIBRARY")
        library_label.setStyleSheet("font-size: 10px; font-weight: 600; color: #86868b;")
        footer_layout.addWidget(library_label)

        library_actions = QHBoxLayout()
        library_actions.setContentsMargins(0, 0, 0, 0)
        library_actions.setSpacing(8)

        self.btn_add = SidebarActionButton("+", "Add", "Add Folder")
        self.btn_add.clicked.connect(self.add_folder_clicked)

        self.btn_remove = SidebarActionButton("-", "Remove", "Remove Selected Folder")
        self.btn_remove.clicked.connect(self.remove_folder_clicked)

        library_actions.addWidget(self.btn_add)
        library_actions.addWidget(self.btn_remove)
        footer_layout.addLayout(library_actions)

        index_label = QLabel("INDEX")
        index_label.setStyleSheet("font-size: 10px; font-weight: 600; color: #86868b;")
        footer_layout.addWidget(index_label)

        index_actions = QVBoxLayout()
        index_actions.setContentsMargins(0, 0, 0, 0)
        index_actions.setSpacing(6)

        self.btn_refresh = SidebarActionButton("↻", "Index Now", "Scan added folders for new images")
        self.btn_refresh.clicked.connect(self.refresh_clicked)

        self.btn_duplicates = SidebarActionButton("▣", "Find Duplicates", "Find duplicate images in indexed folders")
        self.btn_duplicates.clicked.connect(self.duplicates_clicked)

        self.btn_info = SidebarActionButton("i", "Index Info", "Show index information")
        self.btn_info.clicked.connect(self.info_clicked)

        self.btn_clear = SidebarActionButton("!", "Clear Index", "Clear the local image index")
        self.btn_clear.setStyleSheet(
            "QPushButton { text-align: left; padding: 4px 8px; font-size: 12px; "
            "font-weight: 500; color: #d70015; }"
        )
        self.btn_clear.clicked.connect(self.clear_clicked)

        index_actions.addWidget(self.btn_refresh)
        index_actions.addWidget(self.btn_duplicates)
        index_actions.addWidget(self.btn_info)
        index_actions.addWidget(self.btn_clear)
        footer_layout.addLayout(index_actions)
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
