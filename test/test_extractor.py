import unittest
from unittest.mock import patch, mock_open, MagicMock
import io
import json
import os
import pandas as pd
import urllib.error as ue
# ~~~
from extract import JsonDataExtractor, IdhsDataExtractor


class MockArgs:
    """Mock arguments object to pass into the extractors."""

    def __init__(self, source):
        self.source = source


class TestJsonDataExtractor(unittest.TestCase):
    def setUp(self):
        self.args = MockArgs(source="fake_file.json")
        self.extractor = JsonDataExtractor(self.args)
        self.extractor.import_size = 2  # Small size for easier chunk testing

    @patch('os.path.exists')
    def test_load_json_file_not_found(self, mock_exists):
        """Should raise FileNotFoundError if the file does not exist."""
        mock_exists.return_value = False
        with self.assertRaises(FileNotFoundError):
            self.extractor.load_json_file()

    @patch('extract.ijson.items')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_source_header(self, mock_file, mock_ijson_items):
        """Should extract schema IDs properly from ijson items."""
        mock_ijson_items.return_value = [{"id": "col1"}, {"id": "col2"}]

        headers = self.extractor.get_source_header()

        self.assertEqual(headers, ["col1", "col2"])
        mock_file.assert_called_once_with("fake_file.json", "rb")

    # @patch('extract.ijson.items')
    # @patch('builtins.open', new_callable=mock_open)
    # def test_get_source_records_chunking(self, mock_file, mock_ijson_items):
    #     """Should yield chunks matching the import_size threshold."""
    #     # Yield 3 rows total. With import_size=2, it should yield 2 chunks (size 2 and size 1)
    #     mock_ijson_items.return_value = [["r1_v1", "r1_v2"], ["r2_v1", "r2_v2"], ["r3_v1", "r3_v2"]]
    #
    #     chunks = list(self.extractor.get_source_records())
    #
    #     self.assertEqual(len(chunks), 2)
    #     self.assertEqual(len(chunks[0]), 2)  # First chunk limit reached
    #     self.assertEqual(len(chunks[1]), 1)  # Leftovers

    @patch('os.path.exists')
    def test_load_json_file_success(self, mock_exists):
        """Should combine headers and chunked rows into a single unified DataFrame."""
        mock_exists.return_value = True

        # Stub the internal methods instead of patching deep dependencies again
        self.extractor.get_source_header = MagicMock(return_value=["A", "B"])
        self.extractor.get_source_records = MagicMock(return_value=[
            [["1", "2"], ["3", "4"]],
            [["5", "6"]]
        ])

        df = self.extractor.load_json_file()

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 3)
        self.assertEqual(list(df.columns), ["A", "B"])


class TestIdhsDataExtractor(unittest.TestCase):

    def setUp(self):
        self.args = MockArgs(source="http_trigger")
        self.extractor = IdhsDataExtractor(self.args)
        self.extractor.import_size = 5000

    @patch('extract.ur.urlopen')
    def test_get_emsr_incidents_dataset_success(self, mock_urlopen):
        """Should successfully parse HTTP response data and construct DataFrame."""
        # Mocking network response envelope
        fake_api_payload = {
            "success": True,
            "result": {
                "_links": {"next": "/api/3/action/datastore_search?offset=5000"},
                "fields": [{"id": "id"}, {"id": "name"}],
                "records": [{"id": 101, "name": "Incident A"}]
            }
        }

        # Setup mock context manager for urllib
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(fake_api_payload).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        source_url = "https://hub.mph.in.gov/api/3/action/datastore_search"
        next_url = self.extractor.get_emsr_incidents_dataset(source_url)

        # Assert next link resolved using up.urljoin rules
        self.assertIn("offset=5000", next_url)
        self.assertIsInstance(self.extractor.df, pd.DataFrame)
        self.assertEqual(len(self.extractor.df), 1)

    @patch('extract.ur.urlopen')
    def test_get_emsr_incidents_dataset_api_false_success(self, mock_urlopen):
        """Should fail gracefully if the payload element 'success' reads False."""
        fake_api_payload = {"success": False}

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(fake_api_payload).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        next_url = self.extractor.get_emsr_incidents_dataset("https://fake-url.com")

        self.assertIsNone(next_url)  # Code catches exception inside except block and returns full_next_url (None)

    @patch('extract.ur.urlopen')
    def test_get_emsr_incidents_dataset_network_error(self, mock_urlopen):
        """Should gracefully handle a urllib URLError exception."""
        mock_urlopen.side_effect = ue.URLError("Connection Timed Out")

        next_url = self.extractor.get_emsr_incidents_dataset("https://fake-url.com")

        self.assertIsNone(next_url)

    @patch.object(IdhsDataExtractor, 'get_emsr_incidents_dataset')
    def test_extract_sourcedata_pagination_loop(self, mock_get_dataset):
        """Should repeatedly request pages until get_emsr_incidents_dataset returns None."""
        # Loop control: return a next URL target first, then None to break loop
        mock_get_dataset.side_effect = ["https://fake-url.com", None]

        self.extractor.extract_sourcedata("test-resource-id")

        self.assertEqual(mock_get_dataset.call_count, 2)


if __name__ == '__main__':
    unittest.main()
