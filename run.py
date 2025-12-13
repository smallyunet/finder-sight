import sys
from PyQt6.QtWidgets import QApplication
from src.finder_sight.ui.main_window import ImageFinderApp

def main():
    app = QApplication(sys.argv)
    window = ImageFinderApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
