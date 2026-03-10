---
name: wechat-mp-markdown-draft
description: Use when user provides Markdown content and wants automatic Markdown to HTML conversion, then create WeChat Official Account draft via `python app.py draft-from-markdown`. Keywords: markdown, md, 公众号, 草稿, html.
---

# WeChat MP Markdown Draft Skill

## Purpose
Convert Markdown content to WeChat-compatible HTML and create a draft article in the WeChat Official Account backend.

## Preconditions
- `config.py` has valid `APP_ID` and `APP_SECRET`.
- Markdown file is UTF-8.

## Workflow
1. Save user Markdown as `article.md`.
2. Get metadata: `title`, `author`.
3. If `thumb_media_id` is available, pass it directly.
4. If `thumb_media_id` is missing, run command without it and let script ask interactively.
5. Execute:
   ```bash
   python app.py draft-from-markdown --md-file article.md --title "文章标题" --author "作者"
   ```
6. Return draft result (`media_id`) to user.

## Optional Parameters
- `--thumb-media-id`: Provide known cover media_id.
- `--digest`: Optional summary.
- `--content-source-url`: Optional source URL.
- `--need-open-comment 0|1`
- `--only-fans-can-comment 0|1`
- `--no-interactive`: Disable interactive prompt for missing fields.

## Safety
- Do not call `clean-images` unless the user explicitly requests deletion.
- In non-interactive workflows, require `--thumb-media-id`.
