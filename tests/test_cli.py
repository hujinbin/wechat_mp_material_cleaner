"""
Tests for CLI module
"""

import os
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from wechat_mp_cleaner.cli import cli


class TestCLI:
    """Test CLI functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.runner = CliRunner()
        
        # Mock environment variables
        self.env_vars = {
            'WECHAT_APP_ID': 'test_app_id',
            'WECHAT_APP_SECRET': 'test_app_secret'
        }
    
    def test_cli_help(self):
        """Test CLI help message"""
        result = self.runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert '微信公众号图片素材批量删除工具' in result.output
        assert 'WeChat MP Material Cleaner' in result.output
    
    def test_cli_missing_credentials(self):
        """Test CLI with missing credentials"""
        result = self.runner.invoke(cli, ['test-connection'])
        
        assert result.exit_code == 1
        assert 'Configuration error' in result.output
    
    @patch.dict(os.environ, {'WECHAT_APP_ID': 'test_id', 'WECHAT_APP_SECRET': 'test_secret'})
    @patch('wechat_mp_cleaner.cleaner.WeChatMaterialCleaner.get_access_token')
    @patch('wechat_mp_cleaner.cleaner.WeChatMaterialCleaner.get_material_list')
    def test_list_materials_command(self, mock_get_material_list, mock_get_access_token):
        """Test list-materials command"""
        # Mock API responses
        mock_get_access_token.return_value = 'mock_token'
        mock_get_material_list.return_value = (
            [{'media_id': 'test_id_1', 'name': 'test.jpg', 'update_time': 1640995200}],
            1
        )
        
        result = self.runner.invoke(cli, ['list-materials', '--type', 'image', '--count', '1'])
        
        assert result.exit_code == 0
        assert 'Found 1 materials' in result.output
    
    @patch.dict(os.environ, {'WECHAT_APP_ID': 'test_id', 'WECHAT_APP_SECRET': 'test_secret'})
    @patch('wechat_mp_cleaner.cleaner.WeChatMaterialCleaner.get_access_token')
    @patch('wechat_mp_cleaner.cleaner.WeChatMaterialCleaner.get_material_list')
    def test_test_connection_command(self, mock_get_material_list, mock_get_access_token):
        """Test test-connection command"""
        # Mock API responses
        mock_get_access_token.return_value = 'mock_token'
        mock_get_material_list.return_value = ([], 0)
        
        result = self.runner.invoke(cli, ['test-connection'])
        
        assert result.exit_code == 0
        assert 'Connection test passed!' in result.output
    
    @patch.dict(os.environ, {'WECHAT_APP_ID': 'test_id', 'WECHAT_APP_SECRET': 'test_secret'})
    def test_delete_command_no_confirmation(self):
        """Test delete command without confirmation"""
        result = self.runner.invoke(cli, ['delete', 'test_media_id'], input='n')
        
        assert result.exit_code == 0
        assert 'Operation cancelled' in result.output