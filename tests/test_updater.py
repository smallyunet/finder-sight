import unittest
from unittest.mock import patch, MagicMock
from src.finder_sight.utils.updater import check_for_updates, parse_version

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
        
        available, latest, url = check_for_updates("0.9.0", "owner", "repo")
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
        
        available, latest, url = check_for_updates("0.9.0", "owner", "repo")
        self.assertFalse(available)

if __name__ == '__main__':
    unittest.main()
