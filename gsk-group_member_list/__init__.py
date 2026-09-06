"""
get_group_member_list 测试插件

触发指令：成员列表
功能：调用 Gensokyo 扩展 API get_group_member_list 拉取群成员列表。

参数：
- group_id 必填（当前群，自动获取）
- 数量可选（展示前 N 个成员，缺省 20，始终显示总数）

用法（群聊触发）：
  成员列表          → 展示前 20 个成员
  成员列表 50       → 展示前 50 个成员
"""

import time

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.params import CommandArg

member_list_test = on_command("成员列表", priority=5)

# 角色图标：owner/admin 特殊标记，其余按普通成员处理
_ROLE_EMOJI = {"owner": "👑", "admin": "🛡"}


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


@member_list_test.handle()
async def handle_member_list_test(
    bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()
) -> None:
    arg = args.extract_plain_text().strip()
    limit = int(arg) if arg.isdigit() and int(arg) > 0 else 20

    try:
        members = await bot.call_api(
            "get_group_member_list", group_id=str(event.group_id)
        )
    except Exception as e:
        await member_list_test.finish(f"❌ 拉取成员列表失败：{e}")

    shown = members[:limit]
    lines = [f"👥 群成员共 {len(members)} 人（展示前 {len(shown)} 个）："]
    for m in shown:
        role = m.get("role", "member")
        emoji = _ROLE_EMOJI.get(role, "👤")
        lines.append(
            f"{emoji}[{mask_id(m.get('user_id'))}] {m.get('nickname', '')}"
            f"（{role}）入群于 {format_time(m.get('join_time'))}"
        )
    await member_list_test.finish("\n".join(lines))
