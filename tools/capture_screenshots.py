import pytest
import os
import sys
from PyQt6.QtGui import QImage, QColor, QPixmap
from PyQt6.QtCore import Qt

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.finder_sight.ui.main_window import ImageFinderApp
from src.finder_sight.ui.search_area import ResultWidget

def create_dummy_image(path, color_hex):
    img = QImage(400, 300, QImage.Format.Format_RGB32)
    img.fill(QColor(color_hex))
    img.save(path)

def test_capture_main_window(qtbot, tmp_path, monkeypatch):
    """
    Launches the app, populates it with mock data, and takes a screenshot.
    """
    # Mock config to prevent side effects
    monkeypatch.setattr(ImageFinderApp, 'load_config', lambda self: None)
    monkeypatch.setattr(ImageFinderApp, 'save_config', lambda self: None)
    monkeypatch.setattr(ImageFinderApp, 'load_index', lambda self: None)
    
    app = ImageFinderApp()
    qtbot.addWidget(app)
    app.resize(1100, 750)
    app.show()
    
    # 1. Populate Sidebar
    # Using logical paths that look good
    fake_dirs = [
        "/Users/username/Pictures/Photography",
        "/Users/username/Work/DesignAssets",
        "/Users/username/Downloads/Wallpapers"
    ]
    for d in fake_dirs:
        app.sidebar.add_folder(d)
        
    app.sidebar.set_status("Ready")

    # 2. Populate Search Results
    # Create temp images so the real loading logic works
    img1 = tmp_path / "sunset_v1.jpg"
    img2 = tmp_path / "sunset_backup.png"
    img3 = tmp_path / "sunset_edit.jpg"
    img4 = tmp_path / "other_match.jpg"
    
    create_dummy_image(str(img1), "#FF6B6B") # Reddish
    create_dummy_image(str(img2), "#4ECDC4") # Teal
    create_dummy_image(str(img3), "#45B7D1") # Blue
    create_dummy_image(str(img4), "#96CEB4") # Green
    
    results = [
        (str(img1), 0),
        (str(img2), 4),
        (str(img3), 12),
        (str(img4), 25)
    ]
    
    # Trick: The ResultWidget uses QImageReader which might fail if format isn't guessed from extension or content
    # But QImage.save should write correct headers.
    
    app.search_area.lbl_results_title.setText(f"Found {len(results)} Matches")
    app.search_area.result_list.clear() # Clear default
    
    # We call show_results which does the logic
    app.search_area.show_results(results)
    
    # Set a fake search image/preview
    # Create a small thumbnail for the dropzone preview
    preview_path = tmp_path / "query_thumb.jpg"
    create_dummy_image(str(preview_path), "#FF6B6B")
    app.search_area.set_preview(path=str(preview_path))
    
    # 3. Wait for rendering
    qtbot.wait(1000)
    
    # 4. Capture
    # Ensure docs/assets exists
    assets_dir = os.path.join(os.getcwd(), "docs/assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    screenshot_path = os.path.join(assets_dir, "screenshot_main.png")
    screen = app.grab()
    screen.save(screenshot_path)
    
    print(f"\nSaved screenshot to: {screenshot_path}")
    assert os.path.exists(screenshot_path)
