import sys
import multiprocessing
from PyQt6.QtWidgets import QApplication
from src.finder_sight.ui.main_window import ImageFinderApp

def main():
    # Must be called at the very beginning for multiprocessing in frozen apps
    multiprocessing.freeze_support()
    
    app = QApplication(sys.argv)
    window = ImageFinderApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
