"""
Comprehensive tests for OpenCast CLI.
Target: 100% test coverage.
"""
import json
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from io import StringIO
import argparse

import pytest
import httpx

# Add cli directory to path
sys.path.insert(0, str(Path(__file__).parent))

from opencast_cli import OpenCastCLI, create_parser, main


class TestOpenCastCLI:
    """Test cases for OpenCastCLI class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('opencast_cli.CONFIG_FILE')
    def test_load_config_file_not_exists(self, mock_config_file):
        """Test loading config when file doesn't exist."""
        mock_config_file.exists.return_value = False
        cli = OpenCastCLI()
        assert cli.load_config() == {}
    
    @patch('opencast_cli.CONFIG_FILE')
    @patch('builtins.open', new_callable=mock_open, read_data='{"base_url": "http://test.com"}')
    def test_load_config_success(self, mock_file, mock_config_file):
        """Test successful config loading."""
        mock_config_file.exists.return_value = True
        cli = OpenCastCLI()
        config = cli.load_config()
        assert config == {"base_url": "http://test.com"}
    
    def test_get_base_url_default(self):
        """Test getting default base URL."""
        cli = OpenCastCLI()
        cli.config = {}
        assert cli.get_base_url() == "http://localhost:8000"
    
    def test_get_headers_no_token(self):
        """Test getting headers without token."""
        cli = OpenCastCLI()
        cli.tokens = {}
        headers = cli.get_headers()
        assert headers == {'Content-Type': 'application/json'}
    
    @patch('httpx.Client.get')
    def test_make_request_get_success(self, mock_get):
        """Test successful GET request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"result": "success"}'
        mock_response.json.return_value = {"result": "success"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        cli = OpenCastCLI()
        result = cli.make_request('GET', '/test/')
        assert result == {"result": "success"}
    
    def test_cmd_configure_set_base_url(self):
        """Test configure command setting base URL."""
        cli = OpenCastCLI()
        cli.config = {}
        
        args = argparse.Namespace(base_url="http://new.com", show=False)
        
        with patch.object(cli, 'save_config') as mock_save:
            cli.cmd_configure(args)
            mock_save.assert_called_once()
    
    def test_cmd_login_success(self):
        """Test successful login."""
        cli = OpenCastCLI()
        args = argparse.Namespace(email="test@test.com", password="password")
        
        with patch.object(cli, 'make_request') as mock_request, \
             patch.object(cli, 'save_tokens') as mock_save:
            mock_request.return_value = {"access": "token123", "refresh": "refresh123"}
            cli.cmd_login(args)
            mock_save.assert_called_once()
    
    def test_cmd_login_missing_credentials(self):
        """Test login with missing credentials."""
        cli = OpenCastCLI()
        args = argparse.Namespace(email=None, password="test")
        
        with pytest.raises(SystemExit):
            cli.cmd_login(args)
    
    def test_cmd_logout(self):
        """Test logout command."""
        cli = OpenCastCLI()
        cli.tokens = {"refresh_token": "refresh123"}
        args = argparse.Namespace()
        
        with patch.object(cli, 'make_request') as mock_request, \
             patch.object(cli, 'save_tokens') as mock_save:
            cli.cmd_logout(args)
            mock_save.assert_called_with({})
    
    def test_cmd_profile_success(self):
        """Test successful profile retrieval."""
        cli = OpenCastCLI()
        args = argparse.Namespace()
        
        with patch.object(cli, 'make_request') as mock_request:
            mock_request.return_value = {"email": "test@test.com"}
            with patch('sys.stdout', new=StringIO()) as fake_out:
                cli.cmd_profile(args)
                output = fake_out.getvalue()
                assert "User Profile:" in output
    
    def test_cmd_organizations_success(self):
        """Test successful organizations listing."""
        cli = OpenCastCLI()
        args = argparse.Namespace()
        
        with patch.object(cli, 'make_request') as mock_request:
            mock_request.return_value = {
                "results": [{"name": "Test Org", "id": 1}]
            }
            with patch('sys.stdout', new=StringIO()) as fake_out:
                cli.cmd_organizations(args)
                output = fake_out.getvalue()
                assert "Organizations:" in output
                assert "Test Org" in output
    
    def test_cmd_create_org_success(self):
        """Test successful organization creation."""
        cli = OpenCastCLI()
        args = argparse.Namespace(name="New Org", description="Test org")
        
        with patch.object(cli, 'make_request') as mock_request:
            mock_request.return_value = {"id": 1, "name": "New Org"}
            with patch('sys.stdout', new=StringIO()) as fake_out:
                cli.cmd_create_org(args)
                output = fake_out.getvalue()
                assert "created successfully" in output
    
    def test_cmd_memberships_success(self):
        """Test successful memberships listing."""
        cli = OpenCastCLI()
        args = argparse.Namespace()
        
        with patch.object(cli, 'make_request') as mock_request:
            mock_request.return_value = {
                "results": [{
                    "organization": {"name": "Test Org"},
                    "role": {"name": "Admin"}
                }]
            }
            with patch('sys.stdout', new=StringIO()) as fake_out:
                cli.cmd_memberships(args)
                output = fake_out.getvalue()
                assert "Your Memberships:" in output
                assert "Test Org: Admin" in output
    
    # Additional CLI tests for better coverage
    @patch('opencast_cli.TOKENS_FILE')
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    def test_load_tokens_json_error(self, mock_file, mock_tokens_file):
        """Test tokens loading with JSON error."""
        mock_tokens_file.exists.return_value = True
        cli = OpenCastCLI()
        tokens = cli.load_tokens()
        assert tokens == {}
    
    @patch('opencast_cli.CONFIG_DIR')
    @patch('builtins.open', side_effect=IOError("Write error"))
    def test_save_tokens_io_error(self, mock_file, mock_config_dir):
        """Test tokens saving with IO error."""
        mock_config_dir.mkdir = MagicMock()
        cli = OpenCastCLI()
        tokens = {"access_token": "test123"}
        
        with pytest.raises(SystemExit):
            cli.save_tokens(tokens)
    
    def test_get_headers_with_token(self):
        """Test getting headers with token."""
        cli = OpenCastCLI()
        cli.tokens = {"access_token": "test123"}
        headers = cli.get_headers()
        expected = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test123'
        }
        assert headers == expected
    
    @patch('httpx.Client.post')
    def test_make_request_post_success(self, mock_post):
        """Test successful POST request."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.content = b'{"id": 1}'
        mock_response.json.return_value = {"id": 1}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        cli = OpenCastCLI()
        result = cli.make_request('POST', '/test/', {"data": "test"})
        assert result == {"id": 1}
    
    @patch('httpx.Client.put')
    def test_make_request_put_success(self, mock_put):
        """Test successful PUT request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"updated": true}'
        mock_response.json.return_value = {"updated": True}
        mock_response.raise_for_status = MagicMock()
        mock_put.return_value = mock_response
        
        cli = OpenCastCLI()
        result = cli.make_request('PUT', '/test/', {"data": "test"})
        assert result == {"updated": True}
    
    @patch('httpx.Client.delete')
    def test_make_request_delete_success(self, mock_delete):
        """Test successful DELETE request."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.content = b''
        mock_response.raise_for_status = MagicMock()
        mock_delete.return_value = mock_response
        
        cli = OpenCastCLI()
        result = cli.make_request('DELETE', '/test/')
        assert result == {}
    
    def test_make_request_unsupported_method(self):
        """Test unsupported HTTP method."""
        cli = OpenCastCLI()
        result = cli.make_request('PATCH', '/test/')
        assert result is None
    
    @patch('httpx.Client.get')
    def test_make_request_401_error(self, mock_get):
        """Test 401 authentication error."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        cli = OpenCastCLI()
        result = cli.make_request('GET', '/test/')
        assert result is None
    
    @patch('httpx.Client.get')
    def test_make_request_exception(self, mock_get):
        """Test request exception."""
        mock_get.side_effect = httpx.RequestError("Network error")
        
        cli = OpenCastCLI()
        result = cli.make_request('GET', '/test/')
        assert result is None
    
    def test_cmd_configure_show(self):
        """Test configure command show option."""
        cli = OpenCastCLI()
        cli.config = {"base_url": "http://test.com"}
        
        args = argparse.Namespace(base_url=None, show=True)
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            cli.cmd_configure(args)
            output = fake_out.getvalue()
            assert "Current configuration:" in output
    
    def test_cmd_login_failure(self):
        """Test login failure."""
        cli = OpenCastCLI()
        args = argparse.Namespace(email="test@test.com", password="password")
        
        with patch.object(cli, 'make_request') as mock_request:
            mock_request.return_value = None
            with pytest.raises(SystemExit):
                cli.cmd_login(args)
    
    def test_cmd_logout_without_token(self):
        """Test logout without refresh token."""
        cli = OpenCastCLI()
        cli.tokens = {}
        args = argparse.Namespace()
        
        with patch.object(cli, 'save_tokens') as mock_save:
            cli.cmd_logout(args)
            mock_save.assert_called_with({})
    
    def test_cmd_profile_failure(self):
        """Test profile retrieval failure."""
        cli = OpenCastCLI()
        args = argparse.Namespace()
        
        with patch.object(cli, 'make_request') as mock_request:
            mock_request.return_value = None
            with patch('sys.stdout', new=StringIO()) as fake_out:
                cli.cmd_profile(args)
                output = fake_out.getvalue()
                assert "Failed to get profile" in output
    
    def test_cmd_organizations_failure(self):
        """Test organizations listing failure."""
        cli = OpenCastCLI()
        args = argparse.Namespace()
        
        with patch.object(cli, 'make_request') as mock_request:
            mock_request.return_value = None
            with patch('sys.stdout', new=StringIO()) as fake_out:
                cli.cmd_organizations(args)
                output = fake_out.getvalue()
                assert "Failed to get organizations" in output
    
    def test_cmd_create_org_missing_name(self):
        """Test create organization with missing name."""
        cli = OpenCastCLI()
        args = argparse.Namespace(name=None, description="Test")
        
        with pytest.raises(SystemExit):
            cli.cmd_create_org(args)
    
    def test_cmd_create_org_failure(self):
        """Test organization creation failure."""
        cli = OpenCastCLI()
        args = argparse.Namespace(name="New Org", description="Test org")
        
        with patch.object(cli, 'make_request') as mock_request:
            mock_request.return_value = None
            with patch('sys.stdout', new=StringIO()) as fake_out:
                cli.cmd_create_org(args)
                output = fake_out.getvalue()
                assert "Failed to create organization" in output
    
    def test_cmd_memberships_failure(self):
        """Test memberships listing failure."""
        cli = OpenCastCLI()
        args = argparse.Namespace()
        
        with patch.object(cli, 'make_request') as mock_request:
            mock_request.return_value = None
            with patch('sys.stdout', new=StringIO()) as fake_out:
                cli.cmd_memberships(args)
                output = fake_out.getvalue()
                assert "Failed to get memberships" in output


class TestCLIParser:
    """Test cases for CLI argument parser."""
    
    def test_create_parser(self):
        """Test parser creation."""
        parser = create_parser()
        assert isinstance(parser, argparse.ArgumentParser)
    
    def test_parser_configure_command(self):
        """Test configure command parsing."""
        parser = create_parser()
        args = parser.parse_args(['configure', '--base-url', 'http://test.com'])
        assert args.command == 'configure'
        assert args.base_url == 'http://test.com'


class TestMainFunction:
    """Test cases for main function."""
    
    @patch('opencast_cli.create_parser')
    def test_main_no_command(self, mock_create_parser):
        """Test main function with no command."""
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = argparse.Namespace(command=None)
        mock_create_parser.return_value = mock_parser
        
        with pytest.raises(SystemExit):
            main() 