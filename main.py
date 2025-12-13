import sys
import os
import json
import subprocess
import typing
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QListWidget, QProgressBar, QMessageBox, QStyle,
                             QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QBuffer, QIODevice, QSize
from PyQt6.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent, QAction, QKeySequence, QIcon, QImageReader
from PIL import Image
import imagehash
import io

# Constants
INDEX_FILE = "image_index.json"
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
HASH_THRESHOLD = 5

class IndexerThread(QThread):
    """
    Background thread: Used to traverse directories and calculate image hashes
    """
    progress_update = pyqtSignal(int, int, str) # current, total, current_file
    finished = pyqtSignal(dict)

    def __init__(self, directories, existing_index=None):
        super().__init__()
        self.directories = directories
        self.existing_index = existing_index or {}
        self.is_running = True

    def run(self):
        image_files = []
        # 1. Scan all files
        for directory in self.directories:
            for root, _, files in os.walk(directory):
                for file in files:
                    if not self.is_running:
                        return
                    if os.path.splitext(file)[1].lower() in SUPPORTED_EXTENSIONS:
                        full_path = os.path.join(root, file)
                        # Skip if already indexed
                        if full_path not in self.existing_index:
                            image_files.append(full_path)
        
        total_files = len(image_files)
        index_data = {}
        
        # 2. Calculate hashes
        for i, file_path in enumerate(image_files):
            if not self.is_running:
                return
            
            try:
                # Use crop_resistant_hash for partial image matching
                with Image.open(file_path) as img:
                    h = imagehash.crop_resistant_hash(img)
                    index_data[file_path] = str(h)
            except Exception as e:
                print(f"Error indexing {file_path}: {e}")
            
            # Throttle updates to avoid UI freeze
            if i % 10 == 0 or i == total_files - 1:
                self.progress_update.emit(i + 1, total_files, file_path)
            
        self.finished.emit(index_data)

    def stop(self):
        self.is_running = False

class DropLabel(QLabel):
    dropped = pyqtSignal(str)

    def __init__(self, title):
        super().__init__(title)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.dropped.emit(file_path)

class ImageFinderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("macOS Image Finder")
        self.resize(800, 600)
        self.setAcceptDrops(True) 
        
        self.image_index = {}
        self.image_hashes = {} # Cache for ImageHash objects
        self.directories = []
        self.indexer_thread = None
        
        self.init_ui()
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
        self.btn_index = QPushButton("Start Indexing")
        self.btn_index.clicked.connect(self.start_indexing)
        top_btn_layout.addWidget(self.btn_add_dir)
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
        self.drop_zone.setStyleSheet("""
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
        """)
        self.drop_zone.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.drop_zone)

        result_group = QFrame()
        result_group.setFrameShape(QFrame.Shape.StyledPanel)
        result_layout = QHBoxLayout(result_group)
        
        self.lbl_result_thumb = QLabel()
        self.lbl_result_thumb.setFixedSize(100, 100)
        self.lbl_result_thumb.setStyleSheet("border: 1px solid #ccc; background: #eee;")
        self.lbl_result_thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        result_info_layout = QVBoxLayout()
        self.lbl_result_text = QLabel("No result")
        self.lbl_result_text.setWordWrap(True)
        self.btn_reveal = QPushButton("Reveal in Finder")
        self.btn_reveal.setEnabled(False)
        self.btn_reveal.clicked.connect(self.reveal_current_result)
        
        result_info_layout.addWidget(self.lbl_result_text)
        result_info_layout.addWidget(self.btn_reveal)
        result_info_layout.addStretch()
        
        result_layout.addWidget(self.lbl_result_thumb)
        result_layout.addLayout(result_info_layout)
        
        layout.addWidget(result_group)
        
        self.current_result_path = None

    def add_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            if dir_path not in self.directories:
                self.directories.append(dir_path)
                self.dir_list.addItem(dir_path)

    def start_indexing(self):
        if not self.directories:
            QMessageBox.warning(self, "Warning", "Please add, self.image_index at least one directory.")
            return
            
        self.btn_index.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.indexer_thread = IndexerThread(self.directories)
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

        target_hash = None
        try:
            if file_path:
                self.lbl_status.setText(f"Searching for: {os.path.basename(file_path)}...")
                with Image.open(file_path) as img:
                    target_hash = imagehash.crop_resistant_hash(img)
            elif image_data:
                self.lbl_status.setText("Searching for pasted image...")
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

        # Find best match
        best_match_path = None
        max_matches = 0
        min_dist = float('inf')

        # Iterate through pre-calculated hashes
        for path, h in self.image_hashes.items():
            try:
                # hash_diff returns (matches, distance)
                # matches: number of segments in query that matched segments in db image
                matches, dist = h.hash_diff(target_hash)
                
                # We prioritize number of matches, then lower distance
                if matches > max_matches:
                    max_matches = matches
                    min_dist = dist
                    best_match_path = path
                elif matches == max_matches and matches > 0:
                    if dist < min_dist:
                        min_dist = dist
                        best_match_path = path
            except:
                continue

        if best_match_path and max_matches > 0:
            self.show_result(best_match_path, f"Matches: {max_matches}, Dist: {min_dist}")
        else:
            self.show_no_result()

    def show_result(self, path, dist):
        self.current_result_path = path
        self.lbl_result_text.setText(f"Found: {os.path.basename(path)}\nPath: {path}\nDistance: {dist}")
        self.btn_reveal.setEnabled(True)
        
        # Show thumbnail efficiently using QImageReader
        reader = QImageReader(path)
        # Scale to slightly larger than target size to maintain quality, then let QLabel handle final scaling or scale here
        reader.setScaledSize(QSize(100, 100)) 
        img = reader.read()
        
        if not img.isNull():
            self.lbl_result_thumb.setPixmap(QPixmap.fromImage(img))
        else:
            self.lbl_result_thumb.setText("No Preview")
            
        self.lbl_status.setText("Match found!")

    def show_no_result(self):
        self.current_result_path = None
        self.lbl_result_text.setText("No matching image found.")
        self.btn_reveal.setEnabled(False)
        self.lbl_result_thumb.clear()
        self.lbl_status.setText("Search finished.")

    def reveal_current_result(self):
        if self.current_result_path:
            self.reveal_in_finder(self.current_result_path)

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageFinderApp()
    window.show()
    sys.exit(app.exec())
