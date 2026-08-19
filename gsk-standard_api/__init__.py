"""
标准 OneBot V11 API 测试插件（P2 补全）

触发指令：
  群信息        → get_group_info       （当前群）
  群列表API     → get_group_list
  成员信息      → get_group_member_info（当前群，@某人 或 不传=触发者）
  成员列表      → get_group_member_list（当前群）
  好友列表      → get_friend_list
  登录信息      → get_login_info
  运行状态      → get_status
  版本信息      → get_version_info
  在线客户端    → get_online_clients
  撤回标准      → delete_msg            （需 message_id + group_id/user_id）
  已读测试      → mark_msg_as_read
  原始发送      → send_group_msg_raw    （少预处理，保留原始参数）
  转发测试      → send_group_forward_msg（合并转发，messages 节点数组）

安全说明：所有输出中的长 ID（OpenID/虚拟ID/消息ID）经 mask_id 脱敏展示，
仅保留前 4 后 4 位；参数回传时仍使用真实值。
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    Event,
    GroupMessageEvent,
    Message,
    MessageSegment,
)
from nonebot.params import CommandArg


# ---------- 脱敏辅助 ----------

def mask_id(value) -> str:
    """长 ID（OpenID/虚拟ID/消息ID）脱敏：保留前 4 后 4，中间掩码。"""
    s = str(value)
    if len(s) <= 8:
        return s
    return f"{s[:4]}***{s[-4:]}"


def mask_result(result) -> str:
    """对 API 返回的 JSON 做脱敏（递归替换长数字/长字符串）。"""
    import json

    def _walk(obj):
        if isinstance(obj, dict):
            return {k: _walk(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_walk(v) for v in obj]
        if isinstance(obj, str):
            # 32 位 OpenID 或 9 位以上数字 ID 视为敏感 ID
            if len(obj) >= 32 or (obj.isdigit() and len(obj) >= 9):
                return mask_id(obj)
            return obj
        if isinstance(obj, int) and abs(obj) >= 1_000_000_000:
            return mask_id(obj)
        return obj

    try:
        return json.dumps(_walk(json.loads(result)), ensure_ascii=False)
    except Exception:
        return mask_id(result)


# ── get_group_info ───────────────────────────

group_info_cmd = on_command("群信息", priority=5)


@group_info_cmd.handle()
async def handle_group_info(bot: Bot, event: Event):
    if not isinstance(event, GroupMessageEvent):
        await group_info_cmd.finish("❌ 仅支持群聊触发")
    try:
        result = await bot.call_api("get_group_info", group_id=str(event.group_id))
        await group_info_cmd.finish(f"群信息：{mask_result(result)}")
    except Exception as e:
        await group_info_cmd.finish(f"❌ 获取失败：{e}")


# ── get_group_list ───────────────────────────

group_list_cmd = on_command("群列表API", priority=5)


@group_list_cmd.handle()
async def handle_group_list(bot: Bot, event: Event):
    try:
        result = await bot.call_api("get_group_list")
        await group_list_cmd.finish(f"群列表：{mask_result(result)}")
    except Exception as e:
        await group_list_cmd.finish(f"❌ 获取失败：{e}")


# ── get_group_member_info ────────────────────

member_info_cmd = on_command("成员信息", priority=5)


@member_info_cmd.handle()
async def handle_member_info(bot: Bot, event: Event, args: Message = CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await member_info_cmd.finish("❌ 仅支持群聊触发")
    user_id = None
    for seg in args:
        if seg.type == "at":
            user_id = str(seg.data.get("qq", ""))
            break
    if user_id is None:
        arg_text = args.extract_plain_text().strip()
        user_id = arg_text if arg_text else str(event.user_id)
    try:
        result = await bot.call_api(
            "get_group_member_info",
            group_id=str(event.group_id),
            user_id=user_id,
        )
        await member_info_cmd.finish(f"成员信息：{mask_result(result)}")
    except Exception as e:
        await member_info_cmd.finish(f"❌ 获取失败：{e}")


# ── get_group_member_list ────────────────────

member_list_cmd = on_command("成员列表", priority=5)


@member_list_cmd.handle()
async def handle_member_list(bot: Bot, event: Event):
    if not isinstance(event, GroupMessageEvent):
        await member_list_cmd.finish("❌ 仅支持群聊触发")
    try:
        result = await bot.call_api("get_group_member_list", group_id=str(event.group_id))
        await member_list_cmd.finish(f"成员列表：{mask_result(result)}")
    except Exception as e:
        await member_list_cmd.finish(f"❌ 获取失败：{e}")


# ── get_friend_list ──────────────────────────

friend_list_cmd = on_command("好友列表", priority=5)


@friend_list_cmd.handle()
async def handle_friend_list(bot: Bot, event: Event):
    try:
        result = await bot.call_api("get_friend_list")
        await friend_list_cmd.finish(f"好友列表：{mask_result(result)}")
    except Exception as e:
        await friend_list_cmd.finish(f"❌ 获取失败：{e}")


# ── get_login_info ───────────────────────────

login_info_cmd = on_command("登录信息", priority=5)


@login_info_cmd.handle()
async def handle_login_info(bot: Bot, event: Event):
    try:
        result = await bot.call_api("get_login_info")
        await login_info_cmd.finish(f"登录信息：{mask_result(result)}")
    except Exception as e:
        await login_info_cmd.finish(f"❌ 获取失败：{e}")


# ── get_status ───────────────────────────────

status_cmd = on_command("运行状态", priority=5)


@status_cmd.handle()
async def handle_status(bot: Bot, event: Event):
    try:
        result = await bot.call_api("get_status")
        await status_cmd.finish(f"运行状态：{mask_result(result)}")
    except Exception as e:
        await status_cmd.finish(f"❌ 获取失败：{e}")


# ── get_version_info ─────────────────────────

version_info_cmd = on_command("版本信息", priority=5)


@version_info_cmd.handle()
async def handle_version_info(bot: Bot, event: Event):
    try:
        result = await bot.call_api("get_version_info")
        await version_info_cmd.finish(f"版本信息：{mask_result(result)}")
    except Exception as e:
        await version_info_cmd.finish(f"❌ 获取失败：{e}")


# ── get_online_clients ───────────────────────

online_clients_cmd = on_command("在线客户端", priority=5)


@online_clients_cmd.handle()
async def handle_online_clients(bot: Bot, event: Event):
    try:
        result = await bot.call_api("get_online_clients")
        await online_clients_cmd.finish(f"在线客户端：{mask_result(result)}")
    except Exception as e:
        await online_clients_cmd.finish(f"❌ 获取失败：{e}")


# ── delete_msg（标准撤回） ───────────────────

delete_msg_cmd = on_command("撤回标准", priority=5)


@delete_msg_cmd.handle()
async def handle_delete_msg(bot: Bot, event: Event, args: Message = CommandArg()):
    parts = args.extract_plain_text().strip().split()
    if not parts:
        await delete_msg_cmd.finish("用法：撤回标准 <message_id> [user_id]，群聊中省略 user_id 用当前群")
    msg_id = parts[0]
    user_id = parts[1] if len(parts) > 1 else ""

    params: dict = {"message_id": msg_id}
    if isinstance(event, GroupMessageEvent):
        params["group_id"] = str(event.group_id)
    if user_id:
        params["user_id"] = user_id
    if "group_id" not in params and "user_id" not in params:
        params["user_id"] = str(event.user_id)

    try:
        result = await bot.call_api("delete_msg", **params)
        await delete_msg_cmd.finish(f"✅ 已撤回 {mask_id(msg_id)}：{mask_result(result)}")
    except Exception as e:
        await delete_msg_cmd.finish(f"❌ 撤回失败：{e}")


# ── mark_msg_as_read ─────────────────────────

mark_read_cmd = on_command("已读测试", priority=5)


@mark_read_cmd.handle()
async def handle_mark_read(bot: Bot, event: Event):
    try:
        result = await bot.call_api("mark_msg_as_read")
        await mark_read_cmd.finish(f"标记已读：{mask_result(result)}")
    except Exception as e:
        await mark_read_cmd.finish(f"❌ 调用失败：{e}")


# ── send_group_msg_raw ───────────────────────

raw_send_cmd = on_command("原始发送", priority=5)


@raw_send_cmd.handle()
async def handle_raw_send(bot: Bot, event: Event, args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    if not text:
        await raw_send_cmd.finish("用法：原始发送 <内容>（仅群聊）")
    if not isinstance(event, GroupMessageEvent):
        await raw_send_cmd.finish("❌ 仅支持群聊触发")
    try:
        result = await bot.call_api(
            "send_group_msg_raw", group_id=str(event.group_id), message=text
        )
        await raw_send_cmd.finish(f"✅ 原始发送成功：{mask_result(result)}")
    except Exception as e:
        await raw_send_cmd.finish(f"❌ 发送失败：{e}")


# ── send_group_forward_msg（合并转发） ───────

forward_cmd = on_command("转发测试", priority=5)


@forward_cmd.handle()
async def handle_forward(bot: Bot, event: Event, args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    if not text:
        await forward_cmd.finish("用法：转发测试 <内容>（构造两条合并转发消息，仅群聊）")
    if not isinstance(event, GroupMessageEvent):
        await forward_cmd.finish("❌ 仅支持群聊触发")

    nodes = [
        {"type": "node", "data": {"content": f"{text}（第1条）"}},
        {"type": "node", "data": {"content": f"{text}（第2条）"}},
    ]
    try:
        result = await bot.call_api(
            "send_group_forward_msg", group_id=str(event.group_id), messages=nodes
        )
        await forward_cmd.finish(f"✅ 合并转发已发送：{mask_result(result)}")
    except Exception as e:
        await forward_cmd.finish(f"❌ 发送失败：{e}")
