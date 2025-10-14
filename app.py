import requests
import json
import time
from config import APP_ID, APP_SECRET

class WxManager:
    def __init__(self, appid, appsecret):
        self.appid = appid
        self.appsecret = appsecret
        self.session = requests.Session()
        self.token = None
        self.token_expires_at = 0
        self._get_access_token()

    def _get_access_token(self):
        # 如果token存在且未过期，则直接返回
        if self.token and self.token_expires_at > time.time():
            return

        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.appid}&secret={self.appsecret}"
        response = self.session.get(url)
        data = response.json()
        if "access_token" in data:
            self.token = data["access_token"]
            # 微信的token有效期为7200秒，这里设置一个缓冲时间
            self.token_expires_at = time.time() + data["expires_in"] - 600
            print("获取 access_token 成功")
        else:
            raise Exception(f"获取 access_token 失败: {data.get('errmsg', '未知错误')}")

    def get_permanent_materials(self, material_type="image", offset=0, count=20):
        """获取永久素材列表"""
        self._get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/material/batchget_material?access_token={self.token}"
        payload = {
            "type": material_type,
            "offset": offset,
            "count": count
        }
        response = self.session.post(url, data=json.dumps(payload))
        result = response.json()
        if "item" in result:
            return result
        else:
            print(f"获取素材列表失败: {result.get('errmsg', '未知错误')}")
            return None

    def delete_materials(self, media_ids):
        """批量删除永久素材"""
        if not media_ids:
            print("没有需要删除的素材ID")
            return
        
        deleted_count = 0
        failed_count = 0
        for media_id in media_ids:
            self._get_access_token()
            url = f"https://api.weixin.qq.com/cgi-bin/material/del_material?access_token={self.token}"
            payload = {"media_id": media_id}
            response = self.session.post(url, data=json.dumps(payload))
            if response.json().get("errcode") == 0:
                print(f"删除素材 {media_id} 成功")
                deleted_count += 1
            else:
                print(f"删除素材 {media_id} 失败: {response.json().get('errmsg', '未知错误')}")
                failed_count += 1
        print(f"删除完成: 成功 {deleted_count} 个, 失败 {failed_count} 个")


def clean_all_images(wx_manager):
    """清理所有永久图片素材"""
    total_count = -1
    current_offset = 0
    page_size = 20 # 每次最多获取20个

    while total_count == -1 or current_offset < total_count:
        materials_data = wx_manager.get_permanent_materials(material_type="image", offset=current_offset, count=page_size)
        
        if not materials_data:
            print("无法获取素材列表，脚本终止。")
            break

        if total_count == -1:
            total_count = materials_data.get("total_count", 0)
            print(f"检测到总共有 {total_count} 个图片素材。")
            if total_count == 0:
                print("没有图片素材需要清理。")
                break
        
        items = materials_data.get("item", [])
        if not items:
            print("当前批次没有获取到素材，可能已全部处理完毕。")
            break

        media_ids_to_delete = [item['media_id'] for item in items]
        print(f"正在删除 {len(media_ids_to_delete)} 个图片素材 (偏移量: {current_offset})...")
        wx_manager.delete_materials(media_ids_to_delete)
        
        current_offset += len(items)
        # 如果返回的素材数量小于请求的数量，说明已经是最后一页了
        if len(items) < page_size:
            break
        
        time.sleep(1) # 避免过于频繁的API调用

    print("所有图片素材清理完毕。")


# --- 使用示例 ---
if __name__ == "__main__":
    if APP_ID == "your_appid" or APP_SECRET == "your_appsecret":
        print("错误: 请在 config.py 文件中替换 'your_appid' 和 'your_appsecret' 为你的微信公众号AppID和AppSecret。")
        print("你可以在微信公众号后台 -> 设置与开发 -> 基本配置 中找到它们。")
    else:
        wx = WxManager(appid=APP_ID, appsecret=APP_SECRET)
        
        # **危险操作**: 下面的函数会删除公众号所有的永久图片素材，请谨慎操作！
        # **请在执行前确认你真的要删除所有图片！**
        # 如果确认，请取消下面这行代码的注释
        clean_all_images(wx)

        # 如果你只想删除指定的几个图片，可以使用下面的方式：
        # image_ids_to_delete = ["media_id_1", "media_id_2"]
        # wx.delete_materials(image_ids_to_delete)
        
        print("\n脚本执行完毕。如果未执行任何操作，请检查代码中的注释。")