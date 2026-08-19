"""
[CQ:remove] 测试插件

触发指令：撤回测试
功能：发送 [CQ:remove] 动作 CQ 码撤回指定群消息（出站单向）。
用法：撤回测试 <msg_id>
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.params import CommandArg

remove_test = on_command("撤回测试", priority=5)


@remove_test.handle()
async def handle_remove_test(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    msg_id = args.extract_plain_text().strip()
    if not msg_id:
        await remove_test.finish("用法：撤回测试 <msg_id>，例如：撤回测试 1823")
    # 纯动作 CQ 码消息：Gensokyo 执行后不发送到群
    msg = Message(f"[CQ:remove,user_id={event.user_id},msg_id={msg_id}]")
    await remove_test.finish(msg)
