"""Unit tests for processor module."""

import json
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock

import pytest
import requests
import yaml

from ydiskarc.cmds.processor import (
    Project,
    get_file,
    yd_get_full,
    yd_get_and_store_dir,
    validate_yandex_url,
    DEFAULT_CHUNK_SIZE,
    REQUEST_HEADER,
)


class TestGetFile:
    """Tests for get_file function."""

    @patch('ydiskarc.cmds.processor.requests.get')
    @patch('ydiskarc.cmds.processor.open', create=True)
    def test_get_file_basic(self, mock_open, mock_get):
        """Test basic file download."""
        # Mock response
        mock_response = Mock()
        mock_response.headers = {}
        mock_response.iter_content.return_value = [b'file content']
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Mock file operations
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        with tempfile.TemporaryDirectory() as tmpdir:
            get_file('http://example.com/file.txt', filepath=tmpdir)

        mock_get.assert_called_once()
        mock_file.write.assert_called()

    @patch('ydiskarc.cmds.processor.requests.get')
    def test_get_file_with_content_disposition(self, mock_get):
        """Test filename extraction from Content-Disposition header."""
        mock_response = Mock()
        mock_response.headers = {
            'Content-Disposition': 'filename="test file.txt"'
        }
        mock_response.iter_content.return_value = [b'content']
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('ydiskarc.cmds.processor.open', create=True) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file
                get_file('http://example.com/file', filepath=tmpdir)

        mock_get.assert_called_once()

    @patch('ydiskarc.cmds.processor.requests.get')
    def test_get_file_http_error(self, mock_get):
        """Test handling of HTTP errors."""
        mock_get.side_effect = requests.exceptions.HTTPError("404 Not Found")

        with pytest.raises(requests.exceptions.RequestException):
            get_file('http://example.com/missing')

    @patch('ydiskarc.cmds.processor.requests.get')
    def test_get_file_with_filesize(self, mock_get):
        """Test progress tracking with known file size."""
        mock_response = Mock()
        mock_response.headers = {}
        mock_response.iter_content.return_value = [b'x' * DEFAULT_CHUNK_SIZE]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('ydiskarc.cmds.processor.open', create=True) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file
                get_file('http://example.com/file', filepath=tmpdir, filesize=1000)

        mock_get.assert_called_once()


class TestYdGetFull:
    """Tests for yd_get_full function."""

    @patch('ydiskarc.cmds.processor.requests.get')
    @patch('ydiskarc.cmds.processor.get_file')
    def test_yd_get_full_basic(self, mock_get_file, mock_get):
        """Test basic full resource download."""
        # Mock metadata response
        mock_meta_resp = Mock()
        mock_meta_resp.text = '{"name": "test"}'
        mock_meta_resp.raise_for_status = Mock()

        # Mock download link response
        mock_dl_resp = Mock()
        mock_dl_resp.json.return_value = {'href': 'http://example.com/download'}
        mock_dl_resp.raise_for_status = Mock()
        mock_get.side_effect = [mock_meta_resp, mock_dl_resp]

        with tempfile.TemporaryDirectory() as tmpdir:
            yd_get_full('https://disk.yandex.ru/d/test123', tmpdir, None, False)

        assert mock_get.call_count == 2
        mock_get_file.assert_called_once()

    @patch('ydiskarc.cmds.processor.requests.get')
    def test_yd_get_full_with_metadata(self, mock_get):
        """Test downloading with metadata."""
        mock_meta_resp = Mock()
        mock_meta_resp.text = '{"name": "test", "type": "file"}'
        mock_meta_resp.raise_for_status = Mock()

        mock_dl_resp = Mock()
        mock_dl_resp.json.return_value = {'href': 'http://example.com/download'}
        mock_dl_resp.raise_for_status = Mock()
        mock_get.side_effect = [mock_meta_resp, mock_dl_resp]

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('ydiskarc.cmds.processor.get_file') as mock_get_file:
                yd_get_full('https://disk.yandex.ru/d/test123', tmpdir, None, True)

                # Check metadata file was created
                metadata_file = os.path.join(tmpdir, '_metadata.json')
                assert os.path.exists(metadata_file)

    @patch('ydiskarc.cmds.processor.requests.get')
    def test_yd_get_full_no_download_url(self, mock_get):
        """Test error when download URL is missing."""
        mock_resp = Mock()
        mock_resp.json.return_value = {}  # No 'href' key
        mock_resp.raise_for_status = Mock()
        mock_get.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="No download url"):
                yd_get_full('https://disk.yandex.ru/d/test123', tmpdir, None, False)


class TestYdGetAndStoreDir:
    """Tests for yd_get_and_store_dir function."""

    @patch('ydiskarc.cmds.processor.requests.get')
    def test_yd_get_and_store_dir_basic(self, mock_get):
        """Test basic directory metadata retrieval."""
        mock_resp = Mock()
        mock_resp.text = json.dumps({
            'name': 'test_dir',
            'type': 'dir',
            '_embedded': {
                'items': []
            }
        })
        mock_resp.json.return_value = {
            'name': 'test_dir',
            'type': 'dir',
            '_embedded': {
                'items': []
            }
        }
        mock_resp.raise_for_status = Mock()
        mock_get.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmpdir:
            result = yd_get_and_store_dir(
                'https://disk.yandex.ru/d/test123',
                '',
                tmpdir,
                update=False,
                nofiles=True,
                iterative=False
            )

            assert result is not None
            assert os.path.exists(os.path.join(tmpdir, '_metadata.json'))

    @patch('ydiskarc.cmds.processor.requests.get')
    @patch('ydiskarc.cmds.processor.get_file')
    def test_yd_get_and_store_dir_with_files(self, mock_get_file, mock_get):
        """Test directory processing with files."""
        mock_resp = Mock()
        mock_resp.text = json.dumps({
            'name': 'test_dir',
            'type': 'dir',
            '_embedded': {
                'items': [
                    {
                        'type': 'file',
                        'path': 'test_file.txt',
                        'file': 'http://example.com/file.txt',
                        'size': 100
                    }
                ]
            }
        })
        mock_resp.json.return_value = {
            'name': 'test_dir',
            'type': 'dir',
            '_embedded': {
                'items': [
                    {
                        'type': 'file',
                        'path': 'test_file.txt',
                        'file': 'http://example.com/file.txt',
                        'size': 100
                    }
                ]
            }
        }
        mock_resp.raise_for_status = Mock()
        mock_get.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmpdir:
            yd_get_and_store_dir(
                'https://disk.yandex.ru/d/test123',
                '',
                tmpdir,
                update=False,
                nofiles=False,
                iterative=True
            )

            mock_get_file.assert_called()


class TestProject:
    """Tests for Project class."""

    def test_project_init(self):
        """Test Project initialization."""
        project = Project()
        assert project is not None

    @patch('ydiskarc.cmds.processor.yd_get_and_store_dir')
    def test_project_sync(self, mock_yd_get):
        """Test sync method."""
        project = Project()
        with tempfile.TemporaryDirectory() as tmpdir:
            project.sync('https://disk.yandex.ru/d/test123', tmpdir, False, False)
        mock_yd_get.assert_called_once()

    @patch('ydiskarc.cmds.processor.yd_get_full')
    def test_project_full(self, mock_yd_get):
        """Test full method."""
        project = Project()
        with tempfile.TemporaryDirectory() as tmpdir:
            project.full('https://disk.yandex.ru/d/test123', tmpdir, None, False)
        mock_yd_get.assert_called_once()

    def test_project_configure_new(self):
        """Test configuration creation."""
        project = Project()
        with tempfile.TemporaryDirectory() as tmpdir:
            project.configure('test_key', tmpdir)
            config_file = os.path.join(tmpdir, '.ydiskarc')
            assert os.path.exists(config_file)
            with open(config_file, 'r', encoding='utf8') as f:
                config = yaml.safe_load(f)
                assert config['keys']['yandex_oauth'] == 'test_key'

    def test_project_configure_existing(self):
        """Test updating existing configuration."""
        project = Project()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, '.ydiskarc')
            # Create existing config
            with open(config_file, 'w', encoding='utf8') as f:
                yaml.safe_dump({'keys': {'other_key': 'value'}}, f)
            
            project.configure('new_key', tmpdir)
            
            with open(config_file, 'r', encoding='utf8') as f:
                config = yaml.safe_load(f)
                assert config['keys']['yandex_oauth'] == 'new_key'
                assert config['keys']['other_key'] == 'value'


class TestValidateYandexUrl:
    """Tests for URL validation function."""

    def test_validate_yandex_url_valid_directory(self):
        """Test validation of valid directory URL."""
        assert validate_yandex_url('https://disk.yandex.ru/d/ABC123') is True
        assert validate_yandex_url('https://disk.yandex.ru/d/test-folder_123') is True

    def test_validate_yandex_url_valid_file(self):
        """Test validation of valid file URL."""
        assert validate_yandex_url('https://disk.yandex.ru/i/XYZ789') is True
        assert validate_yandex_url('https://disk.yandex.ru/i/file-name_456') is True

    def test_validate_yandex_url_alternative_domain(self):
        """Test validation with alternative domain."""
        assert validate_yandex_url('https://disk.yandex.com/d/ABC123') is True
        assert validate_yandex_url('https://disk.yandex.com/i/XYZ789') is True

    def test_validate_yandex_url_invalid(self):
        """Test validation rejects invalid URLs."""
        assert validate_yandex_url('https://example.com/file') is False
        assert validate_yandex_url('not-a-url') is False
        assert validate_yandex_url('https://disk.yandex.ru/') is False
        assert validate_yandex_url('https://disk.yandex.ru/d/') is False
        assert validate_yandex_url('http://disk.yandex.ru/d/ABC123') is False  # http not https


class TestEdgeCases:
    """Tests for edge cases and error scenarios."""

    @patch('ydiskarc.cmds.processor.create_session_with_retries')
    def test_get_file_timeout(self, mock_session):
        """Test handling of network timeout."""
        mock_session.return_value.get.side_effect = requests.exceptions.Timeout("Connection timeout")
        
        with pytest.raises(requests.exceptions.RequestException):
            get_file('http://example.com/file')

    @patch('ydiskarc.cmds.processor.create_session_with_retries')
    def test_get_file_connection_error(self, mock_session):
        """Test handling of connection errors."""
        mock_session.return_value.get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with pytest.raises(requests.exceptions.RequestException):
            get_file('http://example.com/file')

    @patch('ydiskarc.cmds.processor.create_session_with_retries')
    def test_get_file_rate_limit(self, mock_session):
        """Test handling of rate limiting."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '10'}
        mock_response.raise_for_status = Mock()
        
        # Second response after retry
        mock_response2 = Mock()
        mock_response2.headers = {}
        mock_response2.iter_content.return_value = [b'content']
        mock_response2.raise_for_status = Mock()
        
        mock_session.return_value.get.side_effect = [mock_response, mock_response2]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('ydiskarc.cmds.processor.open', create=True) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file
                get_file('http://example.com/file', filepath=tmpdir)

    @patch('ydiskarc.cmds.processor.create_session_with_retries')
    def test_get_file_resume_existing_file(self, mock_session):
        """Test resume functionality with existing file."""
        mock_response = Mock()
        mock_response.headers = {}
        mock_response.iter_content.return_value = [b'additional content']
        mock_response.raise_for_status = Mock()
        mock_session.return_value.get.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create partial file
            partial_file = os.path.join(tmpdir, 'test.txt')
            with open(partial_file, 'wb') as f:
                f.write(b'existing content')
            
            with patch('ydiskarc.cmds.processor.open', create=True) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file
                get_file('http://example.com/test.txt', filepath=tmpdir, filename='test.txt', resume=True)
            
            # Check that Range header was used
            calls = mock_session.return_value.get.call_args_list
            assert any('Range' in str(call) for call in calls)

    @patch('ydiskarc.cmds.processor.create_session_with_retries')
    def test_get_file_io_error(self, mock_session):
        """Test handling of file I/O errors."""
        mock_response = Mock()
        mock_response.headers = {}
        mock_response.iter_content.return_value = [b'content']
        mock_response.raise_for_status = Mock()
        mock_session.return_value.get.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a directory with the same name as the file to cause I/O error
            file_path = os.path.join(tmpdir, 'test.txt')
            os.makedirs(file_path, exist_ok=True)
            
            with pytest.raises(IOError):
                get_file('http://example.com/test.txt', filepath=tmpdir, filename='test.txt')

    @patch('ydiskarc.cmds.processor.create_session_with_retries')
    def test_yd_get_full_invalid_json(self, mock_session):
        """Test handling of invalid JSON response."""
        mock_resp = Mock()
        mock_resp.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_resp.raise_for_status = Mock()
        mock_session.return_value.get.return_value = mock_resp
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="Invalid response from API"):
                yd_get_full('https://disk.yandex.ru/d/test123', tmpdir, None, False)

    @patch('ydiskarc.cmds.processor.create_session_with_retries')
    def test_yd_get_and_store_dir_missing_path_key(self, mock_session):
        """Test handling of missing path key in API response."""
        mock_resp = Mock()
        mock_resp.text = json.dumps({
            'name': 'test_dir',
            'type': 'dir',
            '_embedded': {
                'items': [
                    {
                        'type': 'file',
                        # Missing 'path' key
                        'file': 'http://example.com/file.txt'
                    }
                ]
            }
        })
        mock_resp.json.return_value = {
            'name': 'test_dir',
            'type': 'dir',
            '_embedded': {
                'items': [
                    {
                        'type': 'file',
                        'file': 'http://example.com/file.txt'
                    }
                ]
            }
        }
        mock_resp.raise_for_status = Mock()
        mock_session.return_value.get.return_value = mock_resp
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Should not raise error, just skip items without path
            yd_get_and_store_dir(
                'https://disk.yandex.ru/d/test123',
                '',
                tmpdir,
                update=False,
                nofiles=False,
                iterative=True
            )

    @patch('ydiskarc.cmds.processor.create_session_with_retries')
    def test_yd_get_and_store_dir_permission_error(self, mock_session):
        """Test handling of permission errors when creating directories."""
        mock_resp = Mock()
        mock_resp.text = json.dumps({'name': 'test_dir', 'type': 'dir'})
        mock_resp.json.return_value = {'name': 'test_dir', 'type': 'dir'}
        mock_resp.raise_for_status = Mock()
        mock_session.return_value.get.return_value = mock_resp
        
        # Create a read-only directory
        with tempfile.TemporaryDirectory() as tmpdir:
            read_only_dir = os.path.join(tmpdir, 'readonly')
            os.makedirs(read_only_dir)
            os.chmod(read_only_dir, 0o444)  # Read-only
            
            try:
                with pytest.raises(OSError):
                    yd_get_and_store_dir(
                        'https://disk.yandex.ru/d/test123',
                        '',
                        read_only_dir,
                        update=False,
                        nofiles=True,
                        iterative=False
                    )
            finally:
                os.chmod(read_only_dir, 0o755)  # Restore permissions for cleanup

    def test_get_file_unicode_filename(self):
        """Test handling of Unicode filenames."""
        # This would be tested with actual Content-Disposition header containing Unicode
        # For now, we test that the code handles it gracefully
        pass  # Placeholder - would need actual Unicode test case
