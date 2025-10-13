#!/usr/bin/env python3
"""
Demo script showing how to use WeChat MP Material Cleaner programmatically
演示脚本：展示如何编程方式使用微信公众号素材清理工具
"""

import os
import sys
import logging
from wechat_mp_cleaner import WeChatMaterialCleaner, Config


def setup_logging():
    """Setup logging for demo"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def demo_basic_usage():
    """Demonstrate basic usage of the cleaner"""
    print("=" * 60)
    print("WeChat MP Material Cleaner Demo")
    print("微信公众号素材清理工具演示")
    print("=" * 60)
    
    # Check if credentials are available
    if not os.getenv('WECHAT_APP_ID') or not os.getenv('WECHAT_APP_SECRET'):
        print("❌ Error: WeChat credentials not found!")
        print("   Please set WECHAT_APP_ID and WECHAT_APP_SECRET environment variables")
        print("   或者创建 .env 文件并设置您的微信凭据")
        return False
    
    try:
        # Initialize configuration and cleaner
        config = Config()
        cleaner = WeChatMaterialCleaner(config)
        
        print("✅ Successfully initialized WeChat MP Material Cleaner")
        print("   成功初始化微信公众号素材清理工具")
        
        # Test connection
        print("\n📡 Testing connection...")
        access_token = cleaner.get_access_token()
        print(f"✅ Connection successful! Got access token: {access_token[:10]}...")
        
        # Get material list
        print("\n📋 Fetching material list...")
        materials, total_count = cleaner.get_material_list(material_type="image", count=5)
        
        print(f"✅ Found {total_count} total image materials")
        print(f"   Retrieved first {len(materials)} materials:")
        
        for i, material in enumerate(materials, 1):
            media_id = material.get('media_id', 'N/A')
            name = material.get('name', 'N/A')
            print(f"   {i}. {media_id} - {name}")
        
        # Demonstrate dry run cleanup
        print("\n🧹 Demonstrating dry run cleanup...")
        print("   (This will NOT delete anything)")
        
        dry_run_results = cleaner.clean_old_materials(
            material_type="image",
            days_old=365,  # Very old materials
            dry_run=True
        )
        
        if dry_run_results['would_delete'] > 0:
            print(f"📊 Dry run results: Would delete {dry_run_results['would_delete']} materials")
            print("   Materials that would be deleted:")
            for media_id in dry_run_results['materials'][:5]:
                print(f"   - {media_id}")
            if len(dry_run_results['materials']) > 5:
                print(f"   ... and {len(dry_run_results['materials']) - 5} more")
        else:
            print("📊 No old materials found to delete")
        
        print("\n🎉 Demo completed successfully!")
        print("   演示成功完成！")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during demo: {str(e)}")
        print(f"   演示过程中出错：{str(e)}")
        return False


def demo_advanced_usage():
    """Demonstrate advanced usage patterns"""
    print("\n" + "=" * 60)
    print("Advanced Usage Examples")
    print("高级使用示例")
    print("=" * 60)
    
    # Example configurations
    print("\n📋 Example 1: Custom configuration")
    custom_config = Config.from_dict({
        'app_id': 'your_app_id',
        'app_secret': 'your_app_secret',
        'timeout': 60,
        'retry_times': 5
    })
    print("   Custom config created with extended timeout and retries")
    
    print("\n📋 Example 2: Batch operations")
    print("   # Get all materials")
    print("   materials = cleaner.get_all_materials('image')")
    print("   ")
    print("   # Filter by criteria (example)")
    print("   old_materials = [m for m in materials if should_delete(m)]")
    print("   ")
    print("   # Delete in batches")
    print("   media_ids = [m['media_id'] for m in old_materials]")
    print("   results = cleaner.batch_delete_materials(media_ids)")
    
    print("\n📋 Example 3: Different material types")
    material_types = ["image", "video", "voice", "news"]
    for mat_type in material_types:
        print(f"   - Clean {mat_type} materials: cleaner.clean_old_materials('{mat_type}', days_old=30)")


if __name__ == "__main__":
    setup_logging()
    
    print("Starting WeChat MP Material Cleaner Demo...")
    print("开始微信公众号素材清理工具演示...")
    
    # Run basic demo
    success = demo_basic_usage()
    
    # Show advanced examples
    demo_advanced_usage()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Demo completed successfully!")
        print("   For more information, run: wechat-cleaner --help")
    else:
        print("❌ Demo failed. Please check your configuration.")
        print("   Make sure to set your WeChat credentials first.")
    
    print("\n💡 Next steps:")
    print("   1. Set up your .env file with WeChat credentials")
    print("   2. Run: wechat-cleaner test-connection")
    print("   3. List materials: wechat-cleaner list-materials")
    print("   4. Clean old materials: wechat-cleaner clean-old --dry-run")
    print("=" * 60)