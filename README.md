# 微信公众号素材批量清理工具

这是一个用于批量删除微信公众号永久素材（目前主要针对图片）的 Python 脚本。

## 功能

- 自动获取并管理 `access_token`。
- 分页获取所有永久图片素材的 `media_id`。
- 批量删除所有获取到的图片素材。
- 将敏感配置（AppID 和 AppSecret）与主逻辑分离，提高安全性。

## 使用方法

1. **克隆仓库**
   ```bash
   git clone https://github.com/hujinbin/wechat_mp_material_cleaner.git
   cd wechat_mp_material_cleaner
   ```

2. **安装依赖**
   ```bash
   pip install requests
   ```

3. **配置 AppID 和 AppSecret**
   - 复制 `config.py.template` 文件并重命名为 `config.py`。
   - 打开 `config.py` 文件，将 `your_appid` 和 `your_appsecret` 替换为你的微信公众号的真实 AppID 和 AppSecret。你可以在微信公众号后台的“设置与开发” -> “基本配置”中找到它们。

4. **执行脚本**
   - 打开 `app.py` 文件。
   - **这是一个非常危险的操作，会删除你公众号所有的永久图片素材，请谨慎操作！**
   - 仔细阅读 `app.py` 文件末尾的说明。如果你确认要删除所有图片，请取消 `clean_all_images(wx)` 这一行的注释。
   - 运行脚本：
     ```bash
     python app.py
     ```

## 注意事项

- **请在执行删除操作前务必备份好重要素材！**
- 脚本默认会删除所有图片类永久素材，执行前请三思。
- 微信 API 有调用频率限制，脚本中已加入简单的延时处理，但如果素材量巨大，仍需注意可能遇到的频率问题。

## 许可证

[MIT](LICENSE)
