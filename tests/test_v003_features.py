import sys
import os
import json
import tempfile
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.finder_sight.ui.main_window import ImageFinderApp
from src.finder_sight.core.indexer import IndexerThread

class MockIndexerThread(IndexerThread):
    def run(self) -> None:
        self.is_running = True
        # Just finish immediately with empty data for testing state
        self.finished.emit({})

def test_clear_index(qtbot, monkeypatch):
    """Test clearing the index."""
    # Mock save_config and load_index to avoid file IO issues in test
    monkeypatch.setattr(ImageFinderApp, 'load_index', lambda self: None)
    monkeypatch.setattr(ImageFinderApp, 'save_config', lambda self: None)
    monkeypatch.setattr(ImageFinderApp, 'save_index', lambda self: None)
    
    # Mock QMessageBox.question to return Yes
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.StandardButton.Yes)

    app = ImageFinderApp()
    qtbot.addWidget(app)
    
    # Fill some dummy data
    app.image_index = {"path1": "hash1"}
    app.image_hashes = {"path1": "obj1"}
    app.result_list.addItem("Found image")
    
    app.clear_index()
    
    assert len(app.image_index) == 0
    assert len(app.image_hashes) == 0
    assert app.result_list.count() == 0

def test_ui_state_after_cancel(qtbot, monkeypatch):
    """Test that UI buttons are correctly enabled/disabled after cancel."""
    from src.finder_sight.ui import main_window
    from PyQt6.QtWidgets import QApplication
    
    # Mock IndexerThread to stay running until we stop it
    class SlowIndexer(IndexerThread):
        def run(self):
            self.is_running = True
            while self.is_running:
                self.msleep(10)
            self.finished.emit({})

    monkeypatch.setattr(main_window, 'IndexerThread', SlowIndexer)
    monkeypatch.setattr(ImageFinderApp, 'load_index', lambda self: None)
    monkeypatch.setattr(ImageFinderApp, 'save_config', lambda self: None)
    monkeypatch.setattr(ImageFinderApp, 'save_index', lambda self: None)

    app = ImageFinderApp()
    app.directories = ["/dummy"]
    qtbot.addWidget(app)
    
    # 1. Before indexing
    assert app.btn_index.isEnabled()
    assert not app.btn_cancel.isEnabled()
    assert app.btn_clear_index.isEnabled()
    
    # 2. Start indexing
    qtbot.mouseClick(app.btn_index, Qt.MouseButton.LeftButton)
    # Wait for thread to actually start
    qtbot.waitUntil(lambda: app.indexer_thread is not None and app.indexer_thread.isRunning(), timeout=1000)
    assert not app.btn_index.isEnabled()
    assert app.btn_cancel.isEnabled()
    assert not app.btn_clear_index.isEnabled()
    
    # 3. Cancel indexing - click and wait for thread to finish
    qtbot.mouseClick(app.btn_cancel, Qt.MouseButton.LeftButton)
    # Wait for the thread to stop running
    qtbot.waitUntil(lambda: not app.indexer_thread.isRunning(), timeout=2000)
    # Process pending events to ensure finished signal is handled
    QApplication.processEvents()
        
    # 4. After cancel
    assert app.btn_index.isEnabled()
    assert not app.btn_cancel.isEnabled()
    assert app.btn_clear_index.isEnabled()
    assert not app.progress_bar.isVisible()
