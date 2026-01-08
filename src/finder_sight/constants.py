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
# Search settings
DEFAULT_MAX_RESULTS = 20
HASH_SIZE = 16  # 16x16 = 256 bits
MAX_HASH_DIST = HASH_SIZE * HASH_SIZE  # 256
# Default to 80% match
DEFAULT_SIMILARITY_THRESHOLD = 80 
DEFAULT_PHASH_THRESHOLD = 15  # Fallback

# Indexing
INDEX_VERSION = "v4_hires"  # Increment to force re-indexing


# UI settings
THUMBNAIL_SIZE = 100
