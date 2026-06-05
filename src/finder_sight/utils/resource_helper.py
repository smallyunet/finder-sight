import sys
import os

def get_resource_path(relative_path):
    """Get an absolute resource path in dev and PyInstaller app bundles."""
    candidate_roots = []

    if getattr(sys, "frozen", False):
        executable_dir = os.path.dirname(sys.executable)
        candidate_roots.extend([
            getattr(sys, "_MEIPASS", ""),
            os.path.join(executable_dir, "..", "Resources"),
            os.path.join(executable_dir, "..", "Frameworks"),
            executable_dir,
        ])

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    candidate_roots.extend([project_root, os.path.abspath(".")])

    for root in candidate_roots:
        if not root:
            continue
        candidate = os.path.abspath(os.path.join(root, relative_path))
        if os.path.exists(candidate):
            return candidate

    return os.path.abspath(os.path.join(candidate_roots[0], relative_path))
