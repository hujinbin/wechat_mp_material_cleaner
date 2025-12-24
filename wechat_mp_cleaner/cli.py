"""
命令行界面
Command Line Interface for WeChat MP Material Cleaner
"""

import sys
import logging
import json
from pathlib import Path
from typing import Optional, List

import click
from colorama import init, Fore, Style

from .config import Config
from .cleaner import WeChatMaterialCleaner, WeChatAPIError

# Initialize colorama for cross-platform colored output
init()


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Reduce noise from requests library
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def print_success(message: str):
    """Print success message in green"""
    click.echo(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")


def print_error(message: str):
    """Print error message in red"""
    click.echo(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")


def print_warning(message: str):
    """Print warning message in yellow"""
    click.echo(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")


def print_info(message: str):
    """Print info message in blue"""
    click.echo(f"{Fore.BLUE}ℹ {message}{Style.RESET_ALL}")


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to configuration file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, config: Optional[str], verbose: bool):
    """
    微信公众号图片素材批量删除工具
    
    WeChat MP Material Cleaner - A tool for batch managing WeChat MP materials.
    
    Before using this tool, make sure to set up your WeChat credentials:
    
    \b
    1. Create a .env file with:
       WECHAT_APP_ID=your_app_id
       WECHAT_APP_SECRET=your_app_secret
    
    \b
    2. Or set environment variables:
       export WECHAT_APP_ID=your_app_id
       export WECHAT_APP_SECRET=your_app_secret
    """
    ctx.ensure_object(dict)
    
    setup_logging(verbose)
    
    try:
        if config:
            ctx.obj['config'] = Config(config)
        else:
            ctx.obj['config'] = Config()
            
        ctx.obj['cleaner'] = WeChatMaterialCleaner(ctx.obj['config'])
        
    except (ValueError, WeChatAPIError) as e:
        print_error(f"Configuration error: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option('--type', '-t', default='image', type=click.Choice(['image', 'video', 'voice', 'news']),
              help='Type of materials to list')
@click.option('--count', '-c', default=20, type=click.IntRange(1, 20), 
              help='Number of materials to show (max 20)')
@click.option('--offset', '-o', default=0, type=click.IntRange(0), 
              help='Offset for pagination')
@click.option('--output', type=click.Path(), help='Save results to JSON file')
@click.pass_context
def list_materials(ctx, type: str, count: int, offset: int, output: Optional[str]):
    """List WeChat MP materials"""
    cleaner = ctx.obj['cleaner']
    
    try:
        print_info(f"Fetching {type} materials (offset: {offset}, count: {count})...")
        
        materials, total_count = cleaner.get_material_list(
            material_type=type,
            offset=offset,
            count=count
        )
        
        if not materials:
            print_warning("No materials found")
            return
        
        print_success(f"Found {len(materials)} materials (Total: {total_count})")
        
        # Display materials
        for i, material in enumerate(materials, offset + 1):
            media_id = material.get('media_id', 'N/A')
            name = material.get('name', 'N/A')
            update_time = material.get('update_time', 0)
            
            if update_time:
                import datetime
                update_date = datetime.datetime.fromtimestamp(update_time).strftime('%Y-%m-%d %H:%M:%S')
            else:
                update_date = 'N/A'
            
            click.echo(f"{i:3}. {media_id:<30} {name:<20} {update_date}")
        
        # Save to file if requested
        if output:
            output_data = {
                'materials': materials,
                'total_count': total_count,
                'offset': offset,
                'type': type
            }
            
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print_success(f"Results saved to {output}")
        
    except WeChatAPIError as e:
        print_error(f"API error: {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument('media_ids', nargs=-1, required=True)
@click.option('--delay', '-d', default=0.5, type=float, 
              help='Delay between deletions (seconds)')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def delete(ctx, media_ids: List[str], delay: float, confirm: bool):
    """Delete specific materials by media ID"""
    cleaner = ctx.obj['cleaner']
    
    if not confirm:
        print_warning(f"You are about to delete {len(media_ids)} materials:")
        for media_id in media_ids:
            click.echo(f"  - {media_id}")
        
        if not click.confirm("Are you sure you want to proceed?"):
            click.echo("Operation cancelled")
            return
    
    try:
        print_info(f"Deleting {len(media_ids)} materials...")
        
        results = cleaner.batch_delete_materials(list(media_ids), delay=delay)
        
        print_success(f"Successfully deleted: {results['successful']}")
        if results['failed'] > 0:
            print_error(f"Failed to delete: {results['failed']}")
            
            for error in results['errors']:
                click.echo(f"  - {error['media_id']}: {error['error']}")
        
    except WeChatAPIError as e:
        print_error(f"API error: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option('--type', '-t', default='image', type=click.Choice(['image', 'video', 'voice', 'news']),
              help='Type of materials to clean')
@click.option('--days', '-d', default=30, type=click.IntRange(1),
              help='Delete materials older than this many days')
@click.option('--dry-run', is_flag=True, help='Show what would be deleted without actually deleting')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def clean_old(ctx, type: str, days: int, dry_run: bool, confirm: bool):
    """Clean old materials"""
    cleaner = ctx.obj['cleaner']
    
    try:
        print_info(f"Scanning for {type} materials older than {days} days...")
        
        results = cleaner.clean_old_materials(
            material_type=type,
            days_old=days,
            dry_run=True  # Always do dry run first
        )
        
        if results['would_delete'] == 0:
            print_info("No old materials found to delete")
            return
        
        print_warning(f"Found {results['would_delete']} materials to delete:")
        for media_id in results['materials'][:10]:  # Show first 10
            click.echo(f"  - {media_id}")
        
        if len(results['materials']) > 10:
            click.echo(f"  ... and {len(results['materials']) - 10} more")
        
        if dry_run:
            print_info("Dry run completed - no materials were actually deleted")
            return
        
        if not confirm:
            if not click.confirm(f"Delete {results['would_delete']} materials?"):
                click.echo("Operation cancelled")
                return
        
        # Perform actual deletion
        print_info("Performing actual deletion...")
        results = cleaner.clean_old_materials(
            material_type=type,
            days_old=days,
            dry_run=False
        )
        
        print_success(f"Successfully deleted: {results['successful']}")
        if results['failed'] > 0:
            print_error(f"Failed to delete: {results['failed']}")
        
    except WeChatAPIError as e:
        print_error(f"API error: {str(e)}")
        sys.exit(1)


@cli.command()
@click.pass_context
def test_connection(ctx):
    """Test WeChat API connection"""
    cleaner = ctx.obj['cleaner']
    
    try:
        print_info("Testing WeChat API connection...")
        
        # Test getting access token
        token = cleaner.get_access_token()
        print_success("Successfully obtained access token")
        
        # Test getting material list
        materials, total_count = cleaner.get_material_list(count=1)
        print_success(f"Successfully retrieved material list (Total materials: {total_count})")
        
        print_success("Connection test passed!")
        
    except WeChatAPIError as e:
        print_error(f"Connection test failed: {str(e)}")
        sys.exit(1)


def main():
    """Main entry point"""
    try:
        cli()
    except KeyboardInterrupt:
        print_warning("\nOperation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()