"""
微信公众号素材清理核心模块
Core WeChat MP material cleaning functionality.
"""

import json
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import Config


class WeChatAPIError(Exception):
    """WeChat API 错误"""
    pass


class WeChatMaterialCleaner:
    """WeChat MP material cleaner main class"""
    
    def __init__(self, config: Config):
        """
        Initialize the cleaner
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.config.validate()
        
        self.access_token = None
        self.token_expires_at = 0
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Setup requests session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=self.config.retry_times,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def get_access_token(self) -> str:
        """
        Get WeChat access token
        
        Returns:
            str: Access token
            
        Raises:
            WeChatAPIError: If failed to get access token
        """
        current_time = time.time()
        
        # Check if token is still valid (with 5 minute buffer)
        if self.access_token and current_time < (self.token_expires_at - 300):
            return self.access_token
        
        params = {
            'grant_type': 'client_credential',
            'appid': self.config.app_id,
            'secret': self.config.app_secret
        }
        
        try:
            response = self.session.get(
                self.config.token_url,
                params=params,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            if 'access_token' not in data:
                error_msg = data.get('errmsg', 'Unknown error')
                raise WeChatAPIError(f"Failed to get access token: {error_msg}")
            
            self.access_token = data['access_token']
            expires_in = data.get('expires_in', 7200)  # Default 2 hours
            self.token_expires_at = current_time + expires_in
            
            self.logger.info("Successfully obtained access token")
            return self.access_token
            
        except requests.RequestException as e:
            raise WeChatAPIError(f"Network error when getting access token: {str(e)}")
    
    def get_material_list(self, material_type: str = "image", offset: int = 0, count: int = 20) -> Tuple[List[Dict], int]:
        """
        Get material list from WeChat API
        
        Args:
            material_type: Type of material (image, video, voice, news)
            offset: Offset for pagination
            count: Number of items to fetch (max 20)
            
        Returns:
            Tuple[List[Dict], int]: (materials list, total count)
            
        Raises:
            WeChatAPIError: If API request fails
        """
        access_token = self.get_access_token()
        
        url = f"{self.config.material_list_url}?access_token={access_token}"
        
        payload = {
            "type": material_type,
            "offset": offset,
            "count": min(count, 20)  # WeChat API limit
        }
        
        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            if 'errcode' in data and data['errcode'] != 0:
                error_msg = data.get('errmsg', 'Unknown error')
                raise WeChatAPIError(f"API error: {error_msg} (code: {data['errcode']})")
            
            total_count = data.get('total_count', 0)
            materials = data.get('item', [])
            
            self.logger.info(f"Retrieved {len(materials)} materials (offset: {offset}, total: {total_count})")
            return materials, total_count
            
        except requests.RequestException as e:
            raise WeChatAPIError(f"Network error when getting material list: {str(e)}")
    
    def delete_material(self, media_id: str) -> bool:
        """
        Delete a single material
        
        Args:
            media_id: Media ID to delete
            
        Returns:
            bool: True if successful
            
        Raises:
            WeChatAPIError: If deletion fails
        """
        access_token = self.get_access_token()
        
        url = f"{self.config.material_delete_url}?access_token={access_token}"
        
        payload = {
            "media_id": media_id
        }
        
        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            if 'errcode' in data and data['errcode'] != 0:
                error_msg = data.get('errmsg', 'Unknown error')
                raise WeChatAPIError(f"Failed to delete material {media_id}: {error_msg} (code: {data['errcode']})")
            
            self.logger.info(f"Successfully deleted material: {media_id}")
            return True
            
        except requests.RequestException as e:
            raise WeChatAPIError(f"Network error when deleting material {media_id}: {str(e)}")
    
    def batch_delete_materials(self, material_ids: List[str], delay: float = 0.5) -> Dict[str, Any]:
        """
        Batch delete materials
        
        Args:
            material_ids: List of material IDs to delete
            delay: Delay between deletions (seconds) to avoid rate limiting
            
        Returns:
            Dict: Summary of deletion results
        """
        results = {
            'total': len(material_ids),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        self.logger.info(f"Starting batch deletion of {len(material_ids)} materials")
        
        for i, media_id in enumerate(material_ids, 1):
            try:
                self.delete_material(media_id)
                results['successful'] += 1
                self.logger.info(f"Progress: {i}/{len(material_ids)} - Deleted {media_id}")
                
            except WeChatAPIError as e:
                results['failed'] += 1
                error_info = {
                    'media_id': media_id,
                    'error': str(e)
                }
                results['errors'].append(error_info)
                self.logger.error(f"Failed to delete {media_id}: {str(e)}")
            
            # Add delay to avoid rate limiting
            if delay > 0 and i < len(material_ids):
                time.sleep(delay)
        
        self.logger.info(f"Batch deletion completed. Success: {results['successful']}, Failed: {results['failed']}")
        return results
    
    def get_all_materials(self, material_type: str = "image") -> List[Dict]:
        """
        Get all materials of specified type
        
        Args:
            material_type: Type of material to fetch
            
        Returns:
            List[Dict]: List of all materials
        """
        all_materials = []
        offset = 0
        page_size = 20
        
        self.logger.info(f"Fetching all {material_type} materials")
        
        while True:
            materials, total_count = self.get_material_list(
                material_type=material_type,
                offset=offset,
                count=page_size
            )
            
            if not materials:
                break
                
            all_materials.extend(materials)
            offset += len(materials)
            
            # Break if we've fetched all materials
            if offset >= total_count:
                break
        
        self.logger.info(f"Retrieved {len(all_materials)} total materials")
        return all_materials
    
    def clean_old_materials(self, material_type: str = "image", days_old: int = 30, dry_run: bool = True) -> Dict[str, Any]:
        """
        Clean materials older than specified days
        
        Args:
            material_type: Type of material to clean
            days_old: Delete materials older than this many days
            dry_run: If True, only show what would be deleted without actually deleting
            
        Returns:
            Dict: Summary of what was or would be deleted
        """
        current_time = time.time()
        cutoff_time = current_time - (days_old * 24 * 60 * 60)
        
        materials = self.get_all_materials(material_type)
        
        old_materials = []
        for material in materials:
            # Extract creation time from material info
            update_time = material.get('update_time', 0)
            if update_time < cutoff_time:
                old_materials.append(material)
        
        self.logger.info(f"Found {len(old_materials)} materials older than {days_old} days")
        
        if dry_run:
            return {
                'dry_run': True,
                'would_delete': len(old_materials),
                'materials': [m.get('media_id') for m in old_materials]
            }
        
        # Perform actual deletion
        material_ids = [m.get('media_id') for m in old_materials if m.get('media_id')]
        return self.batch_delete_materials(material_ids)