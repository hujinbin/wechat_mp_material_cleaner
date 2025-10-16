import asyncio
import aiohttp
import sys
import time
from config import APP_ID, APP_SECRET

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


async def main():
    """主执行函数"""
    if APP_ID == "your_appid" or APP_SECRET == "your_appsecret":
        print("错误: 请在 config.py 文件中替换 'your_appid' 和 'your_appsecret' 为你的微信公众号AppID和AppSecret。")
        print("你可以在微信公众号后台 -> 设置与开发 -> 基本配置 中找到它们。")
        return

    wx = WxManager(appid=APP_ID, appsecret=APP_SECRET)
    try:
        # **危险操作**: 下面的函数会删除公众号所有的永久图片素材，请谨慎操作！
        # **请在执行前确认你真的要删除所有图片！**
        # 如果确认，请取消下面这行代码的注释
        await clean_all_images(wx)

        # 如果你只想删除指定的几个图片，可以使用下面的方式：
        # image_ids_to_delete = ["media_id_1", "media_id_2"]
        # await wx.delete_materials(image_ids_to_delete)
        
        print("\n脚本执行完毕。如果未执行任何操作，请检查代码中的注释。")
    finally:
        await wx.close_session()


if __name__ == "__main__":
    # 在Windows上，asyncio的默认事件循环策略可能会导致 aiohttp 在关闭时出错
    # 设置此策略可以解决 "Event loop is closed" 的常见问题
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())
