"""
[CQ:set_group] 统一动作 CQ 码测试插件

覆盖 8 种 action（出站单向，执行后 CQ 码从文本移除）：
- 群禁言测试 <秒>            → action=ban（缺省 60 秒；0=解除禁言）
- 群全员禁言测试 on|off       → action=whole_ban
- 入群审批测试 <flag> 通过|拒绝 → action=add_request
- 策略执行测试 <strategy_id>  → action=strategy_execute
- 策略删除测试 <strategy_id>  → action=strategy_delete
- 踢人测试 <user_id> [user_id2 ...] [拉黑] → action=kick
  （user_ids 逗号分隔批量；结尾出现"拉黑"则 add_blacklist=true；
    user_id 与 user_ids 可同时存在会合并；group_id 省略回退当前群）
- 黑名单加入测试 <user_id...> → action=blacklist_add（群内成员会被官方拒绝，属预期）
- 黑名单移出测试 <user_id...> → action=blacklist_del
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message
from nonebot.params import CommandArg

# 审批决定的可选词（缺省视为通过）
_APPROVE_WORDS = ("通过", "true", "1", "on")

# ── 禁言（ban）──────────────────────────────
group_ban_test = on_command("群禁言测试", priority=5)


@group_ban_test.handle()
async def handle_group_ban_test(
    event: GroupMessageEvent, args: Message = CommandArg()
) -> None:
    arg = args.extract_plain_text().strip()
    duration = int(arg) if arg.isdigit() else 60
    action = "解除禁言" if duration == 0 else f"禁言 {duration} 秒"
    cq = f"[CQ:set_group,action=ban,user_id={event.user_id},duration={duration}]"
    await group_ban_test.finish(Message(cq) + f" 正在{action}")


# ── 全员禁言（whole_ban）─────────────────────
group_whole_ban_test = on_command("群全员禁言测试", priority=5)


@group_whole_ban_test.handle()
async def handle_group_whole_ban_test(
    _event: GroupMessageEvent, args: Message = CommandArg()
) -> None:
    arg = args.extract_plain_text().strip().lower()
    enable = "true" if arg in ("on", "true", "1", "开启") else "false"
    cq = f"[CQ:set_group,action=whole_ban,enable={enable}]"
    state = "开启" if enable == "true" else "关闭"
    await group_whole_ban_test.finish(Message(cq) + f" 正在{state}全员禁言")


# ── 入群申请审批（add_request）────────────────
approval_test = on_command("入群审批测试", priority=5)


@approval_test.handle()
async def handle_approval_test(
    event: GroupMessageEvent, args: Message = CommandArg()
) -> None:
    parts = args.extract_plain_text().strip().split(maxsplit=1)
    if not parts:
        await approval_test.finish(
            "用法：入群审批测试 <flag> [通过|拒绝]"
            "（flag 来自入站 request 事件或 get_group_join_request_list）"
        )
    flag = parts[0]
    rest = parts[1:]
    approve = "true" if not rest or rest[0] in _APPROVE_WORDS else "false"
    op = "通过" if approve == "true" else "拒绝"
    cq = (
        f"[CQ:set_group,action=add_request,user_id={event.user_id},"
        f"flag={flag},approve={approve}]"
    )
    await approval_test.finish(Message(cq) + f" 正在{op}申请 {flag}")


# ── 审批策略执行（strategy_execute）───────────
strategy_execute_test = on_command("策略执行测试", priority=5)


@strategy_execute_test.handle()
async def handle_strategy_execute_test(
    _event: GroupMessageEvent, args: Message = CommandArg()
) -> None:
    sid = args.extract_plain_text().strip()
    if not sid:
        await strategy_execute_test.finish("用法：策略执行测试 <strategy_id>")
    cq = f"[CQ:set_group,action=strategy_execute,strategy_id={sid}]"
    await strategy_execute_test.finish(Message(cq) + f" 正在执行策略 {sid}")


# ── 审批策略删除（strategy_delete）───────────
strategy_delete_test = on_command("策略删除测试", priority=5)


@strategy_delete_test.handle()
async def handle_strategy_delete_test(
    _event: GroupMessageEvent, args: Message = CommandArg()
) -> None:
    sid = args.extract_plain_text().strip()
    if not sid:
        await strategy_delete_test.finish("用法：策略删除测试 <strategy_id>")
    cq = f"[CQ:set_group,action=strategy_delete,strategy_id={sid}]"
    await strategy_delete_test.finish(Message(cq) + f" 正在删除策略 {sid}")


# ── 踢人（kick，user_ids 批量，可选拉黑）────────
kick_test = on_command("踢人测试", priority=5)


@kick_test.handle()
async def handle_kick_test(
    event: GroupMessageEvent, args: Message = CommandArg()
) -> None:
    parts = [p for p in args.extract_plain_text().strip().split() if p]
    if not parts:
        await kick_test.finish("用法：踢人测试 <user_id> [user_id2 ...] [拉黑]")
    add_blacklist = "拉黑" in parts
    user_ids = [p for p in parts if p != "拉黑"]
    cq = (
        f"[CQ:set_group,action=kick,user_ids={','.join(user_ids)},"
        f"add_blacklist={'true' if add_blacklist else 'false'},"
        f"group_id={event.group_id}]"
    )
    suffix = "(+拉黑)" if add_blacklist else ""
    await kick_test.finish(
        Message(cq) + f" 已提交踢人{suffix}，目标：{'、'.join(user_ids)}"
    )


# ── 黑名单加入（blacklist_add）────────────────
blacklist_add_test = on_command("黑名单加入测试", priority=5)


@blacklist_add_test.handle()
async def handle_blacklist_add_test(
    _event: GroupMessageEvent, args: Message = CommandArg()
) -> None:
    parts = [p for p in args.extract_plain_text().strip().split() if p]
    if not parts:
        await blacklist_add_test.finish(
            "用法：黑名单加入测试 <user_id> [user_id2 ...]"
            "（群内成员会被官方拒绝，属预期）"
        )
    cq = f"[CQ:set_group,action=blacklist_add,user_ids={','.join(parts)}]"
    await blacklist_add_test.finish(
        Message(cq) + f" 正在加入黑名单：{'、'.join(parts)}"
    )


# ── 黑名单移出（blacklist_del）────────────────
blacklist_del_test = on_command("黑名单移出测试", priority=5)


@blacklist_del_test.handle()
async def handle_blacklist_del_test(
    _event: GroupMessageEvent, args: Message = CommandArg()
) -> None:
    parts = [p for p in args.extract_plain_text().strip().split() if p]
    if not parts:
        await blacklist_del_test.finish("用法：黑名单移出测试 <user_id> [user_id2 ...]")
    cq = f"[CQ:set_group,action=blacklist_del,user_ids={','.join(parts)}]"
    await blacklist_del_test.finish(
        Message(cq) + f" 正在移出黑名单：{'、'.join(parts)}"
    )
