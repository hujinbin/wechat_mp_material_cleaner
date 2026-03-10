---
name: wechat-mp-material-cleaner
description: Use when you need to generate WeChat Official Account article JSON and save it as a UTF-8 file, then call local script `python app.py draft-from-json --json-file <file>` to create draft in WeChat MP backend. Keywords: WeChat, 公众号, draft, article.json, 草稿, 素材.
---

# WeChat MP Material Cleaner Skill

## Purpose
Use this skill to convert user article intent into valid WeChat draft JSON, write it to a local file, and call the local script to create a draft in the WeChat Official Account backend.

## Project Assumptions
- Workspace root contains `app.py`.
- `config.py` has valid `APP_ID` and `APP_SECRET`.
- Python dependencies are installed (`aiohttp`).

## JSON Requirements
Create UTF-8 JSON in one of these forms:
- Single article object.
- Object with `articles` array.

Required fields for each article:
- `title`
- `author`
- `content`

`thumb_media_id` behavior:
- Recommended to provide explicitly.
- If missing, script can ask interactively during `draft-from-json`.
- For non-interactive runs, pass `--thumb-media-id`.

Optional fields:
- `digest`
- `content_source_url`
- `need_open_comment` (`0` or `1`)
- `only_fans_can_comment` (`0` or `1`)

## Workflow
1. Confirm article intent from user prompt.
2. Generate clean HTML for `content`.
3. Save UTF-8 JSON file, default name `article.json` in workspace root.
4. Run:
   ```bash
   python app.py draft-from-json --json-file article.json
   ```
  Or for batch mode:
  ```bash
  python app.py draft-from-json --json-file article.json --thumb-media-id "你的media_id" --no-interactive
  ```
5. Return command result summary to user.

## Safety Checks
- Never run `clean-images` unless the user explicitly asks for deletion.
- If `thumb_media_id` is missing, prefer interactive prompt or provide `--thumb-media-id`.
- Keep JSON UTF-8 and avoid escape-only Unicode text.

## JSON Template
```json
{
  "title": "文章标题",
  "author": "作者",
  "digest": "摘要（可选）",
  "content": "<p>HTML 正文</p>",
  "content_source_url": "",
  "thumb_media_id": "请填写已有封面media_id",
  "need_open_comment": 0,
  "only_fans_can_comment": 0
}
```

## Multi-Article Template
```json
{
  "articles": [
    {
      "title": "第一篇",
      "author": "作者",
      "content": "<p>正文1</p>",
      "thumb_media_id": "media_id_1"
    },
    {
      "title": "第二篇",
      "author": "作者",
      "content": "<p>正文2</p>",
      "thumb_media_id": "media_id_2"
    }
  ]
}
```
