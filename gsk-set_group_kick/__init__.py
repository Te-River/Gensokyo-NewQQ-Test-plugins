"""
set_group_kick 测试插件

触发指令：踢人API测试
功能：调用 Gensokyo 扩展 API set_group_kick 批量踢出群成员（可选拉黑）。

参数：
- group_id 必填（当前群，自动获取）
- user_ids 必填（一个或多个成员，空格分隔）
- 结尾出现"拉黑"则 add_blacklist=true（缺省 false）

用法（群聊触发）：
  踢人API测试 123456            → 踢出单个成员
  踢人API测试 111 222           → 批量踢出
  踢人API测试 111 222 拉黑      → 批量踢出并加入黑名单
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.params import CommandArg

kick_api_test = on_command("踢人API测试", priority=5)


def mask_id(value) -> str:
    """长 ID（OpenID/虚拟ID）脱敏：保留前 4 后 4，中间掩码。"""
    s = str(value)
    if len(s) <= 8:
        return s
    return f"{s[:4]}***{s[-4:]}"


@kick_api_test.handle()
async def handle_kick_api_test(
    bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()
) -> None:
    parts = [p for p in args.extract_plain_text().strip().split() if p]
    if not parts:
        await kick_api_test.finish("用法：踢人API测试 <user_id> [user_id2 ...] [拉黑]")
    add_blacklist = "拉黑" in parts
    user_ids = [p for p in parts if p != "拉黑"]

    try:
        result = await bot.call_api(
            "set_group_kick",
            group_id=str(event.group_id),
            user_ids=user_ids,
            add_blacklist=add_blacklist,
        )
    except Exception as e:
        await kick_api_test.finish(f"❌ 踢人失败：{e}")

    suffix = "(+拉黑)" if add_blacklist else ""
    lines = [f"✅ 已提交踢人{suffix}"]
    lines.append(f"· remove_members_result：{result.get('remove_members_result')}")
    kicked = result.get("kicked") or []
    if kicked:
        lines.append(f"· 已踢出：{'、'.join(mask_id(u) for u in kicked)}")
    fail_openids = result.get("add_to_member_blacklist_fail_openids") or []
    if fail_openids:
        lines.append(f"· 拉黑失败：{'、'.join(mask_id(u) for u in fail_openids)}")
    await kick_api_test.finish("\n".join(lines))
