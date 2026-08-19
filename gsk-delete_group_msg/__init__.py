"""
delete_group_msg 测试插件

触发指令：撤回API测试
功能：调用 Gensokyo 扩展 API delete_group_msg 撤回 q群 内指定用户或
Bot 自身的消息（与 [CQ:remove] CQ 码路径不同，本插件走独立 API）。

参数规则（对齐 handler 实现）：
- group_id 必填（当前群，自动获取）
- user_id 省略/0/负 → 撤回 Bot 自身消息
- user_id 为正数     → 撤回该用户的最后一条消息
- message_id 省略    → 自动查找该用户/Bot 的最后一条消息
- message_id 指定    → 撤回指定消息

用法（群聊触发）：
  撤回API测试              → 撤回 Bot 在本群的最后一条消息
  撤回API测试 <虚拟用户ID>  → 撤回指定用户的最后一条消息
  撤回API测试 <虚拟用户ID> <msg_id> → 撤回指定用户的指定消息
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.params import CommandArg

delete_group_msg_test = on_command("撤回API测试", priority=5)


def mask_id(value) -> str:
    """长 ID（OpenID/虚拟ID/消息ID）脱敏：保留前 4 后 4，中间掩码。"""
    s = str(value)
    if len(s) <= 8:
        return s
    return f"{s[:4]}***{s[-4:]}"


@delete_group_msg_test.handle()
async def handle_delete_group_msg_test(
    bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()
) -> None:
    parts = args.extract_plain_text().strip().split()
    user_id = parts[0] if len(parts) > 0 and parts[0].isdigit() else ""
    msg_id = parts[1] if len(parts) > 1 else ""

    params = {"group_id": str(event.group_id)}
    if user_id:
        params["user_id"] = user_id
    if msg_id:
        params["message_id"] = msg_id

    desc = "Bot 自身最后一条消息"
    if user_id:
        desc = f"用户 {mask_id(user_id)} 的" + ("指定消息" if msg_id else "最后一条消息")

    try:
        result = await bot.call_api("delete_group_msg", **params)
        if msg_id:
            await delete_group_msg_test.finish(f"✅ 已撤回{desc}（msg_id={mask_id(msg_id)}）\n返回：{result}")
        else:
            await delete_group_msg_test.finish(f"✅ 已撤回{desc}\n返回：{result}")
    except Exception as e:
        await delete_group_msg_test.finish(f"❌ 撤回{desc}失败：{e}")
