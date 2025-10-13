# WeChat MP Material Cleaner
微信公众号图片素材批量删除工具

![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A powerful command-line tool for batch managing and cleaning WeChat MP (微信公众号) materials including images, videos, voice files, and news articles.

一个强大的命令行工具，用于批量管理和清理微信公众号素材，包括图片、视频、语音文件和图文消息。

## Features 功能特性

- ✅ **Batch Material Deletion** - Delete multiple materials at once / 批量删除素材
- ✅ **Material Type Support** - Support images, videos, voice, news / 支持图片、视频、语音、图文消息
- ✅ **Smart Time-based Cleaning** - Clean materials older than specified days / 智能时间筛选清理
- ✅ **Dry Run Mode** - Preview what will be deleted before actual deletion / 预览模式
- ✅ **Progress Tracking** - Real-time progress feedback / 实时进度反馈
- ✅ **Error Handling** - Robust error handling and retry mechanism / 强大的错误处理和重试机制
- ✅ **Configuration Management** - Flexible configuration options / 灵活的配置选项

## Installation 安装

### Prerequisites 先决条件

- Python 3.7+
- WeChat MP developer account with API access / 微信公众号开发者账号

### Install from source 从源码安装

```bash
# Clone the repository / 克隆仓库
git clone https://github.com/hujinbin/wechat_mp_material_cleaner.git
cd wechat_mp_material_cleaner

# Install dependencies / 安装依赖
pip install -r requirements.txt

# Install the package / 安装包
pip install -e .
```

## Configuration 配置

### 1. Create configuration file 创建配置文件

Copy the example configuration file and edit it with your credentials:
复制示例配置文件并编辑您的凭据：

```bash
cp .env.example .env
```

### 2. Edit .env file 编辑 .env 文件

```env
# Required / 必需
WECHAT_APP_ID=your_wechat_app_id_here
WECHAT_APP_SECRET=your_wechat_app_secret_here

# Optional / 可选
WECHAT_API_TIMEOUT=30
WECHAT_RETRY_TIMES=3
WECHAT_RETRY_DELAY=1
```

### 3. Get WeChat MP credentials 获取微信公众号凭据

1. Login to WeChat MP admin panel / 登录微信公众号管理后台
2. Go to "开发" -> "基本配置" (Development -> Basic Configuration)
3. Find your AppID and AppSecret / 找到您的 AppID 和 AppSecret
4. Add your server IP to the whitelist / 将您的服务器IP添加到白名单

## Usage 使用方法

### Test connection 测试连接

```bash
wechat-cleaner test-connection
```

### List materials 列出素材

```bash
# List first 20 images / 列出前20个图片素材
wechat-cleaner list-materials --type image

# List videos with pagination / 分页列出视频素材
wechat-cleaner list-materials --type video --count 10 --offset 20

# Save results to file / 保存结果到文件
wechat-cleaner list-materials --type image --output materials.json
```

### Delete specific materials 删除指定素材

```bash
# Delete single material / 删除单个素材
wechat-cleaner delete MEDIA_ID_HERE

# Delete multiple materials / 删除多个素材
wechat-cleaner delete MEDIA_ID_1 MEDIA_ID_2 MEDIA_ID_3

# Skip confirmation / 跳过确认
wechat-cleaner delete MEDIA_ID_HERE --confirm

# Add delay between deletions / 添加删除间隔
wechat-cleaner delete MEDIA_ID_HERE --delay 1.0
```

### Clean old materials 清理旧素材

```bash
# Dry run - see what would be deleted / 预览模式 - 查看将要删除的内容
wechat-cleaner clean-old --type image --days 30 --dry-run

# Actually delete materials older than 30 days / 实际删除30天前的素材
wechat-cleaner clean-old --type image --days 30

# Clean all types of materials / 清理所有类型的素材
wechat-cleaner clean-old --type video --days 60
wechat-cleaner clean-old --type voice --days 90
wechat-cleaner clean-old --type news --days 180
```

### Command options 命令选项

#### Global options 全局选项

- `--config, -c`: Path to configuration file / 配置文件路径
- `--verbose, -v`: Enable verbose logging / 启用详细日志

#### Material types 素材类型

- `image`: Images / 图片
- `video`: Videos / 视频
- `voice`: Voice files / 语音文件
- `news`: News articles / 图文消息

## Examples 示例

### Example 1: Regular cleanup routine 定期清理例程

```bash
#!/bin/bash
# Weekly cleanup script / 每周清理脚本

echo "Starting WeChat MP material cleanup..."

# Clean images older than 60 days / 清理60天前的图片
wechat-cleaner clean-old --type image --days 60 --confirm

# Clean videos older than 90 days / 清理90天前的视频
wechat-cleaner clean-old --type video --days 90 --confirm

# Clean voice files older than 120 days / 清理120天前的语音文件
wechat-cleaner clean-old --type voice --days 120 --confirm

echo "Cleanup completed!"
```

### Example 2: Backup before deletion 删除前备份

```bash
# List and backup materials before deletion / 删除前列出和备份素材
wechat-cleaner list-materials --type image --output backup_$(date +%Y%m%d).json

# Review the backup file / 查看备份文件
cat backup_$(date +%Y%m%d).json

# Perform cleanup / 执行清理
wechat-cleaner clean-old --type image --days 30
```

## API Rate Limiting API速率限制

WeChat MP API has rate limiting. This tool includes:
微信公众号 API 有速率限制。本工具包含：

- Automatic retry with exponential backoff / 指数退避自动重试
- Configurable delays between requests / 可配置的请求间隔
- Access token caching / 访问令牌缓存

## Troubleshooting 故障排除

### Common issues 常见问题

1. **Access token error / 访问令牌错误**
   ```
   Solution: Check your AppID and AppSecret in .env file
   解决方案：检查 .env 文件中的 AppID 和 AppSecret
   ```

2. **IP not in whitelist / IP不在白名单中**
   ```
   Solution: Add your server IP to WeChat MP whitelist
   解决方案：将您的服务器IP添加到微信公众号白名单
   ```

3. **Rate limiting / 速率限制**
   ```
   Solution: Increase delay between requests using --delay option
   解决方案：使用 --delay 选项增加请求间隔
   ```

### Enable debug logging 启用调试日志

```bash
wechat-cleaner --verbose list-materials --type image
```

## Safety Features 安全特性

- **Dry run mode** - Preview operations before execution / 预览模式 - 执行前预览操作
- **Confirmation prompts** - Require user confirmation for destructive operations / 确认提示 - 危险操作需要用户确认
- **Progress tracking** - Real-time feedback on operations / 进度跟踪 - 操作的实时反馈
- **Error recovery** - Automatic retry on network failures / 错误恢复 - 网络故障自动重试

## Contributing 贡献

Contributions are welcome! Please feel free to submit a Pull Request.
欢迎贡献！请随时提交 Pull Request。

## License 许可证

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## Disclaimer 免责声明

This tool is for educational and legitimate use only. Users are responsible for complying with WeChat's Terms of Service and applicable laws.
本工具仅用于教育和合法用途。用户有责任遵守微信服务条款和适用法律。
