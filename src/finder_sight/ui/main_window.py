import sys
import os
import json
import subprocess
import io
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QListWidget, QProgressBar, QMessageBox, QStyle,
                             QFrame, QSizePolicy, QListWidgetItem)
from PyQt6.QtCore import Qt, QBuffer, QIODevice, QSize
from PyQt6.QtGui import QPixmap, QDragEnterEvent, QDropEvent, QImageReader, QKeySequence, QIcon
from PIL import Image
import imagehash

from src.finder_sight.constants import INDEX_FILE, CONFIG_FILE
from src.finder_sight.core.indexer import IndexerThread
from src.finder_sight.core.searcher import SearchThread
from src.finder_sight.ui.widgets import DropLabel, ClickableLabel

class ImageFinderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("macOS Image Finder")
        self.resize(800, 600)
        self.setAcceptDrops(True) 
        
        self.image_index = {}
        self.image_hashes = {} 
        self.directories = []
        self.indexer_thread = None
        self.search_thread = None
        
        self.init_ui()
        self.load_config()
        self.load_index()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        index_group = QFrame()
        index_group.setFrameShape(QFrame.Shape.StyledPanel)
        index_layout = QVBoxLayout(index_group)
        
        top_btn_layout = QHBoxLayout()
        self.btn_add_dir = QPushButton("Add Directory")
        self.btn_add_dir.clicked.connect(self.add_directory)
        self.btn_add_dir.setShortcut("Ctrl+O")
        
        self.btn_remove_dir = QPushButton("Remove Directory")
        self.btn_remove_dir.clicked.connect(self.remove_directory)
        self.btn_remove_dir.setShortcut("Backspace")

        self.btn_index = QPushButton("Start Indexing")
        self.btn_index.clicked.connect(self.start_indexing)
        
        top_btn_layout.addWidget(self.btn_add_dir)
        top_btn_layout.addWidget(self.btn_remove_dir)
        top_btn_layout.addWidget(self.btn_index)
        top_btn_layout.addStretch()
        
        self.dir_list = QListWidget()
        self.dir_list.setFixedHeight(80)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.lbl_status = QLabel("Ready")
        
        index_layout.addLayout(top_btn_layout)
        index_layout.addWidget(self.dir_list)
        index_layout.addWidget(self.progress_bar)
        index_layout.addWidget(self.lbl_status)
        
        layout.addWidget(index_group)

        self.drop_zone = DropLabel("Drag & Drop Image Here\nor Paste (Cmd+V)")
        self.drop_zone.dropped.connect(lambda path: self.search_image(file_path=path))
        self.drop_zone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_zone.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.drop_zone)

        result_group = QFrame()
        result_group.setFrameShape(QFrame.Shape.StyledPanel)
        result_layout = QVBoxLayout(result_group)
        
        result_layout.addWidget(QLabel("Search Results (Double click to reveal):"))

        self.result_list = QListWidget()
        self.result_list.setIconSize(QSize(100, 100))
        self.result_list.itemDoubleClicked.connect(self.on_result_double_clicked)
        
        result_layout.addWidget(self.result_list)
        
        layout.addWidget(result_group)

    def add_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            if dir_path not in self.directories:
                self.directories.append(dir_path)
                self.dir_list.addItem(dir_path)
                self.save_config()

    def remove_directory(self):
        selected_items = self.dir_list.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            self.directories.remove(item.text())
            self.dir_list.takeItem(self.dir_list.row(item))
        self.save_config()

    def start_indexing(self):
        if not self.directories:
            QMessageBox.warning(self, "Warning", "Please add at least one directory.")
            return
            
        self.btn_index.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.indexer_thread = IndexerThread(self.directories, self.image_index)
        self.indexer_thread.progress_update.connect(self.update_progress)
        self.indexer_thread.finished.connect(self.indexing_finished)
        self.indexer_thread.start()

    def update_progress(self, current, total, current_file):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.lbl_status.setText(f"Indexing: {os.path.basename(current_file)}")

    def indexing_finished(self, index_data):
        # Update hash cache
        for path, hash_str in index_data.items():
            try:
                self.image_hashes[path] = imagehash.hex_to_multihash(hash_str)
            except:
                pass
                
        self.image_index.update(index_data)
        self.save_index()
        self.btn_index.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText(f"Indexing complete. Total images: {len(self.image_index)}")
        QMessageBox.information(self, "Done", f"Indexed {len(index_data)} new images.")

    def save_index(self):
        try:
            with open(INDEX_FILE, 'w') as f:
                json.dump(self.image_index, f)
        except Exception as e:
            print(f"Failed to save index: {e}")

    def load_index(self):
        if os.path.exists(INDEX_FILE):
            try:
                with open(INDEX_FILE, 'r') as f:
                    self.image_index = json.load(f)
                
                # Pre-calculate hashes for faster search
                self.image_hashes = {}
                for path, hash_str in self.image_index.items():
                    try:
                        self.image_hashes[path] = imagehash.hex_to_multihash(hash_str)
                    except:
                        continue
                        
                self.lbl_status.setText(f"Loaded index with {len(self.image_index)} images.")
            except Exception as e:
                print(f"Failed to load index: {e}")

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({"directories": self.directories}, f)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.directories = data.get("directories", [])
                    for d in self.directories:
                        self.dir_list.addItem(d)
            except Exception as e:
                print(f"Failed to load config: {e}")

    # --- Drag & Drop Implementation ---
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.search_image(file_path=file_path)

    # --- Paste (Cmd+V) Implementation ---
    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Paste):
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()
            
            if mime_data.hasImage():
                qimage = clipboard.image()
                self.search_image(image_data=qimage)
            elif mime_data.hasUrls():
                 # Handle copied file
                urls = mime_data.urls()
                if urls:
                    file_path = urls[0].toLocalFile()
                    self.search_image(file_path=file_path)
        else:
            super().keyPressEvent(event)

    # --- Search Logic ---
    def search_image(self, file_path=None, image_data=None):
        if not self.image_index:
            QMessageBox.warning(self, "Warning", "Index is empty. Please index some directories first.")
            return

        # Cancel previous search if running
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.requestInterruption()
            self.search_thread.wait()

        target_hash = None
        try:
            if file_path:
                self.lbl_status.setText(f"Processing: {os.path.basename(file_path)}...")
                with Image.open(file_path) as img:
                    target_hash = imagehash.crop_resistant_hash(img)
            elif image_data:
                self.lbl_status.setText("Processing pasted image...")
                # Convert QImage to PIL Image
                buffer = QBuffer()
                buffer.open(QIODevice.OpenModeFlag.ReadWrite)
                image_data.save(buffer, "PNG")
                pil_im = Image.open(io.BytesIO(buffer.data()))
                target_hash = imagehash.crop_resistant_hash(pil_im)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process input image: {e}")
            return

        if target_hash is None:
            return

        self.lbl_status.setText("Searching...")
        self.drop_zone.set_searching(True)
        
        # Start background search
        self.search_thread = SearchThread(self.image_hashes, target_hash)
        self.search_thread.finished.connect(self.on_search_finished)
        self.search_thread.error.connect(lambda e: QMessageBox.critical(self, "Error", e))
        self.search_thread.start()

    def on_search_finished(self, results):
        self.drop_zone.set_searching(False)
        self.result_list.clear()

        if not results:
            self.lbl_status.setText("Search finished. No match.")
            return

        self.lbl_status.setText(f"Found {len(results)} matches.")
        
        for path, matches, dist in results:
            item = QListWidgetItem()
            item.setText(f"{os.path.basename(path)}\nScore: {dist:.2f} (Matches: {matches})")
            item.setData(Qt.ItemDataRole.UserRole, path)
            
            # Load thumbnail
            reader = QImageReader(path)
            reader.setScaledSize(QSize(100, 100))
            img = reader.read()
            if not img.isNull():
                item.setIcon(QIcon(QPixmap.fromImage(img)))
            
            self.result_list.addItem(item)

    def on_result_double_clicked(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.reveal_in_finder(path)

    def reveal_in_finder(self, path):
        """
        Reveal file in Finder
        """
        if sys.platform == 'darwin':
            subprocess.run(['open', '-R', path])
        else:
            # Fallback for other OS
            if os.name == 'nt':
                subprocess.run(['explorer', '/select,', os.path.normpath(path)])
            else:
                subprocess.run(['xdg-open', os.path.dirname(path)])
