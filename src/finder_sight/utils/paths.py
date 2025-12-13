import os
import sys
from pathlib import Path

def get_user_data_dir(app_name="FinderSight"):
    """
    Get the standard user data directory for the application.
    
    macOS: ~/Library/Application Support/<app_name>
    Windows: %LOCALAPPDATA%/<app_name>
    Linux: ~/.local/share/<app_name>
    """
    home = Path.home()
    
    if sys.platform == 'darwin':
        data_dir = home / 'Library' / 'Application Support' / app_name
    elif sys.platform == 'win32':
        data_dir = Path(os.getenv('LOCALAPPDATA', home / 'AppData' / 'Local')) / app_name
    else:
        # Linux / Unix
        data_dir = Path(os.getenv('XDG_DATA_HOME', home / '.local' / 'share')) / app_name
        
    # Ensure directory exists
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def get_config_path(filename="config.json"):
    return get_user_data_dir() / filename

def get_index_path(filename="image_index.json"):
    return get_user_data_dir() / filename
