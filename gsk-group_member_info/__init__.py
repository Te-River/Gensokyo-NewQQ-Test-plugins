"""
get_group_member_info 测试插件

触发指令：成员信息
功能：调用 Gensokyo 扩展 API get_group_member_info 查询单个群成员资料。

参数：
- group_id 必填（当前群，自动获取）
- user_id 可选（缺省查询自己）

用法（群聊触发）：
  成员信息              → 查询自己
  成员信息 <user_id>    → 查询指定成员
"""

import time

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.params import CommandArg

member_info_test = on_command("成员信息", priority=5)


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


@member_info_test.handle()
async def handle_member_info_test(
    bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()
) -> None:
    arg = args.extract_plain_text().strip()
    user_id = arg if arg.isdigit() else str(event.user_id)

    try:
        m = await bot.call_api(
            "get_group_member_info",
            group_id=str(event.group_id),
            user_id=user_id,
        )
    except Exception as e:
        await member_info_test.finish(f"❌ 查询成员信息失败：{e}")

    lines = [f"👤 成员 [{mask_id(m.get('user_id'))}]："]
    lines.append(
        f"· 昵称：{m.get('nickname', '')}"
        f"（群名片：{m.get('card') or '无'}）"
    )
    lines.append(f"· 角色：{m.get('role', '')}")
    lines.append(f"· 入群时间：{format_time(m.get('join_time'))}")
    lines.append(f"· 禁言到期：{format_time(m.get('shut_up_timestamp'))}")
    await member_info_test.finish("\n".join(lines))
