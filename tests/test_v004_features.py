"""Tests for v0.0.4 features: settings persistence, similarity threshold, search progress."""
import sys
import os
import json
import tempfile
from unittest.mock import MagicMock, patch
from PIL import Image
import imagehash

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.finder_sight.core.searcher import SearchThread
from src.finder_sight.constants import (
    SUPPORTED_EXTENSIONS, 
    DEFAULT_SIMILARITY_THRESHOLD,
    DEFAULT_MAX_RESULTS
)


def test_new_supported_extensions():
    """Test that new extensions are added in v0.0.4."""
    assert '.gif' in SUPPORTED_EXTENSIONS
    assert '.heic' in SUPPORTED_EXTENSIONS
    assert '.heif' in SUPPORTED_EXTENSIONS
    assert '.tiff' in SUPPORTED_EXTENSIONS
    assert '.tif' in SUPPORTED_EXTENSIONS


def test_similarity_threshold_constant():
    """Test that default similarity threshold is defined."""
    assert DEFAULT_SIMILARITY_THRESHOLD == 8  # Max Hamming distance for phash


def test_search_thread_with_threshold(qtbot):
    """Test SearchThread filters results by similarity threshold."""
    # Create a sample hash
    img = Image.new('RGB', (100, 100), color='red')
    sample_hash = imagehash.phash(img)
    
    # Create image_hashes dict
    image_hashes = {
        "/path/to/image1.jpg": sample_hash,
        "/path/to/image2.jpg": sample_hash,
    }
    
    # Test with very high threshold - should filter out all results
    # since matches must be > threshold
    thread = SearchThread(
        image_hashes, 
        sample_hash, 
        max_results=10,
        similarity_threshold=-1  # Impossible to have negative distance
    )
    
    results = []
    def on_finished(data):
        results.extend(data)
    
    thread.finished.connect(on_finished)
    
    with qtbot.waitSignal(thread.finished, timeout=5000):
        thread.start()
    
    # Very low (negative) threshold should filter all results
    assert len(results) == 0


def test_search_thread_progress_signal(qtbot):
    """Test that SearchThread emits progress signals."""
    img = Image.new('RGB', (100, 100), color='red')
    sample_hash = imagehash.phash(img)
    
    # Create enough hashes to trigger progress
    image_hashes = {
        f"/path/to/image_{i}.jpg": sample_hash
        for i in range(150)
    }
    
    thread = SearchThread(image_hashes, sample_hash)
    
    progress_updates = []
    def on_progress(current, total):
        progress_updates.append((current, total))
    
    thread.progress.connect(on_progress)
    
    with qtbot.waitSignal(thread.finished, timeout=5000):
        thread.start()
    
    # Should have at least one progress update
    assert len(progress_updates) > 0
    # Last progress should show completion
    assert progress_updates[-1][0] == progress_updates[-1][1]


def test_settings_dialog_defaults():
    """Test SettingsDialog initializes with correct defaults."""
    from src.finder_sight.ui.settings_dialog import SettingsDialog
    
    dialog = SettingsDialog()
    settings = dialog.get_settings()
    
    assert settings['similarity_threshold'] == DEFAULT_SIMILARITY_THRESHOLD
    assert settings['max_results'] == DEFAULT_MAX_RESULTS


def test_settings_dialog_custom_values():
    """Test SettingsDialog respects current settings."""
    from src.finder_sight.ui.settings_dialog import SettingsDialog
    
    custom = {
        'similarity_threshold': 42,
        'max_results': 50
    }
    dialog = SettingsDialog(current_settings=custom)
    settings = dialog.get_settings()
    
    assert settings['similarity_threshold'] == 42
    assert settings['max_results'] == 50
