import sys
import os
import json
import tempfile
import time
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtWidgets import QMessageBox

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.finder_sight.core.indexer import IndexLoaderThread, IndexerThread
from src.finder_sight.ui.main_window import ImageFinderApp
from src.finder_sight.constants import INDEX_FILE

def test_index_loader_thread(qtbot):
    """Test the IndexLoaderThread logic."""
    # Create a dummy index file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        index_data = {
            "version": "v3_mtime",
            "data": {
                "/path/to/img1.jpg": "0000000000000000",
                "/path/to/img2.jpg": "ffffffffffffffff"
            },
            "mtimes": {
                "/path/to/img1.jpg": 123456789,
                "/path/to/img2.jpg": 123456790
            }
        }
        json.dump(index_data, tmp)
        tmp_path = tmp.name
    
    try:
        thread = IndexLoaderThread(tmp_path)
        
        results = []
        def on_finished(idx, hashes, mtimes):
            results.append((idx, hashes, mtimes))
            
        thread.finished.connect(on_finished)
        
        with qtbot.waitSignal(thread.finished, timeout=2000):
            thread.start()
            
        assert len(results) == 1
        idx, hashes, mtimes = results[0]
        assert len(idx) == 2
        assert len(hashes) == 2
        assert len(mtimes) == 2
        assert "/path/to/img1.jpg" in idx
        
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

class MockSlowIndexerThread(IndexerThread):
    def run(self) -> None:
        self.is_running = True
        # Simulate long running task
        for i in range(50):
            if self.isInterruptionRequested():
                self.finished.emit({}, {})
                return
            time.sleep(0.05)
            self.progress_update.emit(i+1, 50, f"file_{i}.jpg")
        
        self.finished.emit({}, {})
    
    def stop(self) -> None:
        self.is_running = False
        self.requestInterruption()

def test_cancel_indexing(qtbot, monkeypatch):
    """Test that the cancel button stops the indexer."""
    # Mock mocks
    monkeypatch.setattr(ImageFinderApp, 'load_index', lambda self: None)
    monkeypatch.setattr(ImageFinderApp, 'save_config', lambda self: None)
    
    # Mock IndexerThread class in main_window module being used
    from src.finder_sight.ui import main_window
    monkeypatch.setattr(main_window, 'IndexerThread', MockSlowIndexerThread)

    app = ImageFinderApp()
    app.directories = ["/dummy/dir"]
    qtbot.addWidget(app)
    
    # Start indexing
    app.start_indexing()
    
    # Check running state
    # Wait for thread to actually start
    qtbot.waitUntil(lambda: app.indexer_thread is not None and app.indexer_thread.isRunning(), timeout=1000)
    assert app.indexer_thread.isRunning()
    assert not app.indexing_cancelled
    
    # Cancel indexing
    # We must ensure we wait for the finished signal which triggers UI update
    # In real app cancel_indexing just stops thread. The thread emits finished eventually if it wasn't force terminated?
    # Actually our cancel_indexing just calls stop() and sets flag.
    
    app.cancel_indexing()
    
    # Ensure thread stops 
    qtbot.waitUntil(lambda: not app.indexer_thread.isRunning(), timeout=5000)
    
    assert not app.indexer_thread.isRunning()
    assert app.indexing_cancelled
