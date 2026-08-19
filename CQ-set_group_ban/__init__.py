"""
[CQ:set_group_ban] 测试插件

触发指令：禁言测试
功能：发送 [CQ:set_group_ban] 动作 CQ 码执行成员禁言（出站单向）。
用法：禁言测试 <duration秒> （缺省 60 秒；0=解除禁言）
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.params import CommandArg

ban_test = on_command("禁言测试", priority=5)


@ban_test.handle()
async def handle_ban_test(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    arg = args.extract_plain_text().strip()
    duration = int(arg) if arg.isdigit() else 60
    action = "解除禁言" if duration == 0 else f"禁言 {duration} 秒"
    msg = Message(f"[CQ:set_group_ban,user_id={event.user_id},duration={duration}]")
    await ban_test.finish(f"正在{action}")
