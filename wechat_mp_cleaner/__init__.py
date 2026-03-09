"""
微信公众号图片素材批量删除工具
WeChat MP Material Cleaner

A tool for batch deleting WeChat MP materials.
"""

__version__ = "1.0.0"
__author__ = "胡金斌"
__email__ = "hujinbin@example.com"

from .cleaner import WeChatMaterialCleaner
from .config import Config

__all__ = ["WeChatMaterialCleaner", "Config"]