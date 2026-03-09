"""
Tests for configuration module
"""

import os
import tempfile
import pytest
from wechat_mp_cleaner.config import Config


class TestConfig:
    """Test configuration management"""
    
    def test_config_from_env_vars(self):
        """Test configuration from environment variables"""
        # Set environment variables
        os.environ['WECHAT_APP_ID'] = 'test_app_id'
        os.environ['WECHAT_APP_SECRET'] = 'test_app_secret'
        
        config = Config()
        
        assert config.app_id == 'test_app_id'
        assert config.app_secret == 'test_app_secret'
        assert config.timeout == 30
        assert config.retry_times == 3
        
        # Clean up
        del os.environ['WECHAT_APP_ID']
        del os.environ['WECHAT_APP_SECRET']
    
    def test_config_from_env_file(self):
        """Test configuration from .env file"""
        # Create temporary .env file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write('WECHAT_APP_ID=file_app_id\n')
            f.write('WECHAT_APP_SECRET=file_app_secret\n')
            temp_file = f.name
        
        try:
            config = Config(temp_file)
            
            assert config.app_id == 'file_app_id'
            assert config.app_secret == 'file_app_secret'
        
        finally:
            os.unlink(temp_file)
    
    def test_config_validation_missing_app_id(self):
        """Test configuration validation with missing app_id"""
        config = Config()
        config.app_id = None
        
        with pytest.raises(ValueError, match="WECHAT_APP_ID is required"):
            config.validate()
    
    def test_config_validation_missing_app_secret(self):
        """Test configuration validation with missing app_secret"""
        config = Config()
        config.app_id = 'test_id'
        config.app_secret = None
        
        with pytest.raises(ValueError, match="WECHAT_APP_SECRET is required"):
            config.validate()
    
    def test_config_validation_success(self):
        """Test successful configuration validation"""
        config = Config()
        config.app_id = 'test_id'
        config.app_secret = 'test_secret'
        
        assert config.validate() is True
    
    def test_config_from_dict(self):
        """Test configuration from dictionary"""
        config_dict = {
            'app_id': 'dict_app_id',
            'app_secret': 'dict_app_secret',
            'timeout': 60,
            'retry_times': 5
        }
        
        config = Config.from_dict(config_dict)
        
        assert config.app_id == 'dict_app_id'
        assert config.app_secret == 'dict_app_secret'
        assert config.timeout == 60
        assert config.retry_times == 5