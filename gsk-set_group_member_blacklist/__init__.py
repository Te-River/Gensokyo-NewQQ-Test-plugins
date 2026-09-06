"""
set_group_member_blacklist 测试插件

触发指令：黑名单操作API测试
功能：调用 Gensokyo 扩展 API set_group_member_blacklist 批量加入/移出群黑名单。

参数：
- group_id 必填（当前群，自动获取）
- op 必填：add（加入）或 del（移出）
- user_ids 必填（一个或多个成员，空格分隔）
注意：add 群内成员会被官方拒绝，属预期行为。

用法（群聊触发）：
  黑名单操作API测试 add 111 222   → 加入黑名单
  黑名单操作API测试 del 111       → 移出黑名单
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.params import CommandArg

blacklist_op_test = on_command("黑名单操作API测试", priority=5)


def mask_id(value) -> str:
    """长 ID（OpenID/虚拟ID）脱敏：保留前 4 后 4，中间掩码。"""
    s = str(value)
    if len(s) <= 8:
        return s
    return f"{s[:4]}***{s[-4:]}"


@blacklist_op_test.handle()
async def handle_blacklist_op_test(
    bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()
) -> None:
    parts = [p for p in args.extract_plain_text().strip().split() if p]
    if len(parts) < 2 or parts[0] not in ("add", "del"):
        await blacklist_op_test.finish(
            "用法：黑名单操作API测试 add|del <user_id> [user_id2 ...]"
        )
    op = parts[0]
    user_ids = parts[1:]

    try:
        result = await bot.call_api(
            "set_group_member_blacklist",
            group_id=str(event.group_id),
            op=op,
            user_ids=user_ids,
        )
    except Exception as e:
        await blacklist_op_test.finish(f"❌ 黑名单操作失败：{e}")

    action = "加入" if op == "add" else "移出"
    fail_openids = result.get("fail_openids") or []
    if fail_openids:
        lines = [f"⚠️ {action}黑名单部分失败（{len(fail_openids)} 个）："]
        lines.append("、".join(mask_id(u) for u in fail_openids))
        await blacklist_op_test.finish("\n".join(lines))
    await blacklist_op_test.finish(f"✅ {action}黑名单全部成功")
