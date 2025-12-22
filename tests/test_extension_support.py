import pytest
from src.finder_sight.constants import SUPPORTED_EXTENSIONS

def test_supported_extensions_include_svg_and_ico():
    assert '.svg' in SUPPORTED_EXTENSIONS
    assert '.ico' in SUPPORTED_EXTENSIONS
