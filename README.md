# 微信公众号素材批量清理工具

这是一个用于微信公众号运营自动化的 Python 脚本，目前支持：

- 批量删除永久图片素材
- 自动发布公众号图文文章（创建草稿并提交发布）

## 功能

- 自动获取并管理 `access_token`。
- 分页获取所有永久图片素材的 `media_id`。
- 批量删除所有获取到的图片素材。
- 根据配置自动创建图文草稿并提交发布。
- 可选轮询发布状态，拿到最终发布结果。
- 将敏感配置（AppID 和 AppSecret）与主逻辑分离，提高安全性。

## 使用方法

1. **克隆仓库**
   ```bash
   git clone https://github.com/hujinbin/wechat_mp_material_cleaner.git
   cd wechat_mp_material_cleaner
   ```

2. **安装依赖**
   ```bash
   pip install aiohttp
   ```

3. **配置 AppID 和 AppSecret**
   - 复制 `config.py.template` 文件并重命名为 `config.py`。
   - 打开 `config.py` 文件，将 `your_appid` 和 `your_appsecret` 替换为你的微信公众号的真实 AppID 和 AppSecret。你可以在微信公众号后台的“设置与开发” -> “基本配置”中找到它们。
   - 如果要发布文章，请继续配置以下字段：
     - `ARTICLE_TITLE`、`ARTICLE_AUTHOR`
     - `ARTICLE_THUMB_MEDIA_ID`（封面图 media_id）
     - `ARTICLE_CONTENT`（HTML正文）或 `ARTICLE_CONTENT_FILE`（本地 UTF-8 文件）
       - 可选：`ARTICLE_THUMB_IMAGE_FILE`（本地封面图路径，脚本会自动上传并使用返回的 media_id）

4. **执行脚本**
      - 列出账号前 20 个图片素材：
         ```bash
         python app.py list-image-media
         ```
    - 清理图片素材（危险操作）：
       ```bash
       python app.py clean-images
       ```
    - 自动发布文章：
       ```bash
       python app.py publish-article
       ```
      - 仅创建草稿（不走发布接口，适合接口权限受限账号）：
         ```bash
         python app.py draft-only
         ```
      - 从 JSON 创建草稿（适合 AI 工作流，例如 OpenClaw）：
         ```bash
         python app.py draft-from-json --json-file article.json
         ```
         - JSON 缺失 `thumb_media_id` 时，脚本会自动交互提问：
            ```bash
            python app.py draft-from-json --json-file article.json
            ```
         - 非交互场景（CI/批处理）可显式传入默认封面：
            ```bash
            python app.py draft-from-json --json-file article.json --thumb-media-id 你的media_id --no-interactive
            ```
         - 从 Markdown 自动转 HTML 并创建草稿：
            ```bash
            python app.py draft-from-markdown --md-file article.md --title "文章标题" --author "作者"
            ```
    - 推荐做法：配置 `ARTICLE_THUMB_IMAGE_FILE="cover.jpg"`，可避免手动找 `media_id`。
    - 提交发布后不等待最终结果：
       ```bash
       python app.py publish-article --no-wait
       ```

## 注意事项

- **请在执行删除操作前务必备份好重要素材！**
- 脚本默认会删除所有图片类永久素材，执行前请三思。
- 微信 API 有调用频率限制，脚本中已加入简单的延时处理，但如果素材量巨大，仍需注意可能遇到的频率问题。
- 自动发布文章依赖公众号接口权限，若返回权限错误，请先确认账号类型和接口授权状态。

## OpenClaw 对接示例

让 OpenClaw 产出 UTF-8 的 `article.json`，然后调用本脚本入草稿箱。

单篇文章 JSON 示例：

```json
{
   "title": "优惠返利写作示例",
   "author": "六言",
   "digest": "一分钟看懂如何领取返利",
   "content": "<p>这里是 AI 生成的 HTML 正文</p>",
   "content_source_url": "",
   "thumb_media_id": "你的封面media_id",
   "need_open_comment": 0,
   "only_fans_can_comment": 0
}
```

执行命令：

```bash
python app.py draft-from-json --json-file article.json
```

## OpenClaw Skill 用法

仓库已提供可直接复用的 Skill：

- `.claude/skills/wechat-mp-material-cleaner/SKILL.md`
- `.claude/skills/wechat-mp-markdown-draft/SKILL.md`

也提供了可直接调用的命令文件：

- `.claude/commands/wechat-draft.md`（在支持 slash command 的环境中可用 `/wechat-draft`）

以及一个可复用 Prompt：

- `.claude/prompts/wechat-draft.prompt.md`
- `.claude/prompts/wechat-draft-batch.prompt.md`（批处理/CI，默认非交互）

推荐触发词示例：

- `请用 wechat-mp-material-cleaner skill 生成公众号草稿 JSON，并保存为 article.json`
- `根据这段内容生成 article.json，然后执行 draft-from-json 入草稿箱`

OpenClaw 执行链路建议：

1. 让模型按 Skill 规则生成 UTF-8 `article.json`。
2. 在仓库根目录执行：
   ```bash
   python app.py draft-from-json --json-file article.json
   ```
3. 查看终端输出中的草稿 `media_id`，并到公众号后台草稿箱确认。

Markdown 链路示例：

1. 保存 `article.md`（UTF-8）。
2. 执行：
   ```bash
   python app.py draft-from-markdown --md-file article.md --title "文章标题" --author "作者"
   ```
3. 如缺失 `thumb_media_id`，脚本会自动提示输入；批处理场景建议加 `--thumb-media-id ... --no-interactive`。

## 许可证

[MIT](LICENSE)
