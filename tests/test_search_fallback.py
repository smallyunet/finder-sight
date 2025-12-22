import sys
import os
import pytest
# Add parent directory to path to import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PyQt6.QtWidgets import QApplication
from src.finder_sight.core.searcher import SearchThread
from src.finder_sight.constants import DEFAULT_MAX_RESULTS, DEFAULT_SIMILARITY_THRESHOLD
from PIL import Image
import imagehash

@pytest.fixture
def sample_image_hash():
    """Create a sample image and return its hash."""
    img = Image.new('RGB', (100, 100), color='red')
    return imagehash.crop_resistant_hash(img)


@pytest.fixture
def app(qtbot):
    # Ensure a QApplication exists for PyQt signals
    return QApplication.instance() or QApplication([])

def test_search_thread_fallback_returns_results(qtbot, sample_image_hash, app):
    """When no results meet the similarity threshold, SearchThread should fallback to the nearest results."""
    # Create a hash that is deliberately different from the sample hash
    img = Image.new('RGB', (100, 100), color='green')
    different_hash = imagehash.phash(img)

    image_hashes = {"/path/to/different_image.jpg": different_hash}

    # Use a strict threshold that will exclude the different hash (e.g., 0)
    thread = SearchThread(image_hashes, sample_image_hash, max_results=3, similarity_threshold=0)
    results = []
    thread.finished.connect(lambda data: results.extend(data))

    with qtbot.waitSignal(thread.finished, timeout=5000):
        thread.start()

    # Since no match meets the threshold, fallback should return the nearest image(s)
    assert len(results) > 0
    assert results[0][0] == "/path/to/different_image.jpg"
