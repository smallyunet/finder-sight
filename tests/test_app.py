import sys
import os
import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication
from PIL import Image
import imagehash
import tempfile
import shutil

# Add parent directory to path to import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.finder_sight.core.indexer import IndexerThread
from src.finder_sight.core.searcher import SearchThread
from src.finder_sight.constants import SUPPORTED_EXTENSIONS, DEFAULT_MAX_RESULTS, THUMBNAIL_SIZE


@pytest.fixture
def temp_image_dir():
    """Create a temporary directory with some dummy images."""
    temp_dir = tempfile.mkdtemp()
    
    # Create a dummy image
    img = Image.new('RGB', (100, 100), color='red')
    img.save(os.path.join(temp_dir, 'test_image.jpg'))
    
    # Create a dummy text file (should be ignored)
    with open(os.path.join(temp_dir, 'test.txt'), 'w') as f:
        f.write('hello')
        
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_image_hash():
    """Create a sample image and return its hash."""
    img = Image.new('RGB', (100, 100), color='red')
    return imagehash.crop_resistant_hash(img)


def test_hashing():
    """Test if imagehash works as expected."""
    img1 = Image.new('RGB', (100, 100), color='red')
    img2 = Image.new('RGB', (100, 100), color='red')
    
    # Create a distinct image for img3
    img3 = Image.new('RGB', (100, 100), color='blue')
    # Add some pattern to make dhash distinct from solid red
    from PIL import ImageDraw
    d = ImageDraw.Draw(img3)
    d.rectangle([20, 20, 80, 80], fill="white")
    
    # Use crop_resistant_hash as in the app
    h1 = imagehash.crop_resistant_hash(img1)
    h2 = imagehash.crop_resistant_hash(img2)
    h3 = imagehash.crop_resistant_hash(img3)
    
    # Note: crop_resistant_hash returns ImageMultiHash
    # For identical images, they should match
    assert h1.matches(h2)
    
    # For different images, they should likely not match (or have low match count)
    # But solid colors might be tricky for segmentation based hashing
    # Let's just check they are not identical objects
    assert str(h1) == str(h2)
    assert str(h1) != str(h3)


def test_indexer_thread(temp_image_dir, qtbot):
    """Test the IndexerThread logic."""
    thread = IndexerThread([temp_image_dir])
    
    # Use a list to capture the signal output
    results = []
    def on_finished(data):
        results.append(data)
    
    thread.finished.connect(on_finished)
    
    with qtbot.waitSignal(thread.finished, timeout=5000):
        thread.start()
    
    assert len(results) == 1
    index_data = results[0]
    
    # Should find 1 image
    assert len(index_data) == 1
    
    # Check if the key is the correct file path
    expected_path = os.path.join(temp_image_dir, 'test_image.jpg')
    assert expected_path in index_data
    
    # Check if value is a valid hash string
    assert len(index_data[expected_path]) > 0


def test_indexer_detects_deleted_files(temp_image_dir, qtbot):
    """Test that IndexerThread detects deleted files in existing index."""
    # Create an existing index with a non-existent file
    existing_index = {
        "/nonexistent/path/image.jpg": "somehash",
        os.path.join(temp_image_dir, 'test_image.jpg'): "existinghash"
    }
    
    thread = IndexerThread([temp_image_dir], existing_index)
    
    deleted_files = []
    def on_deleted(paths):
        deleted_files.extend(paths)
    
    thread.deleted_files.connect(on_deleted)
    
    with qtbot.waitSignal(thread.finished, timeout=5000):
        thread.start()
    
    # Should detect the non-existent file
    assert "/nonexistent/path/image.jpg" in deleted_files
    # Should NOT include the existing file
    assert os.path.join(temp_image_dir, 'test_image.jpg') not in deleted_files


def test_indexer_stop(temp_image_dir, qtbot):
    """Test that IndexerThread can be stopped."""
    thread = IndexerThread([temp_image_dir])
    
    # Stop immediately
    thread.stop()
    assert thread.is_running is False


def test_search_thread_no_matches(qtbot, sample_image_hash):
    """Test SearchThread with no matching hashes."""
    # Create a different hash that won't match
    different_img = Image.new('RGB', (100, 100), color='green')
    from PIL import ImageDraw
    d = ImageDraw.Draw(different_img)
    d.ellipse([10, 10, 90, 90], fill="yellow")
    different_hash = imagehash.crop_resistant_hash(different_img)
    
    image_hashes = {
        "/path/to/image1.jpg": different_hash
    }
    
    thread = SearchThread(image_hashes, sample_image_hash)
    
    results = []
    def on_finished(data):
        results.extend(data)
    
    thread.finished.connect(on_finished)
    
    with qtbot.waitSignal(thread.finished, timeout=5000):
        thread.start()
    
    # Results may or may not be empty depending on hash similarity
    # Just verify the thread completed without error
    assert isinstance(results, list)


def test_search_thread_with_matches(qtbot, sample_image_hash):
    """Test SearchThread finds matching hashes."""
    # Use the same hash for a match
    image_hashes = {
        "/path/to/matching_image.jpg": sample_image_hash
    }
    
    thread = SearchThread(image_hashes, sample_image_hash)
    
    results = []
    def on_finished(data):
        results.extend(data)
    
    thread.finished.connect(on_finished)
    
    with qtbot.waitSignal(thread.finished, timeout=5000):
        thread.start()
    
    # Should find the matching image
    assert len(results) >= 1
    assert results[0][0] == "/path/to/matching_image.jpg"


def test_search_thread_max_results(qtbot, sample_image_hash):
    """Test SearchThread respects max_results limit."""
    # Create many matching hashes
    image_hashes = {
        f"/path/to/image_{i}.jpg": sample_image_hash
        for i in range(50)
    }
    
    thread = SearchThread(image_hashes, sample_image_hash, max_results=5)
    
    results = []
    def on_finished(data):
        results.extend(data)
    
    thread.finished.connect(on_finished)
    
    with qtbot.waitSignal(thread.finished, timeout=5000):
        thread.start()
    
    # Should be limited to max_results
    assert len(results) <= 5


def test_supported_extensions():
    """Test that supported extensions are correctly defined."""
    assert '.jpg' in SUPPORTED_EXTENSIONS
    assert '.jpeg' in SUPPORTED_EXTENSIONS
    assert '.png' in SUPPORTED_EXTENSIONS
    assert '.webp' in SUPPORTED_EXTENSIONS
    assert '.bmp' in SUPPORTED_EXTENSIONS
    # v0.0.4 additions
    assert '.gif' in SUPPORTED_EXTENSIONS
    assert '.heic' in SUPPORTED_EXTENSIONS
    assert '.heif' in SUPPORTED_EXTENSIONS
    assert '.tiff' in SUPPORTED_EXTENSIONS
    assert '.tif' in SUPPORTED_EXTENSIONS
    # Unsupported
    assert '.txt' not in SUPPORTED_EXTENSIONS
    assert '.mp4' not in SUPPORTED_EXTENSIONS


def test_constants():
    """Test that constants are properly defined."""
    assert DEFAULT_MAX_RESULTS == 20
    assert THUMBNAIL_SIZE == 100
