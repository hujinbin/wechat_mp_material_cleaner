"""
配置管理模块
Configuration management for WeChat MP API credentials and settings.
"""

import os
from typing import Optional
from dotenv import load_dotenv


class Config:
    """WeChat MP API configuration manager"""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            env_file: Path to .env file. If None, will look for .env in current directory
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        self.app_id = os.getenv('WECHAT_APP_ID')
        self.app_secret = os.getenv('WECHAT_APP_SECRET')
        
        # API endpoints
        self.base_url = "https://api.weixin.qq.com/cgi-bin"
        self.token_url = f"{self.base_url}/token"
        self.material_list_url = f"{self.base_url}/material/batchget_material"
        self.material_delete_url = f"{self.base_url}/material/del_material"
        
        # Request settings
        self.timeout = 30
        self.retry_times = 3
        self.retry_delay = 1
        
    def validate(self) -> bool:
        """
        Validate that required configuration is present
        
        Returns:
            bool: True if configuration is valid
        """
        if not self.app_id:
            raise ValueError("WECHAT_APP_ID is required in environment variables")
        
        if not self.app_secret:
            raise ValueError("WECHAT_APP_SECRET is required in environment variables")
        
        return True
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> 'Config':
        """
        Create configuration from dictionary
        
        Args:
            config_dict: Dictionary containing configuration values
            
        Returns:
            Config: Configuration instance
        """
        config = cls()
        config.app_id = config_dict.get('app_id')
        config.app_secret = config_dict.get('app_secret')
        
        if 'timeout' in config_dict:
            config.timeout = config_dict['timeout']
        if 'retry_times' in config_dict:
            config.retry_times = config_dict['retry_times']
        if 'retry_delay' in config_dict:
            config.retry_delay = config_dict['retry_delay']
            
        return config