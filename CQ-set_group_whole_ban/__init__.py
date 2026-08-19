"""
[CQ:set_group_whole_ban] 测试插件

触发指令：全员禁言测试
功能：发送 [CQ:set_group_whole_ban] 动作 CQ 码开关全员禁言（出站单向）。
用法：全员禁言测试 on|off
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message
from nonebot.params import CommandArg

whole_ban_test = on_command("全员禁言测试", priority=5)


@whole_ban_test.handle()
async def handle_whole_ban_test(event: GroupMessageEvent, args: Message = CommandArg()):
    arg = args.extract_plain_text().strip().lower()
    enable = "true" if arg in ("on", "true", "1", "开启") else "false"
    msg = Message(f"[CQ:set_group_whole_ban,enable={enable}]")
    state = "开启" if enable == "true" else "关闭"
    await whole_ban_test.finish(f"正在{state}全员禁言")
