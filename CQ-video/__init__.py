"""
[CQ:video] 测试插件

触发指令：视频测试
功能：发送 URL 视频消息，验证 [CQ:video] 的 URL 解析路径。
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message

video_test = on_command("视频测试", priority=5)

_VIDEO_URL = "https://www.w3schools.com/html/mov_bbb.mp4"


@video_test.handle()
async def handle_video_test():
    msg = Message(f"[CQ:video,file={_VIDEO_URL}]这是一段测试视频")
    await video_test.finish(msg)
