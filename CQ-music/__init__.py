"""
[CQ:music] 测试插件

触发指令：音乐测试
功能：发送 QQ 音乐分享消息，验证 [CQ:music,type=qq,id=xxx] 解析路径。
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message

music_test = on_command("音乐测试", priority=5)

# 示例 QQ 音乐 ID（《晴天》）
_MUSIC_ID = "153676"


@music_test.handle()
async def handle_music_test():
    msg = Message(f"[CQ:music,type=qq,id={_MUSIC_ID}]")
    await music_test.finish(msg)
