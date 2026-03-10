---
mode: ask
description: 根据用户输入生成公众号草稿文件（JSON 或 Markdown），并调用本地命令入草稿箱。
---

# wechat-draft

你正在为当前工作区准备微信公众号草稿。

## 目标
把用户提供的内容整理为可用的草稿输入文件，然后执行本地 CLI 命令写入公众号草稿箱。

## 决策流程
- 如果用户提供的是 Markdown，或明确要求走 Markdown 流程：
  - 以 UTF-8 保存为 `article.md`。
  - 执行：
    ```bash
    python app.py draft-from-markdown --md-file article.md --title "<标题>" --author "<作者>"
    ```
- 否则：
  - 以 UTF-8 保存为 `article.json`。
  - 推荐使用单篇对象结构，字段包括：
    - `title`、`author`、`content`、`digest`、`content_source_url`、`thumb_media_id`、`need_open_comment`、`only_fans_can_comment`
  - 执行：
    ```bash
    python app.py draft-from-json --json-file article.json
    ```

## thumb_media_id 处理
- 如果用户已提供 `thumb_media_id`，直接写入并执行。
- 如果缺失且当前终端可交互，可不传 `--thumb-media-id`，让脚本自动提问。
- 如果是非交互场景，必须带上：
  ```bash
  python app.py draft-from-json --json-file article.json --thumb-media-id "<media_id>" --no-interactive
  ```

## 安全约束
- 除非用户明确要求，否则禁止执行 `clean-images`。
- 文件必须使用 UTF-8 编码。
- 完成后汇总命令输出中的草稿 `media_id`。
