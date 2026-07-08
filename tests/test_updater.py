import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.finder_sight.utils.updater import (
    check_for_updates,
    get_release_asset_download_url,
    parse_version,
)

class TestUpdater(unittest.TestCase):
    def test_parse_version(self):
        self.assertEqual(parse_version("1.0.0"), (1, 0, 0))
        self.assertEqual(parse_version("v1.2.3"), (1, 2, 3))
        self.assertEqual(parse_version("0.0.6"), (0, 0, 6))
        
    def test_version_compare(self):
        self.assertTrue(parse_version("1.0.1") > parse_version("1.0.0"))
        self.assertTrue(parse_version("0.1.0") > parse_version("0.0.9"))
        self.assertFalse(parse_version("1.0.0") > parse_version("1.0.0"))
        
    @patch('urllib.request.urlopen')
    def test_check_updates_newer(self, mock_urlopen):
        # Mock API response for newer version
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"tag_name": "v1.0.0", "html_url": "http://example.com"}'
        mock_response.__enter__.return_value = mock_response
        
        mock_urlopen.return_value = mock_response
        
        available, latest, url, error = check_for_updates("0.9.0", "owner", "repo")
        self.assertTrue(available)
        self.assertEqual(latest, "v1.0.0")
        self.assertEqual(url, "http://example.com")

    @patch('urllib.request.urlopen')
    def test_check_updates_older(self, mock_urlopen):
        # Mock API response for same/older version
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"tag_name": "v0.9.0", "html_url": "http://example.com"}'
        mock_response.__enter__.return_value = mock_response
        
        mock_urlopen.return_value = mock_response
        
        available, latest, url, error = check_for_updates("0.9.0", "owner", "repo")
        self.assertFalse(available)

    @patch('urllib.request.urlopen')
    def test_get_release_asset_download_url_prefers_named_dmg(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({
            "assets": [
                {
                    "name": "other.dmg",
                    "browser_download_url": "http://example.com/other.dmg",
                    "size": 1,
                },
                {
                    "name": "FinderSight-macOS.dmg",
                    "browser_download_url": "http://example.com/FinderSight-macOS.dmg",
                    "size": 42,
                },
            ]
        }).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        url, size = get_release_asset_download_url("owner", "repo", "v1.0.0")

        self.assertEqual(url, "http://example.com/FinderSight-macOS.dmg")
        self.assertEqual(size, 42)

if __name__ == '__main__':
    unittest.main()
