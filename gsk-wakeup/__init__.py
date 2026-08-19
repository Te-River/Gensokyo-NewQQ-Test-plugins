"""
send_private_msg_wakeup 测试插件

触发指令：召回测试
功能：调用 Gensokyo 扩展 API send_private_msg_wakeup 发送 C2C 召回消息（is_wakeup=true）。
用法：召回测试 <消息内容>  （私聊场景）
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, PrivateMessageEvent, Message
from nonebot.params import CommandArg

wakeup_test = on_command("召回测试", priority=5)


@wakeup_test.handle()
async def handle_wakeup_test(bot: Bot, event: PrivateMessageEvent, args: Message = CommandArg()):
    text = args.extract_plain_text().strip() or "这是一条召回测试消息"
    try:
        await bot.call_api("send_private_msg_wakeup", user_id=str(event.user_id), message=text)
        await wakeup_test.finish(f"召回消息已发送：{text}")
    except Exception as e:
        await wakeup_test.finish(f"调用失败：{e}")
