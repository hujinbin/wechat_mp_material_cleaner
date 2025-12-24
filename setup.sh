#!/bin/bash

# WeChat MP Material Cleaner Setup Script
# 微信公众号素材清理工具安装脚本

set -e

echo "=================================================="
echo "WeChat MP Material Cleaner Setup"
echo "微信公众号素材清理工具安装"
echo "=================================================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.7"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✅ Python version $python_version is compatible"
else
    echo "❌ Python $python_version is not compatible. Please use Python 3.7 or higher."
    exit 1
fi

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip3 install --user -r requirements.txt

# Install the package
echo ""
echo "🔧 Installing WeChat MP Material Cleaner..."
pip3 install --user -e .

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "📝 Creating .env configuration file..."
    cp .env.example .env
    echo "✅ Created .env file from template"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file with your WeChat credentials:"
    echo "   - WECHAT_APP_ID=your_app_id_here"
    echo "   - WECHAT_APP_SECRET=your_app_secret_here"
else
    echo ""
    echo "ℹ️  .env file already exists"
fi

# Test installation
echo ""
echo "🧪 Testing installation..."
if command -v wechat-cleaner &> /dev/null; then
    echo "✅ Installation successful!"
    echo ""
    echo "📚 Usage examples:"
    echo "   wechat-cleaner --help"
    echo "   wechat-cleaner test-connection"
    echo "   wechat-cleaner list-materials --type image"
    echo "   wechat-cleaner clean-old --type image --days 30 --dry-run"
else
    echo "❌ Installation failed. wechat-cleaner command not found."
    echo "   You may need to add ~/.local/bin to your PATH"
    echo "   Run: echo 'export PATH=\$HOME/.local/bin:\$PATH' >> ~/.bashrc"
    exit 1
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📖 Next steps:"
echo "1. Edit .env file with your WeChat MP credentials"
echo "2. Run: wechat-cleaner test-connection"
echo "3. Start managing your materials!"
echo ""
echo "For help and documentation:"
echo "- Run: wechat-cleaner --help"
echo "- Check README.md for detailed usage instructions"
echo "- See examples/ directory for code samples"
echo "=================================================="