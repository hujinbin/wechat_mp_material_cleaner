---
mode: ask
description: 批处理版公众号草稿入库流程，默认非交互，强制要求 --thumb-media-id。
---

# wechat-draft-batch

你正在执行批处理模式的公众号草稿创建流程。

## 目标
在非交互环境中，把用户内容转成草稿文件并提交到公众号草稿箱。

## 强制规则
- 必须使用非交互参数：`--no-interactive`。
- 必须提供封面：`--thumb-media-id`。
- 如果用户未提供 `thumb_media_id`，先向用户索取，再继续执行。

## 输入分支
- Markdown 分支：
  - 生成 UTF-8 `article.md`。
  - 执行：
    ```bash
    python app.py draft-from-markdown --md-file article.md --title "<标题>" --author "<作者>" --thumb-media-id "<media_id>" --no-interactive
    ```
- JSON 分支：
  - 生成 UTF-8 `article.json`。
  - 执行：
    ```bash
    python app.py draft-from-json --json-file article.json --thumb-media-id "<media_id>" --no-interactive
    ```

## 输出要求
- 回传使用的命令。
- 回传命令输出中的草稿 `media_id`。
- 若失败，回传错误原因和可操作修复建议。

## 安全约束
- 除非用户明确要求，否则禁止执行 `clean-images`。
