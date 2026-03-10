---
description: Generate WeChat article JSON or Markdown-based draft input, then run local command to create draft. Supports interactive thumb_media_id fallback when missing.
---

# /wechat-draft

## Usage
Use this command when the user wants to create a WeChat Official Account draft from AI-generated content.

## Steps
1. Determine input type:
- If user provides Markdown, save as `article.md` and use `draft-from-markdown`.
- Otherwise generate `article.json` and use `draft-from-json`.
2. Ensure UTF-8 file encoding.
3. Execute one of the commands below in workspace root.

## Command Options
JSON flow:
```bash
python app.py draft-from-json --json-file article.json
```

Markdown flow:
```bash
python app.py draft-from-markdown --md-file article.md --title "标题" --author "作者"
```

If `thumb_media_id` is known:
```bash
python app.py draft-from-json --json-file article.json --thumb-media-id "你的media_id"
```

Non-interactive mode (CI/batch):
```bash
python app.py draft-from-json --json-file article.json --thumb-media-id "你的media_id" --no-interactive
```
