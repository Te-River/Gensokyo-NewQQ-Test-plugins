"""
get_group_member_blacklist 测试插件

触发指令：黑名单查询
功能：调用 Gensokyo 扩展 API get_group_member_blacklist 拉取群黑名单列表。

参数：
- group_id 必填（当前群，自动获取）
- limit 可选（单页条数，缺省 100；返回的 next_cursor 可用于继续翻页）

用法（群聊触发）：
  黑名单查询          → 拉取第一页
  黑名单查询 50       → 单页 50 条
"""

import time

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.params import CommandArg

blacklist_query_test = on_command("黑名单查询", priority=5)


def mask_id(value) -> str:
    """长 ID（OpenID/虚拟ID）脱敏：保留前 4 后 4，中间掩码。"""
    s = str(value)
    if len(s) <= 8:
        return s
    return f"{s[:4]}***{s[-4:]}"


def format_time(ts) -> str:
    """秒级时间戳转可读时间，0 视为无记录。"""
    if not ts:
        return "-"
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


@blacklist_query_test.handle()
async def handle_blacklist_query_test(
    bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()
) -> None:
    arg = args.extract_plain_text().strip()
    params = {"group_id": str(event.group_id)}
    if arg.isdigit():
        params["limit"] = int(arg)

    try:
        result = await bot.call_api("get_group_member_blacklist", **params)
    except Exception as e:
        await blacklist_query_test.finish(f"❌ 拉取黑名单失败：{e}")

    users = result.get("users") or []
    next_cursor = result.get("next_cursor")

    if not users:
        lines = ["📭 当前群黑名单为空"]
    else:
        lines = [f"🚫 群黑名单共 {len(users)} 人："]
        for u in users:
            bot_flag = "是" if u.get("bot") else "否"
            lines.append(
                f"· [{mask_id(u.get('user_id'))}] {u.get('username', '')} "
                f"封禁于 {format_time(u.get('banned_at'))} 机器人:{bot_flag}"
            )
    if next_cursor:
        lines.append(f"（next_cursor={next_cursor}，可继续翻页）")
    await blacklist_query_test.finish("\n".join(lines))
