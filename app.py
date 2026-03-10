import asyncio
import aiohttp
import argparse
import html
import json
import re
import sys
import time
from pathlib import Path

import config as cfg

APP_ID = cfg.APP_ID
APP_SECRET = cfg.APP_SECRET

UNICODE_ESCAPE_PATTERN = re.compile(r"(\\u[0-9a-fA-F]{4}|\\U[0-9a-fA-F]{8}|\\x[0-9a-fA-F]{2})")

class WxManager:
    """
    微信公众号素材管理器 (异步 aiohttp 版本)
    """
    def __init__(self, appid, appsecret):
        self.appid = appid
        self.appsecret = appsecret
        self._session = None
        self.token = None
        self.token_expires_at = 0
        self._token_lock = asyncio.Lock()

    async def get_session(self):
        """获取 aiohttp session"""
        if self._session is None or self._session.closed:
            # 创建一个TCP连接器，限制并发连接数为100
            connector = aiohttp.TCPConnector(limit=100)
            self._session = aiohttp.ClientSession(connector=connector)
        return self._session

    async def close_session(self):
        """关闭 aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _get_access_token(self):
        """
        获取或刷新 access_token，带异步锁确保并发安全。
        """
        async with self._token_lock:
            if self.token and self.token_expires_at > time.time():
                return self.token

            session = await self.get_session()
            url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.appid}&secret={self.appsecret}"
            
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json(content_type=None)
                    if "access_token" in data:
                        self.token = data["access_token"]
                        # 微信的token有效期为7200秒，这里设置一个10分钟的缓冲时间
                        self.token_expires_at = time.time() + data["expires_in"] - 600
                        print("获取 access_token 成功")
                        return self.token
                    else:
                        raise Exception(f"获取 access_token 失败: {data.get('errmsg', '未知错误')}")
            except aiohttp.ClientError as e:
                raise Exception(f"请求 access_token 时网络错误: {e}")

    async def get_permanent_materials(self, material_type="image", offset=0, count=20):
        """异步获取永久素材列表"""
        token = await self._get_access_token()
        session = await self.get_session()
        url = f"https://api.weixin.qq.com/cgi-bin/material/batchget_material?access_token={token}"
        payload = {
            "type": material_type,
            "offset": offset,
            "count": count
        }
        
        try:
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                result = await response.json(content_type=None)
                if "item" in result:
                    return result
                else:
                    print(f"获取素材列表失败: {result.get('errmsg', '未知错误')}")
                    return None
        except aiohttp.ClientError as e:
            print(f"获取素材列表时网络错误: {e}")
            return None

    async def _post_json(self, url, payload):
        """发送 POST JSON 请求并返回 JSON 数据。"""
        session = await self.get_session()
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json; charset=utf-8"}
        async with session.post(url, data=body, headers=headers) as response:
            response.raise_for_status()
            return await response.json(content_type=None)

    async def add_draft(self, articles):
        """创建图文草稿，返回草稿 media_id。"""
        token = await self._get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
        payload = {"articles": articles}

        try:
            result = await self._post_json(url, payload)
        except aiohttp.ClientError as e:
            raise Exception(f"创建草稿时网络错误: {e}")

        if "media_id" in result:
            print(f"创建草稿成功，media_id: {result['media_id']}")
            return result["media_id"]

        raise Exception(f"创建草稿失败: {result.get('errmsg', '未知错误')}")

    async def upload_permanent_image(self, image_path):
        """上传永久图片素材，返回 media_id。"""
        path = Path(image_path).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"封面图片不存在: {path}")

        token = await self._get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"

        data = aiohttp.FormData()
        with path.open("rb") as fp:
            data.add_field("media", fp, filename=path.name, content_type="application/octet-stream")
            session = await self.get_session()
            try:
                async with session.post(url, data=data) as response:
                    response.raise_for_status()
                    result = await response.json(content_type=None)
            except aiohttp.ClientError as e:
                raise Exception(f"上传封面图片时网络错误: {e}")

        media_id = result.get("media_id")
        if media_id:
            print(f"封面图片上传成功，media_id: {media_id}")
            return media_id

        raise Exception(f"上传封面图片失败: {result.get('errmsg', '未知错误')}")

    async def get_first_image_media_id(self):
        """获取素材库第一张永久图片的 media_id。"""
        token = await self._get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/material/batchget_material?access_token={token}"
        payload = {"type": "image", "offset": 0, "count": 1}

        try:
            result = await self._post_json(url, payload)
        except aiohttp.ClientError as e:
            raise Exception(f"查询图片素材时网络错误: {e}")

        items = result.get("item", [])
        if items:
            media_id = items[0].get("media_id", "")
            if media_id:
                print(f"已自动选取素材库第一张图片 media_id: {media_id}")
                return media_id

        return ""

    async def publish_draft(self, media_id):
        """提交草稿发布，返回 publish_id。"""
        token = await self._get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={token}"
        payload = {"media_id": media_id}

        try:
            result = await self._post_json(url, payload)
        except aiohttp.ClientError as e:
            raise Exception(f"提交发布时网络错误: {e}")

        if "publish_id" in result:
            print(f"已提交发布，publish_id: {result['publish_id']}")
            return result["publish_id"]

        raise Exception(f"提交发布失败: {result.get('errmsg', '未知错误')}")

    async def get_publish_status(self, publish_id):
        """查询发布状态。"""
        token = await self._get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/freepublish/get?access_token={token}"
        payload = {"publish_id": publish_id}

        try:
            result = await self._post_json(url, payload)
            return result
        except aiohttp.ClientError as e:
            raise Exception(f"查询发布状态时网络错误: {e}")

    async def wait_for_publish_result(self, publish_id, poll_interval=5, timeout=180):
        """轮询发布状态，直到成功/失败或超时。"""
        in_progress_status = {1}
        success_status = {0}

        start = time.time()
        while True:
            result = await self.get_publish_status(publish_id)
            status = result.get("publish_status")

            if status in success_status:
                article_id = result.get("article_id", "")
                article_detail = result.get("article_detail", {})
                article_url = ""
                if isinstance(article_detail, dict):
                    article_url = article_detail.get("article_url", "")
                print(f"发布成功，article_id: {article_id}")
                if article_url:
                    print(f"文章链接: {article_url}")
                return result

            if status not in in_progress_status:
                raise Exception(f"发布失败或状态异常: {result}")

            if time.time() - start > timeout:
                raise TimeoutError(
                    f"等待发布结果超时（>{timeout}秒），请稍后在公众号后台确认，publish_id={publish_id}"
                )

            print(f"发布处理中，当前状态: {status}，{poll_interval} 秒后重试...")
            await asyncio.sleep(poll_interval)

    async def _delete_single_material(self, session, token, media_id):
        """异步删除单个素材的内部方法"""
        url = f"https://api.weixin.qq.com/cgi-bin/material/del_material?access_token={token}"
        payload = {"media_id": media_id}
        try:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json(content_type=None)
                    if data.get("errcode") == 0:
                        # print(f"删除成功: {media_id}")
                        return True
                    else:
                        print(f"删除失败: {media_id}, 原因: {data.get('errmsg', '未知错误')}")
                        return False
                else:
                    print(f"删除请求失败: {media_id}, 状态码: {response.status}")
                    return False
        except aiohttp.ClientError as e:
            print(f"删除请求网络错误: {media_id}, 错误: {e}")
            return False

    async def delete_materials(self, media_ids):
        """使用 asyncio.gather 并发删除多个永久素材"""
        if not media_ids:
            print("没有需要删除的素材ID")
            return
        
        token = await self._get_access_token()
        session = await self.get_session()
        
        tasks = [self._delete_single_material(session, token, media_id) for media_id in media_ids]
        results = await asyncio.gather(*tasks)
        
        deleted_count = sum(1 for r in results if r)
        failed_count = len(results) - deleted_count
        print(f"本批删除完成: 成功 {deleted_count} 个, 失败 {failed_count} 个")
        
        return deleted_count, failed_count


async def clean_all_images(wx_manager):
    """异步清理所有永久图片素材"""
    # 记录无法删除的图片ID（通常是被自动回复或菜单使用的）
    undeletable_ids = set()
    
    # 设置最大重试次数，避免无限循环
    max_attempts = 5
    attempts = 0
    
    while attempts < max_attempts:
        attempts += 1
        current_offset = 0
        page_size = 20  # 微信API限制每次最多获取20个
        empty_pages_count = 0  # 记录连续遇到的空页面数
        
        print(f"\n第 {attempts} 轮扫描 - 开始清理图片素材...")
        
        # 先获取当前总数
        initial_data = await wx_manager.get_permanent_materials(material_type="image", offset=0, count=1)
        if not initial_data:
            print("无法获取素材列表，脚本终止。")
            break
            
        total_count = initial_data.get("total_count", 0)
        if total_count == 0:
            print("没有图片素材需要清理，任务完成。")
            break
            
        print(f"检测到总共有 {total_count} 个图片素材。")
        
        # 记录本轮删除的统计信息
        round_deleted = 0
        round_failed = 0
        
        # 开始逐页处理
        while current_offset < total_count and empty_pages_count < 3:
            materials_data = await wx_manager.get_permanent_materials(material_type="image", offset=current_offset, count=page_size)
            
            if not materials_data:
                print(f"获取偏移量 {current_offset} 处的素材失败，尝试下一页。")
                current_offset += page_size
                continue
            
            items = materials_data.get("item", [])
            if not items:
                empty_pages_count += 1
                print(f"偏移量 {current_offset} 处没有素材，连续空页面数: {empty_pages_count}")
                current_offset += page_size
                
                # 如果连续3页都是空的，可能是微信API返回的总数不准确，提前结束本轮扫描
                if empty_pages_count >= 3:
                    print("连续多页没有获取到素材，本轮扫描结束。")
                    break
                    
                continue
            
            # 重置空页面计数
            empty_pages_count = 0
            
            # 过滤掉已知无法删除的ID
            media_ids_to_delete = [item['media_id'] for item in items if item['media_id'] not in undeletable_ids]
            
            if media_ids_to_delete:
                print(f"正在删除 {len(media_ids_to_delete)} 个图片素材 (本轮进度: {current_offset + len(items)} / {total_count})...")
                
                # 调用删除方法
                session = await wx_manager.get_session()
                token = await wx_manager._get_access_token()
                
                results = []
                for media_id in media_ids_to_delete:
                    success = await wx_manager._delete_single_material(session, token, media_id)
                    results.append(success)
                    
                    if not success:
                        # 记录无法删除的ID，避免后续重复尝试
                        undeletable_ids.add(media_id)
                
                # 统计本批次结果
                deleted_count = sum(1 for r in results if r)
                failed_count = len(results) - deleted_count
                
                round_deleted += deleted_count
                round_failed += failed_count
                
                print(f"本批删除完成: 成功 {deleted_count} 个, 失败 {failed_count} 个")
                
                # 短暂暂停，避免API调用过于频繁
                await asyncio.sleep(0.5)
            else:
                print(f"偏移量 {current_offset} 处的 {len(items)} 个素材都无法删除，跳过。")
            
            current_offset += len(items)
        
        # 本轮扫描结束，显示统计信息
        print(f"\n第 {attempts} 轮扫描结束 - 成功删除: {round_deleted} 个, 失败: {round_failed} 个")
        
        # 再次检查剩余数量
        check_data = await wx_manager.get_permanent_materials(material_type="image", offset=0, count=1)
        if not check_data:
            print("无法检查剩余素材数量。")
            break
            
        remaining = check_data.get("total_count", 0)
        
        # 如果剩余素材等于无法删除的ID数量，则任务完成
        if remaining <= len(undeletable_ids):
            print(f"\n清理完成! 共有 {len(undeletable_ids)} 个素材无法删除，原因是它们正在被自动回复或菜单使用。")
            if undeletable_ids:
                print("无法删除的素材ID:")
                for id in undeletable_ids:
                    print(f"  - {id}")
                print("\n如需删除这些素材，请先在公众号后台检查并移除对应的自动回复规则或菜单设置。")
            break
        
        print(f"还剩 {remaining} 个素材未处理，继续下一轮扫描...")
    
    if attempts >= max_attempts:
        print(f"\n达到最大尝试次数 ({max_attempts} 次)，停止清理。")
        print(f"仍有 {total_count - len(undeletable_ids)} 个素材可能未被处理。")
    
    print("\n所有可删除的图片素材清理完毕。")


def _load_article_content_from_file(content_file):
    """从本地文件读取文章正文。"""
    path = Path(content_file).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"未找到正文文件: {path}")
    return path.read_text(encoding="utf-8")


def _utf8_truncate(text, max_bytes):
    """按 UTF-8 字节数截断字符串，避免多字节字符被截断。"""
    if text is None:
        return ""
    raw = str(text).encode("utf-8")
    if len(raw) <= max_bytes:
        return str(text)
    truncated = raw[:max_bytes]
    while True:
        try:
            return truncated.decode("utf-8")
        except UnicodeDecodeError:
            truncated = truncated[:-1]


def _decode_escaped_unicode(text):
    """把类似 '\\u4f60\\u597d' 的转义文本还原为可读中文。"""
    if text is None:
        return ""

    value = str(text)
    if not UNICODE_ESCAPE_PATTERN.search(value):
        return value

    try:
        decoded = bytes(value, "utf-8").decode("unicode_escape")
        return decoded
    except Exception:
        return value


def _normalize_article_fields(article):
    """对文章字段做微信接口友好的长度处理。"""
    for field in ("title", "author", "digest", "content"):
        original = article.get(field, "")
        normalized = _decode_escaped_unicode(original)
        if normalized != original:
            print(f"检测到 {field} 含有转义字符，已自动还原。")
            article[field] = normalized

    # 微信草稿接口对 author 字段长度较敏感，按 8 字节保守处理。
    author = article.get("author", "")
    normalized_author = _utf8_truncate(author, 8)
    if normalized_author != author:
        print(f"作者名过长，已自动截断: '{author}' -> '{normalized_author}'")
        article["author"] = normalized_author
    return article


def _supports_interactive_input():
    """判断当前运行环境是否支持交互输入。"""
    return sys.stdin.isatty() and sys.stdout.isatty()


def _is_missing_thumb_media_id(value):
    """判断封面 media_id 是否为空或占位值。"""
    return _is_placeholder_media_id(value)


def _prompt_thumb_media_id(article_index=1):
    """交互式询问封面 media_id。"""
    if not _supports_interactive_input():
        raise ValueError(
            "检测到文章缺少 thumb_media_id，且当前是非交互环境。"
            "请在 JSON 中补充 thumb_media_id，或使用 --thumb-media-id 传入默认值。"
        )

    while True:
        user_input = input(f"文章 #{article_index} 缺少 thumb_media_id，请输入可用 media_id: ").strip()
        if user_input and not _is_placeholder_media_id(user_input):
            return user_input
        print("输入无效，请重新输入有效的 media_id。")


def _ensure_thumb_media_ids(articles, default_thumb_media_id="", interactive=True):
    """确保每篇文章都有可用的 thumb_media_id。"""
    default_value = (default_thumb_media_id or "").strip()
    has_default = bool(default_value) and not _is_placeholder_media_id(default_value)

    for idx, article in enumerate(articles, start=1):
        thumb_media_id = (article.get("thumb_media_id") or "").strip()
        if not _is_missing_thumb_media_id(thumb_media_id):
            article["thumb_media_id"] = thumb_media_id
            continue

        if has_default:
            article["thumb_media_id"] = default_value
            print(f"文章 #{idx} 缺少 thumb_media_id，已使用命令行默认值。")
            continue

        if interactive:
            article["thumb_media_id"] = _prompt_thumb_media_id(article_index=idx)
            continue

        raise ValueError(
            f"文章 #{idx} 缺少 thumb_media_id。"
            "请在 JSON 中补充，或使用 --thumb-media-id，或移除 --no-interactive。"
        )

    return articles


def _render_markdown_inline(text):
    """渲染少量常见 Markdown 行内语法。"""
    escaped = html.escape(text.strip())
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)
    escaped = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>',
        escaped,
    )
    return escaped


def _basic_markdown_to_html(markdown_text):
    """无第三方依赖时的基础 Markdown 转 HTML。"""
    lines = markdown_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks = []
    paragraph_lines = []
    in_list = False

    def flush_paragraph():
        nonlocal paragraph_lines
        if paragraph_lines:
            paragraph = " ".join(_render_markdown_inline(line) for line in paragraph_lines if line.strip())
            if paragraph:
                blocks.append(f"<p>{paragraph}</p>")
            paragraph_lines = []

    def close_list():
        nonlocal in_list
        if in_list:
            blocks.append("</ul>")
            in_list = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            close_list()
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading_match:
            flush_paragraph()
            close_list()
            level = len(heading_match.group(1))
            content = _render_markdown_inline(heading_match.group(2))
            blocks.append(f"<h{level}>{content}</h{level}>")
            continue

        list_match = re.match(r"^[-*+]\s+(.+)$", stripped)
        if list_match:
            flush_paragraph()
            if not in_list:
                blocks.append("<ul>")
                in_list = True
            item = _render_markdown_inline(list_match.group(1))
            blocks.append(f"<li>{item}</li>")
            continue

        close_list()
        paragraph_lines.append(stripped)

    flush_paragraph()
    close_list()
    return "\n".join(blocks)


def markdown_to_html(markdown_text):
    """Markdown 转 HTML。优先使用 markdown 库，缺失时回退到内置转换器。"""
    try:
        import markdown as markdown_lib  # type: ignore

        return markdown_lib.markdown(
            markdown_text,
            extensions=["extra", "tables", "sane_lists"],
            output_format="xhtml",
        )
    except Exception:
        return _basic_markdown_to_html(markdown_text)


def build_article_from_config():
    """从 config.py 读取文章配置并构造微信文章对象。"""
    content = getattr(cfg, "ARTICLE_CONTENT", "")
    content_file = getattr(cfg, "ARTICLE_CONTENT_FILE", "")
    if content_file:
        content = _load_article_content_from_file(content_file)

    article = {
        "title": getattr(cfg, "ARTICLE_TITLE", ""),
        "author": getattr(cfg, "ARTICLE_AUTHOR", ""),
        "digest": getattr(cfg, "ARTICLE_DIGEST", ""),
        "content": content,
        "content_source_url": getattr(cfg, "ARTICLE_SOURCE_URL", ""),
        "thumb_media_id": getattr(cfg, "ARTICLE_THUMB_MEDIA_ID", ""),
        "need_open_comment": int(getattr(cfg, "ARTICLE_NEED_OPEN_COMMENT", 0)),
        "only_fans_can_comment": int(getattr(cfg, "ARTICLE_ONLY_FANS_CAN_COMMENT", 0)),
    }

    return prepare_article(article)


def build_article_from_markdown(
    markdown_file,
    title,
    author,
    thumb_media_id="",
    digest="",
    content_source_url="",
    need_open_comment=0,
    only_fans_can_comment=0,
):
    """从 Markdown 文件构造单篇草稿文章。"""
    md_path = Path(markdown_file).expanduser()
    if not md_path.exists():
        raise FileNotFoundError(f"Markdown 文件不存在: {md_path}")

    markdown_content = md_path.read_text(encoding="utf-8")
    html_content = markdown_to_html(markdown_content)

    article = {
        "title": title,
        "author": author,
        "digest": digest,
        "content": html_content,
        "content_source_url": content_source_url,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": int(need_open_comment),
        "only_fans_can_comment": int(only_fans_can_comment),
    }
    return prepare_article(article, require_thumb_media_id=False)


def prepare_article(article, require_thumb_media_id=True):
    """标准化并校验单篇文章对象。"""
    required_fields = ["title", "author", "content"]
    if require_thumb_media_id:
        required_fields.append("thumb_media_id")
    missing_fields = [field for field in required_fields if not article.get(field)]
    if missing_fields:
        missing_str = ", ".join(missing_fields)
        raise ValueError(f"文章配置不完整，缺少字段: {missing_str}")

    article.setdefault("digest", "")
    article.setdefault("content_source_url", "")
    article.setdefault("thumb_media_id", "")
    article.setdefault("need_open_comment", 0)
    article.setdefault("only_fans_can_comment", 0)

    article["need_open_comment"] = int(article.get("need_open_comment", 0))
    article["only_fans_can_comment"] = int(article.get("only_fans_can_comment", 0))

    return _normalize_article_fields(article)


def load_articles_from_json(json_file):
    """从 UTF-8 JSON 文件加载文章。支持单篇或 articles 列表。"""
    path = Path(json_file).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"JSON 文件不存在: {path}")

    raw = path.read_text(encoding="utf-8")
    payload = json.loads(raw)

    if isinstance(payload, dict) and "articles" in payload:
        articles = payload["articles"]
    elif isinstance(payload, dict):
        articles = [payload]
    elif isinstance(payload, list):
        articles = payload
    else:
        raise ValueError("JSON 格式错误，必须是对象、数组，或包含 articles 字段的对象。")

    if not articles:
        raise ValueError("JSON 中没有可用文章。")

    return [prepare_article(article, require_thumb_media_id=False) for article in articles]


def _is_placeholder_media_id(value):
    """判断是否是占位封面 media_id。"""
    v = (value or "").strip().lower()
    return v in {"", "your_thumb_media_id", "media_id", "your_media_id"}


def _looks_like_media_id(value):
    """粗略判断字符串是否像微信公众号素材 media_id。"""
    v = (value or "").strip()
    return len(v) > 20 and all(ch not in v for ch in ("\\", "/", ".jpg", ".jpeg", ".png", ".gif"))


async def resolve_thumb_media_id(wx_manager):
    """解析并返回可用的封面 media_id。"""
    configured_media_id = getattr(cfg, "ARTICLE_THUMB_MEDIA_ID", "")
    cover_file = getattr(cfg, "ARTICLE_THUMB_IMAGE_FILE", "")

    if cover_file:
        cover_path = Path(cover_file).expanduser()
        if cover_path.exists():
            print(f"检测到本地封面图配置，准备上传: {cover_file}")
            return await wx_manager.upload_permanent_image(cover_file)

        if _looks_like_media_id(cover_file):
            print("检测到 ARTICLE_THUMB_IMAGE_FILE 传入了 media_id，已直接作为封面 media_id 使用。")
            return cover_file

        raise FileNotFoundError(
            f"ARTICLE_THUMB_IMAGE_FILE 指向的文件不存在: {cover_file}。"
            "请填写本地图片路径，或改为 ARTICLE_THUMB_MEDIA_ID。"
        )

    if not _is_placeholder_media_id(configured_media_id):
        return configured_media_id

    media_id = await wx_manager.get_first_image_media_id()
    if media_id:
        print("检测到占位 media_id，已自动使用素材库中的可用 media_id。")
        return media_id

    raise ValueError(
        "未找到可用封面 media_id。请在 config.py 中设置 ARTICLE_THUMB_MEDIA_ID，"
        "或配置 ARTICLE_THUMB_IMAGE_FILE 指向本地封面图。"
    )


async def auto_publish_article(wx_manager, wait_result=True, poll_interval=5, timeout=180):
    """自动发布单篇公众号文章。"""
    article = build_article_from_config()
    article["thumb_media_id"] = await resolve_thumb_media_id(wx_manager)
    draft_media_id = await wx_manager.add_draft([article])
    publish_id = await wx_manager.publish_draft(draft_media_id)

    if wait_result:
        await wx_manager.wait_for_publish_result(
            publish_id=publish_id,
            poll_interval=poll_interval,
            timeout=timeout,
        )
    else:
        print("未等待最终发布结果，可稍后在公众号后台查看发布状态。")


async def create_draft_only(wx_manager):
    """仅创建草稿，不调用发布接口。"""
    article = build_article_from_config()
    article["thumb_media_id"] = await resolve_thumb_media_id(wx_manager)
    draft_media_id = await wx_manager.add_draft([article])
    print(f"草稿创建完成，可在公众号后台草稿箱查看。media_id: {draft_media_id}")


async def create_draft_from_json(wx_manager, json_file, default_thumb_media_id="", interactive=True):
    """从 JSON 文件创建草稿，不调用发布接口。"""
    articles = load_articles_from_json(json_file)
    articles = _ensure_thumb_media_ids(
        articles,
        default_thumb_media_id=default_thumb_media_id,
        interactive=interactive,
    )
    draft_media_id = await wx_manager.add_draft(articles)
    print(f"草稿创建完成（来源 JSON），media_id: {draft_media_id}")


async def create_draft_from_markdown(
    wx_manager,
    markdown_file,
    title,
    author,
    thumb_media_id="",
    digest="",
    content_source_url="",
    need_open_comment=0,
    only_fans_can_comment=0,
    interactive=True,
):
    """从 Markdown 文件创建草稿，不调用发布接口。"""
    article = build_article_from_markdown(
        markdown_file=markdown_file,
        title=title,
        author=author,
        thumb_media_id=thumb_media_id,
        digest=digest,
        content_source_url=content_source_url,
        need_open_comment=need_open_comment,
        only_fans_can_comment=only_fans_can_comment,
    )
    articles = _ensure_thumb_media_ids(
        [article],
        default_thumb_media_id=thumb_media_id,
        interactive=interactive,
    )
    draft_media_id = await wx_manager.add_draft(articles)
    print(f"草稿创建完成（来源 Markdown），media_id: {draft_media_id}")


def parse_args():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="微信公众号素材清理与图文发布工具")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("clean-images", help="清理所有可删除的永久图片素材")
    subparsers.add_parser("list-image-media", help="列出账号前20个永久图片素材")
    subparsers.add_parser("draft-only", help="仅创建草稿，不调用发布接口")
    json_parser = subparsers.add_parser("draft-from-json", help="从 UTF-8 JSON 创建草稿，不调用发布接口")
    json_parser.add_argument("--json-file", required=True, help="文章 JSON 文件路径")
    json_parser.add_argument("--thumb-media-id", default="", help="为缺失封面的文章提供默认 thumb_media_id")
    json_parser.add_argument("--no-interactive", action="store_true", help="禁用缺失字段时的交互提问")

    md_parser = subparsers.add_parser("draft-from-markdown", help="从 Markdown 自动转 HTML 并创建草稿")
    md_parser.add_argument("--md-file", required=True, help="Markdown 文件路径（UTF-8）")
    md_parser.add_argument("--title", required=True, help="文章标题")
    md_parser.add_argument("--author", required=True, help="作者")
    md_parser.add_argument("--thumb-media-id", default="", help="封面 thumb_media_id（缺失时可交互输入）")
    md_parser.add_argument("--digest", default="", help="文章摘要")
    md_parser.add_argument("--content-source-url", default="", help="原文链接")
    md_parser.add_argument("--need-open-comment", type=int, default=0, help="评论设置: 0 关闭, 1 开启")
    md_parser.add_argument("--only-fans-can-comment", type=int, default=0, help="仅粉丝可评论: 0 否, 1 是")
    md_parser.add_argument("--no-interactive", action="store_true", help="禁用缺失字段时的交互提问")

    publish_parser = subparsers.add_parser("publish-article", help="根据 config.py 自动发布一篇公众号文章")
    publish_parser.add_argument("--no-wait", action="store_true", help="提交发布后不轮询最终结果")
    publish_parser.add_argument("--poll-interval", type=int, default=5, help="轮询发布状态间隔（秒）")
    publish_parser.add_argument("--timeout", type=int, default=180, help="等待发布结果超时时间（秒）")

    return parser.parse_args()


async def main():
    """主执行函数"""
    if APP_ID == "your_appid" or APP_SECRET == "your_appsecret":
        print("错误: 请在 config.py 文件中替换 'your_appid' 和 'your_appsecret' 为你的微信公众号AppID和AppSecret。")
        print("你可以在微信公众号后台 -> 设置与开发 -> 基本配置 中找到它们。")
        return

    args = parse_args()
    if not args.command:
        print("未指定命令。")
        print("可用命令:")
        print("  python app.py clean-images")
        print("  python app.py list-image-media")
        print("  python app.py draft-only")
        print("  python app.py draft-from-json --json-file article.json")
        print("  python app.py draft-from-markdown --md-file article.md --title 标题 --author 作者")
        print("  python app.py publish-article")
        print("  python app.py publish-article --no-wait")
        return

    wx = WxManager(appid=APP_ID, appsecret=APP_SECRET)
    try:
        if args.command == "clean-images":
            await clean_all_images(wx)
        elif args.command == "list-image-media":
            result = await wx.get_permanent_materials(material_type="image", offset=0, count=20)
            if not result:
                print("获取图片素材失败。")
            else:
                total_count = result.get("total_count", 0)
                item_count = result.get("item_count", 0)
                items = result.get("item", [])
                print(f"图片素材总数: {total_count}")
                print(f"本次返回: {item_count}")
                if not items:
                    print("没有查询到图片素材。")
                else:
                    print("\n前20个图片素材:")
                    for idx, item in enumerate(items, start=1):
                        media_id = item.get("media_id", "")
                        name = item.get("name", "")
                        update_time = item.get("update_time", 0)
                        print(f"{idx:02d}. media_id={media_id}")
                        print(f"    name={name}")
                        print(f"    update_time={update_time}")
        elif args.command == "draft-only":
            await create_draft_only(wx)
        elif args.command == "draft-from-json":
            await create_draft_from_json(
                wx_manager=wx,
                json_file=args.json_file,
                default_thumb_media_id=args.thumb_media_id,
                interactive=not args.no_interactive,
            )
        elif args.command == "draft-from-markdown":
            await create_draft_from_markdown(
                wx_manager=wx,
                markdown_file=args.md_file,
                title=args.title,
                author=args.author,
                thumb_media_id=args.thumb_media_id,
                digest=args.digest,
                content_source_url=args.content_source_url,
                need_open_comment=1 if int(args.need_open_comment) else 0,
                only_fans_can_comment=1 if int(args.only_fans_can_comment) else 0,
                interactive=not args.no_interactive,
            )
        elif args.command == "publish-article":
            await auto_publish_article(
                wx_manager=wx,
                wait_result=not args.no_wait,
                poll_interval=max(1, args.poll_interval),
                timeout=max(10, args.timeout),
            )

        print("\n脚本执行完毕。")
    finally:
        await wx.close_session()


if __name__ == "__main__":
    # 在Windows上，asyncio的默认事件循环策略可能会导致 aiohttp 在关闭时出错
    # 设置此策略可以解决 "Event loop is closed" 的常见问题
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())
