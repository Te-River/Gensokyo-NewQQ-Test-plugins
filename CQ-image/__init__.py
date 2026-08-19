"""
[CQ:image] 测试插件

触发指令：图片测试
功能：发送 URL 图片消息，验证 [CQ:image] 的 URL 解析路径。
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message

image_test = on_command("图片测试", priority=5)

_IMAGE_URL = "https://http.cat/200.jpg"


@image_test.handle()
async def handle_image_test():
    msg = Message(f"[CQ:image,file={_IMAGE_URL}]这是一张测试图片")
    await image_test.finish(msg)
