from src.finder_sight.utils.paths import get_config_path, get_index_path

INDEX_FILE = str(get_index_path())
CONFIG_FILE = str(get_config_path())
SUPPORTED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.webp', '.bmp',
    '.gif',  # GIF images
    '.heic', '.heif',  # Apple HEIC format
    '.tiff', '.tif',  # TIFF images
    '.svg', '.ico'  # New formats
}

# Search settings
DEFAULT_MAX_RESULTS = 20
DEFAULT_SIMILARITY_THRESHOLD = 10  # Max Hamming distance for phash (dist <= threshold)

# UI settings
THUMBNAIL_SIZE = 100
