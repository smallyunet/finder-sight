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
            "/path/to/img1.jpg": "0000000000000000",
            "/path/to/img2.jpg": "ffffffffffffffff"
        }
        json.dump(index_data, tmp)
        tmp_path = tmp.name
    
    try:
        thread = IndexLoaderThread(tmp_path)
        
        results = []
        def on_finished(idx, hashes):
            results.append((idx, hashes))
            
        thread.finished.connect(on_finished)
        
        with qtbot.waitSignal(thread.finished, timeout=2000):
            thread.start()
            
        assert len(results) == 1
        idx, hashes = results[0]
        assert len(idx) == 2
        assert len(hashes) == 2
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
                self.finished.emit({})
                return
            time.sleep(0.05)
            self.progress_update.emit(i+1, 50, f"file_{i}.jpg")
        
        self.finished.emit({})
    
    def stop(self) -> None:
        self.is_running = False
        self.requestInterruption()

def test_cancel_indexing(qtbot, monkeypatch):
    """Test that the cancel button stops the indexer."""
    # Mock mocks
    monkeypatch.setattr(ImageFinderApp, 'load_index', lambda self: None)
    monkeypatch.setattr(ImageFinderApp, 'save_config', lambda self: None)
    
    # Mock IndexerThread class in main_window module being used
    # But main_window imports IndexerThread. We need to patch it where it is imported.
    # actually, we can just patch self.indexer_thread assignment in start_indexing? 
    # Or better, patch the class in the module.
    
    from src.finder_sight.ui import main_window
    monkeypatch.setattr(main_window, 'IndexerThread', MockSlowIndexerThread)

    app = ImageFinderApp()
    app.directories = ["/dummy/dir"]
    qtbot.addWidget(app)
    
    # Start indexing
    qtbot.mouseClick(app.btn_index, Qt.MouseButton.LeftButton)
    
    # Check running state
    assert app.indexer_thread.isRunning()
    assert app.btn_cancel.isEnabled()
    assert not app.btn_index.isEnabled()
    
    # Click cancel
    # We must ensure we wait for the finished signal which triggers UI update
    with qtbot.waitSignal(app.indexer_thread.finished, timeout=5000):
        qtbot.mouseClick(app.btn_cancel, Qt.MouseButton.LeftButton)
        # Ensure thread stops (it should by itself due to signal wait logic mostly, but good to be sure)
        app.indexer_thread.wait(5000)
    
    assert not app.indexer_thread.isRunning()
    
    # Verify UI reset
    assert app.btn_index.isEnabled()
    assert not app.btn_cancel.isEnabled()
    # Actually logic in `cancel_indexing`:
    # self.indexer_thread.stop()
    # self.btn_cancel.setEnabled(False)
    # But `indexing_finished` is only called if thread finishes naturally or emits finished?
    # IndexerThread logic: if !is_running return.
    # It does NOT emit finished if cancelled.
    # So `indexing_finished` is NOT called.
    # So UI needs to handle reset manually in `cancel_indexing` or listen to `finished` signal which won't fire.
    # Wait, `cancel_indexing` just stops thread.
    # Does it re-enable Start button?
    # Current implementation of `cancel_indexing`:
    # self.indexer_thread.stop()
    # self.lbl_status.setText("Stopping indexer...")
    # self.btn_cancel.setEnabled(False)
    
    # It does NOT re-enable `btn_index`. This is a bug revealed by writing the test!
    # I should fix the code.
