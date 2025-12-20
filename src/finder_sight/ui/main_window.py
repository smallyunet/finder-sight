import sys
import os
import json
import subprocess
import io
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QListWidget, QProgressBar, QMessageBox, QStyle,
                             QFrame, QSizePolicy, QListWidgetItem, QMenu)
from PyQt6.QtCore import Qt, QBuffer, QIODevice, QSize
from PyQt6.QtGui import (QPixmap, QDragEnterEvent, QDropEvent, QImageReader, 
                         QKeySequence, QIcon, QAction)
from PIL import Image
import imagehash

from src.finder_sight.constants import (
    INDEX_FILE, CONFIG_FILE, THUMBNAIL_SIZE,
    DEFAULT_MAX_RESULTS, DEFAULT_SIMILARITY_THRESHOLD
)
from src.finder_sight.core.indexer import IndexerThread, IndexLoaderThread
from src.finder_sight.core.searcher import SearchThread
from src.finder_sight.ui.widgets import DropLabel, ClickableLabel
from src.finder_sight.ui.settings_dialog import SettingsDialog
from src.finder_sight.utils.logger import logger

class ImageFinderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("macOS Image Finder")
        self.setMinimumSize(800, 600)
        self.setAcceptDrops(True) 
        
        self.image_index = {}
        self.image_hashes = {} 
        self.directories = []
        self.indexer_thread = None
        self.search_thread = None
        self.index_loader_thread = None
        self.indexing_cancelled = False
        
        # Settings
        self.similarity_threshold = DEFAULT_SIMILARITY_THRESHOLD
        self.max_results = DEFAULT_MAX_RESULTS
        
        self.init_ui()
        self.create_menu_bar()
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
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.cancel_indexing)
        self.btn_cancel.setEnabled(False)
        
        self.btn_clear_index = QPushButton("Clear Index")
        self.btn_clear_index.clicked.connect(self.clear_index)
        
        top_btn_layout.addWidget(self.btn_add_dir)
        top_btn_layout.addWidget(self.btn_remove_dir)
        top_btn_layout.addWidget(self.btn_index)
        top_btn_layout.addWidget(self.btn_cancel)
        top_btn_layout.addWidget(self.btn_clear_index)
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
        self.drop_zone.setToolTip("You can also copy an image to clipboard and paste it here.")
        layout.addWidget(self.drop_zone)

        result_group = QFrame()
        result_group.setFrameShape(QFrame.Shape.StyledPanel)
        result_layout = QVBoxLayout(result_group)
        
        result_layout.addWidget(QLabel("Search Results (Double click to reveal):"))

        self.result_list = QListWidget()
        self.result_list.setIconSize(QSize(THUMBNAIL_SIZE, THUMBNAIL_SIZE))
        self.result_list.itemDoubleClicked.connect(self.on_result_double_clicked)
        self.result_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.result_list.customContextMenuRequested.connect(self.show_context_menu)
        
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
        self.btn_cancel.setEnabled(True)
        self.btn_clear_index.setEnabled(False)
        self.indexing_cancelled = False
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.indexer_thread = IndexerThread(self.directories, self.image_index)
        self.indexer_thread.progress_update.connect(self.update_progress)
        self.indexer_thread.finished.connect(self.indexing_finished)
        self.indexer_thread.deleted_files.connect(self.on_deleted_files_found)
        self.indexer_thread.start()

    def cancel_indexing(self):
        if self.indexer_thread and self.indexer_thread.isRunning():
            self.indexing_cancelled = True
            self.indexer_thread.stop()
            self.lbl_status.setText("Stopping indexer...")
            self.btn_cancel.setEnabled(False)

    def on_deleted_files_found(self, deleted_paths: list[str]) -> None:
        """Handle notification of deleted files from indexer."""
        for path in deleted_paths:
            if path in self.image_index:
                del self.image_index[path]
            if path in self.image_hashes:
                del self.image_hashes[path]
        logger.info(f"Removed {len(deleted_paths)} deleted files from index")

    def update_progress(self, current, total, current_file):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.lbl_status.setText(f"Indexing: {os.path.basename(current_file)}")

    def indexing_finished(self, index_data):
        # Update hash cache
        hash_load_failures = 0
        for path, hash_str in index_data.items():
            try:
                self.image_hashes[path] = imagehash.hex_to_multihash(hash_str)
            except Exception as e:
                hash_load_failures += 1
                logger.debug(f"Failed to parse hash for {path}: {e}")
        
        if hash_load_failures > 0:
            logger.warning(f"{hash_load_failures} hashes failed to load")
                
        self.image_index.update(index_data)
        self.save_index()
        self.save_index()
        self.btn_index.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_clear_index.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText(f"Indexing complete. Total images: {len(self.image_index)}")
        
        if self.indexing_cancelled:
            self.lbl_status.setText("Indexing cancelled.")
            logger.info("Indexing cancelled by user")
        else:
            QMessageBox.information(self, "Done", f"Indexed {len(index_data)} new images.")
            logger.info(f"Indexing finished: {len(index_data)} new images indexed")

    def save_index(self):
        try:
            with open(INDEX_FILE, 'w') as f:
                json.dump(self.image_index, f)
            logger.debug(f"Index saved with {len(self.image_index)} entries")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save index: {e}")
            logger.error(f"Failed to save index: {e}")

    def load_index(self):
        self.lbl_status.setText("Loading index...")
        self.btn_index.setEnabled(False)
        self.btn_add_dir.setEnabled(False)
        self.btn_remove_dir.setEnabled(False)
        
        self.index_loader_thread = IndexLoaderThread(INDEX_FILE)
        self.index_loader_thread.finished.connect(self.on_index_loaded)
        self.index_loader_thread.error.connect(self.on_index_load_error)
        self.index_loader_thread.start()

    def on_index_loaded(self, index_data, hash_data):
        self.image_index = index_data
        self.image_hashes = hash_data
        
        self.lbl_status.setText(f"Loaded index with {len(self.image_index)} images.")
        logger.info(f"Loaded index with {len(self.image_index)} images")
        
        self.btn_index.setEnabled(True)
        self.btn_add_dir.setEnabled(True)
        self.btn_remove_dir.setEnabled(True)
        self.index_loader_thread = None

    def on_index_load_error(self, error_msg):
        self.lbl_status.setText("Error loading index.")
        QMessageBox.warning(self, "Warning", f"Failed to load index: {error_msg}")
        logger.error(f"Failed to load index: {error_msg}")
        
        self.btn_index.setEnabled(True)
        self.btn_add_dir.setEnabled(True)
        self.btn_remove_dir.setEnabled(True)
        self.index_loader_thread = None

    def create_menu_bar(self):
        menu_bar = self.menuBar()
        
        # File Menu
        file_menu = menu_bar.addMenu("&File")
        
        add_dir_action = QAction("&Add Directory", self)
        add_dir_action.setShortcut("Ctrl+O")
        add_dir_action.triggered.connect(self.add_directory)
        file_menu.addAction(add_dir_action)
        
        start_index_action = QAction("Start &Indexing", self)
        start_index_action.setShortcut("Ctrl+I")
        start_index_action.triggered.connect(self.start_indexing)
        file_menu.addAction(start_index_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit Menu
        edit_menu = menu_bar.addMenu("&Edit")
        
        settings_action = QAction("&Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_settings)
        edit_menu.addAction(settings_action)
        
        # Help Menu
        help_menu = menu_bar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def show_about(self):
        QMessageBox.about(self, "About Finder Sight", 
                          "Finder Sight v0.0.4\n\n"
                          "Local Reverse Image Search for macOS.\n"
                          "Created by smallyu.")

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({
                    "directories": self.directories,
                    "similarity_threshold": self.similarity_threshold,
                    "max_results": self.max_results
                }, f)
            logger.debug("Config saved")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save config: {e}")
            logger.error(f"Failed to save config: {e}")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.directories = data.get("directories", [])
                    self.similarity_threshold = data.get(
                        "similarity_threshold", DEFAULT_SIMILARITY_THRESHOLD
                    )
                    self.max_results = data.get("max_results", DEFAULT_MAX_RESULTS)
                    for d in self.directories:
                        self.dir_list.addItem(d)
                logger.debug(f"Config loaded with {len(self.directories)} directories")
            except Exception as e:
                QMessageBox.warning(self, "Warning", f"Failed to load config: {e}")
                logger.error(f"Failed to load config: {e}")

    def show_settings(self):
        """Open the settings dialog."""
        current_settings = {
            'similarity_threshold': self.similarity_threshold,
            'max_results': self.max_results
        }
        dialog = SettingsDialog(self, current_settings)
        if dialog.exec():
            settings = dialog.get_settings()
            self.similarity_threshold = settings['similarity_threshold']
            self.max_results = settings['max_results']
            self.save_config()
            logger.info(f"Settings updated: threshold={self.similarity_threshold}, max_results={self.max_results}")

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
        
        # Start background search with current settings
        self.search_thread = SearchThread(
            self.image_hashes, 
            target_hash,
            max_results=self.max_results,
            similarity_threshold=self.similarity_threshold
        )
        self.search_thread.finished.connect(self.on_search_finished)
        self.search_thread.progress.connect(self.on_search_progress)
        self.search_thread.error.connect(lambda e: QMessageBox.critical(self, "Error", e))
        self.search_thread.start()

    def on_search_progress(self, current, total):
        """Update status with search progress."""
        self.lbl_status.setText(f"Searching... ({current}/{total})")

    def on_search_finished(self, results):
        self.drop_zone.set_searching(False)
        self.result_list.clear()

        if not results:
            self.lbl_status.setText(f"Search finished. No match. (Index: {len(self.image_index)} images)")
            return

        self.lbl_status.setText(f"Found {len(results)} matches. (Index: {len(self.image_index)} images)")
        
        for path, matches, dist in results:
            item = QListWidgetItem()
            item.setText(f"{os.path.basename(path)}\nScore: {dist:.2f} (Matches: {matches})")
            item.setData(Qt.ItemDataRole.UserRole, path)
            
            # Load thumbnail
            reader = QImageReader(path)
            reader.setScaledSize(QSize(THUMBNAIL_SIZE, THUMBNAIL_SIZE))
            img = reader.read()
            if not img.isNull():
                item.setIcon(QIcon(QPixmap.fromImage(img)))
            
            self.result_list.addItem(item)

    def on_result_double_clicked(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.reveal_in_finder(path)

    def show_context_menu(self, position):
        item = self.result_list.itemAt(position)
        if not item:
            return
            
        path = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu()
        
        reveal_action = QAction("Reveal in Finder", self)
        reveal_action.triggered.connect(lambda: self.reveal_in_finder(path))
        menu.addAction(reveal_action)
        
        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self.open_file(path))
        menu.addAction(open_action)
        
        copy_path_action = QAction("Copy Path", self)
        copy_path_action.triggered.connect(lambda: self.copy_to_clipboard(path))
        menu.addAction(copy_path_action)
        
        copy_image_action = QAction("Copy Image", self)
        copy_image_action.triggered.connect(lambda: self.copy_image_to_clipboard(path))
        menu.addAction(copy_image_action)
        
        menu.exec(self.result_list.viewport().mapToGlobal(position))

    def open_file(self, path):
        if sys.platform == 'darwin':
            subprocess.run(['open', path])
        elif os.name == 'nt':
            os.startfile(path)
        else:
            subprocess.run(['xdg-open', path])

    def copy_to_clipboard(self, text):
        QApplication.clipboard().setText(text)
        self.lbl_status.setText(f"Copied to clipboard: {os.path.basename(text)}")

    def copy_image_to_clipboard(self, path):
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            QApplication.clipboard().setPixmap(pixmap)
            self.lbl_status.setText(f"Copied image to clipboard: {os.path.basename(path)}")
        else:
            QMessageBox.warning(self, "Error", "Failed to load image for copying.")

    def clear_index(self):
        reply = QMessageBox.question(self, "Clear Index", 
                                   "Are you sure you want to clear the local index? "
                                   "This will not delete your image files.",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.image_index = {}
            self.image_hashes = {}
            self.save_index()
            self.lbl_status.setText("Index cleared.")
            self.result_list.clear()
            logger.info("Index cleared by user")

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
