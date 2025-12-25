import sys
import os
import json
import subprocess
import io
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QSplitter, QFileDialog, QMessageBox, QMenu)
from PyQt6.QtCore import Qt, QBuffer, QIODevice, QSize
from PyQt6.QtGui import QAction, QKeySequence, QPixmap, QDesktopServices
from PyQt6.QtCore import QUrl, QThread, pyqtSignal

from PIL import Image
import imagehash

from src.finder_sight.constants import (
    INDEX_FILE, CONFIG_FILE, DEFAULT_MAX_RESULTS, 
    DEFAULT_SIMILARITY_THRESHOLD, INDEX_VERSION
)
from src.finder_sight.core.indexer import IndexerThread, IndexLoaderThread
from src.finder_sight.core.searcher import SearchThread
from src.finder_sight.ui.sidebar import Sidebar
from src.finder_sight.ui.search_area import SearchArea
from src.finder_sight.ui.settings_dialog import SettingsDialog
from src.finder_sight.utils.logger import logger
from src.finder_sight.utils.resource_helper import get_resource_path
from src.finder_sight.utils.updater_thread import UpdateCheckThread
from src.finder_sight import __version__ as APP_VERSION

class ImageFinderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("macOS Image Finder")
        self.resize(1000, 700) # Slightly larger default for sidebar layout
        
        self.image_index = {}
        self.image_hashes = {} 
        self.image_mtimes = {}  # Store modification times
        self.directories = []
        
        self.indexer_thread = None
        self.search_thread = None
        self.index_loader_thread = None
        self.indexing_cancelled = False
        
        # Settings
        self.similarity_threshold = DEFAULT_SIMILARITY_THRESHOLD
        self.max_results = DEFAULT_MAX_RESULTS
        
        self.init_ui()
        self.load_stylesheet()
        self.create_menu_bar()
        self.load_config()
        self.load_index() # Async load

    def load_stylesheet(self):
        try:
            # Use helper to find style.qss in both dev and frozen mode
            # We spec'd it to be at src/finder_sight/ui/style.qss in the bundle
            style_path = get_resource_path("src/finder_sight/ui/style.qss")
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            logger.warning(f"Failed to load stylesheet from {style_path}: {e}")

    def init_ui(self):
        # Master-Detail Layout using QSplitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self.splitter)
        
        # 1. Sidebar (Left)
        self.sidebar = Sidebar()
        self.splitter.addWidget(self.sidebar)
        
        # Connect Sidebar signals
        self.sidebar.add_folder_clicked.connect(self.add_directory)
        self.sidebar.remove_folder_clicked.connect(self.remove_directory)
        
        # 2. Search Area (Right)
        self.search_area = SearchArea()
        self.splitter.addWidget(self.search_area)
        
        # Connect SearchArea signals
        self.search_area.image_dropped.connect(self.search_image)
        self.search_area.image_pasted.connect(lambda img: self.search_image(image_data=img))
        self.search_area.result_double_clicked.connect(self.reveal_in_finder)
        
        # Set initial splitter sizes (Sidebar ~250px, Rest for Content)
        self.splitter.setSizes([250, 750])
        self.splitter.setCollapsible(0, False) # Can't fully hide sidebar
        
    def add_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            if dir_path not in self.directories:
                self.directories.append(dir_path)
                self.sidebar.add_folder(dir_path)
                self.save_config()
                # Auto-index on add
                self.start_indexing()

    def remove_directory(self):
        path = self.sidebar.get_selected_folder()
        if not path:
            return
        
        self.directories.remove(path)
        self.sidebar.remove_selected_folder()
        self.save_config()
        # Does not auto-reindex, but we should probably clear entries from that dir? 
        # For now, just leave it until next re-index or clear.

    def start_indexing(self):
        if not self.directories:
            QMessageBox.warning(self, "Warning", "Please add at least one directory.")
            return
            
        if self.indexer_thread and self.indexer_thread.isRunning():
            return # Already indexing
            
        self.indexing_cancelled = False
        self.sidebar.set_status("Indexing...", is_indexing=True)
        
        self.indexer_thread = IndexerThread(self.directories, self.image_index, self.image_mtimes)
        self.indexer_thread.progress_update.connect(self.update_indexing_progress)
        self.indexer_thread.finished.connect(self.indexing_finished)
        self.indexer_thread.deleted_files.connect(self.on_deleted_files_found)
        self.indexer_thread.start()

    def cancel_indexing(self):
        if self.indexer_thread and self.indexer_thread.isRunning():
            self.indexing_cancelled = True
            self.indexer_thread.stop()
            self.sidebar.set_status("Stopping...")
            
    def update_indexing_progress(self, current, total, current_file):
        # Update sidebar status with file name or percentage?
        # Sidebar space is small, maybe just "Indexing: filename"
        filename = os.path.basename(current_file)
        if len(filename) > 20:
             filename = filename[:17] + "..."
        self.sidebar.set_status(f"Indexing: {filename}", is_indexing=True)

    def on_deleted_files_found(self, deleted_paths):
        for path in deleted_paths:
            self.image_index.pop(path, None)
            self.image_hashes.pop(path, None)
            self.image_mtimes.pop(path, None)
        logger.info(f"Removed {len(deleted_paths)} deleted files")

    def indexing_finished(self, index_data, mtime_data):
        # Update hash cache
        for path, hash_str in index_data.items():
            try:
                self.image_hashes[path] = imagehash.hex_to_hash(hash_str)
            except Exception as e:
                logger.debug(f"Failed to parse hash for {path}: {e}")
                
        self.image_index.update(index_data)
        self.image_mtimes.update(mtime_data)
        self.save_index()
        
        status_msg = "Indexing cancelled." if self.indexing_cancelled else "Ready"
        self.sidebar.set_status(status_msg, is_indexing=False)
        
        if not self.indexing_cancelled:
            logger.info(f"Indexing finished: {len(index_data)} new images")

    def save_index(self):
        try:
            data = {
                "version": INDEX_VERSION,
                "data": self.image_index,
                "mtimes": self.image_mtimes
            }
            with open(INDEX_FILE, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Failed to save index: {e}")

    def load_index(self):
        self.sidebar.set_status("Loading index...")
        self.index_loader_thread = IndexLoaderThread(INDEX_FILE)
        self.index_loader_thread.finished.connect(self.on_index_loaded)
        self.index_loader_thread.error.connect(self.on_index_load_error)
        self.index_loader_thread.start()

    def on_index_loaded(self, index_data, hash_data, mtime_data):
        self.image_index = index_data
        self.image_hashes = hash_data
        self.image_mtimes = mtime_data
        self.sidebar.set_status(f"Loaded {len(self.image_index)} images", is_indexing=False)
        self.index_loader_thread = None

    def on_index_load_error(self, error_msg):
        self.sidebar.set_status("Index load error")
        QMessageBox.warning(self, "Warning", f"Failed to load index: {error_msg}")
        self.index_loader_thread = None

    # --- Search Logic ---
    def search_image(self, file_path=None, image_data=None):
        if not self.image_index:
            QMessageBox.warning(self, "Warning", "Index is empty.")
            return

        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.requestInterruption()
            self.search_thread.wait()

        target_hash = None
        try:
            if file_path:
                self.sidebar.set_status("Processing image...")
                with Image.open(file_path) as img:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    target_hash = imagehash.whash(img)
                    self.search_area.set_preview(path=file_path)
            elif image_data:
                self.sidebar.set_status("Processing paste...")
                buffer = QBuffer()
                buffer.open(QIODevice.OpenModeFlag.ReadWrite)
                image_data.save(buffer, "PNG")
                pil_im = Image.open(io.BytesIO(buffer.data()))
                if pil_im.mode != 'RGB':
                    pil_im = pil_im.convert('RGB')
                target_hash = imagehash.whash(pil_im)
                self.search_area.set_preview(image=image_data)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process input: {e}")
            self.sidebar.set_status("Error processing")
            return

        if target_hash is None:
            return

        self.search_area.set_searching_state(True)
        self.sidebar.set_status("Searching...")
        
        self.search_thread = SearchThread(
            self.image_hashes, 
            target_hash,
            max_results=self.max_results,
            similarity_threshold=self.similarity_threshold
        )
        self.search_thread.finished.connect(self.on_search_finished)
        self.search_thread.error.connect(lambda e: QMessageBox.critical(self, "Error", e))
        self.search_thread.start()

    def on_search_finished(self, results):
        self.search_area.set_searching_state(False)
        self.search_area.show_results(results)
        self.sidebar.set_status("Ready")

    # --- Utils ---
    def reveal_in_finder(self, path):
        if sys.platform == 'darwin':
            subprocess.run(['open', '-R', path])
        elif os.name == 'nt':
            subprocess.run(['explorer', '/select,', os.path.normpath(path)])
        else:
            subprocess.run(['xdg-open', os.path.dirname(path)])

    def clear_index(self):
        reply = QMessageBox.question(self, "Clear Index", 
                                   "Clear local index? This won't delete files.",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.image_index = {}
            self.image_hashes = {}
            self.save_index()
            self.search_area.clear()
            self.sidebar.set_status("Index cleared")

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({
                    "directories": self.directories,
                    "similarity_threshold": self.similarity_threshold,
                    "max_results": self.max_results
                }, f)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.directories = data.get("directories", [])
                    self.similarity_threshold = data.get("similarity_threshold", DEFAULT_SIMILARITY_THRESHOLD)
                    self.max_results = data.get("max_results", DEFAULT_MAX_RESULTS)
                    for d in self.directories:
                        self.sidebar.add_folder(d)
            except Exception as e:
                logger.error(f"Failed to load config: {e}")

    def create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        
        add_action = QAction("&Add Directory", self)
        add_action.setShortcut("Ctrl+O")
        add_action.triggered.connect(self.add_directory)
        file_menu.addAction(add_action)
        
        index_action = QAction("&Index Now", self)
        index_action.setShortcut("Ctrl+I")
        index_action.triggered.connect(self.start_indexing)
        file_menu.addAction(index_action)
        
        clear_action = QAction("Clear Index", self)
        clear_action.triggered.connect(self.clear_index)
        file_menu.addAction(clear_action)
        
        edit_menu = menu_bar.addMenu("&Edit")
        settings_action = QAction("&Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_settings)
        settings_action.triggered.connect(self.show_settings)
        edit_menu.addAction(settings_action)

        help_menu = menu_bar.addMenu("&Help")
        update_action = QAction("Check for Updates...", self)
        update_action.triggered.connect(self.check_updates)
        help_menu.addAction(update_action)

    def show_settings(self):
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

    def check_updates(self):
        self.sidebar.set_status("Checking for updates...")
        self.update_thread = UpdateCheckThread()
        self.update_thread.finished.connect(self.on_update_check_finished)
        self.update_thread.start()

    def on_update_check_finished(self, available, latest, url):
        self.sidebar.set_status("Ready")
        if available:
            reply = QMessageBox.question(
                self, 
                "Update Available", 
                f"A new version ({latest}) is available.\n\nCurrent version: {APP_VERSION}\n\nDo you want to download it now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                QDesktopServices.openUrl(QUrl(url))
        else:
             QMessageBox.information(self, "Up to Date", f"You are using the latest version ({APP_VERSION}).")
