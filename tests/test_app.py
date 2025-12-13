import sys
import os
import pytest
from PyQt6.QtWidgets import QApplication
from PIL import Image
import imagehash
import tempfile
import shutil

# Add parent directory to path to import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.finder_sight.core.indexer import IndexerThread
from src.finder_sight.constants import SUPPORTED_EXTENSIONS

@pytest.fixture
def temp_image_dir():
    # Create a temporary directory with some dummy images
    temp_dir = tempfile.mkdtemp()
    
    # Create a dummy image
    img = Image.new('RGB', (100, 100), color = 'red')
    img.save(os.path.join(temp_dir, 'test_image.jpg'))
    
    # Create a dummy text file (should be ignored)
    with open(os.path.join(temp_dir, 'test.txt'), 'w') as f:
        f.write('hello')
        
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_hashing():
    # Test if imagehash works as expected
    img1 = Image.new('RGB', (100, 100), color = 'red')
    img2 = Image.new('RGB', (100, 100), color = 'red')
    
    # Create a distinct image for img3
    img3 = Image.new('RGB', (100, 100), color = 'blue')
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
    # Test the IndexerThread logic
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

def test_supported_extensions():
    assert '.jpg' in SUPPORTED_EXTENSIONS
    assert '.png' in SUPPORTED_EXTENSIONS
    assert '.txt' not in SUPPORTED_EXTENSIONS
