import sys
import os

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # In dev mode, we assume the relative path is from the project root
        # If relative_path is 'src/finder_sight/ui/style.qss', and we run from project root, it works.
        # But if we run from somewhere else, it might be safer to be relative to this file?
        # Let's assume relative_path starts from project root for now.
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
