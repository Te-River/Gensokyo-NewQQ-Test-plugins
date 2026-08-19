"""
[CQ:keyboard] 测试插件

触发指令：键盘测试
功能：发送一条带有内嵌键盘按钮的文本消息，用于验证 [CQ:keyboard] CQ 码是否正常工作。
"""

import base64
import json

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event

keyboard_test = on_command("键盘测试", priority=5)

# 测试键盘 JSON：包含指令按钮、跳转按钮
_keyboard_data = {
    "content": {
        "rows": [
            {
                "buttons": [
                    {
                        "id": "btn_hello",
                        "render_data": {"label": "你好", "style": 1},
                        "action": {
                            "type": 2,
                            "data": "/你好",
                            "permission": {"type": 2},
                        },
                    },
                    {
                        "id": "btn_help",
                        "render_data": {"label": "帮助", "style": 0},
                        "action": {
                            "type": 2,
                            "data": "/帮助",
                            "permission": {"type": 2},
                        },
                    },
                ]
            },
            {
                "buttons": [
                    {
                        "id": "btn_link",
                        "render_data": {"label": "打开链接", "style": 2},
                        "action": {
                            "type": 0,
                            "data": "https://example.com",
                            "permission": {"type": 2},
                        },
                    },
                ]
            },
        ]
    }
}


@keyboard_test.handle()
async def handle_keyboard_test(bot: Bot, event: Event) -> None:
    """发送带 [CQ:keyboard] 的文本消息"""
    b64 = base64.b64encode(
        json.dumps(_keyboard_data, ensure_ascii=False).encode()
    ).decode()
    msg = f"[CQ:keyboard,data=base64://{b64}]你好，这是键盘按钮测试喵~"
    await bot.send(event, msg)
