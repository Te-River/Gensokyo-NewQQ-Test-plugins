"""
指令面板系列 API 测试插件

触发指令：面板列表 / 面板创建 / 面板详情 / 面板修改 / 面板删除 / 面板关联
功能：调用 Gensokyo 扩展面板 API，管理机器人指令面板
（get_panel_list / create_panel / get_panel / set_panel / delete_panel /
set_panel_target，机器人最多 20 个面板）。

参数：
- scope：c2c|group|channel|dm（面板列表可指定，缺省 c2c）
- panel：面板 JSON 对象（创建时 target_type 固定为 all）
- user_openids：用户维度关联（本插件面板关联仅演示群维度 group_openids；
  用户维度用法：bot.call_api("set_panel_target", panel_id=..., op=...,
  user_openids=[...])）

用法（任意会话触发）：
  面板列表 [scope] [cursor]           → 拉取面板列表
  面板创建 <panel JSON>               → 创建面板（scope=c2c，target_type=all）
  面板详情 <panel_id>                 → 查看面板详情
  面板修改 <panel_id> <panel JSON>    → 修改面板内容
  面板删除 <panel_id>                 → 删除面板
  面板关联 <panel_id> add|del <虚拟群ID...> → 关联/解除关联目标群
"""

import json

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Message
from nonebot.params import CommandArg

_SCOPES = ("c2c", "group", "channel", "dm")

_panel_list_test = on_command("面板列表", priority=5)
_panel_create_test = on_command("面板创建", priority=5)
_panel_detail_test = on_command("面板详情", priority=5)
_panel_update_test = on_command("面板修改", priority=5)
_panel_delete_test = on_command("面板删除", priority=5)
_panel_target_test = on_command("面板关联", priority=5)


def _parse_panel(text: str):
    """解析面板 JSON，失败时返回 None。"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


@_panel_list_test.handle()
async def handle_panel_list_test(bot: Bot, args: Message = CommandArg()) -> None:
    parts = [p for p in args.extract_plain_text().strip().split() if p]
    scope, cursor = "c2c", ""
    if parts:
        if parts[0] in _SCOPES:
            scope = parts[0]
            cursor = parts[1] if len(parts) > 1 else ""
        else:
            cursor = parts[0]

    params = {"scope": scope}
    if cursor:
        params["cursor"] = cursor

    try:
        result = await bot.call_api("get_panel_list", **params)
    except Exception as e:
        await _panel_list_test.finish(f"❌ 拉取面板列表失败：{e}")

    records = result.get("records") or []
    next_cursor = result.get("next_cursor")
    is_end = result.get("is_end")

    if not records:
        lines = [f"📭 scope={scope} 暂无指令面板"]
    else:
        lines = [f"📋 scope={scope} 共 {len(records)} 个面板："]
        for r in records:
            lines.append(
                f"· [{r.get('panel_id', '')}] version={r.get('version')} "
                f"target_type={r.get('target_type')}"
            )
    if next_cursor and not is_end:
        lines.append(f"（next_cursor={next_cursor}，可继续翻页）")
    await _panel_list_test.finish("\n".join(lines))


@_panel_create_test.handle()
async def handle_panel_create_test(bot: Bot, args: Message = CommandArg()) -> None:
    arg = args.extract_plain_text().strip()
    if not arg:
        await _panel_create_test.finish("用法：面板创建 <panel JSON>")
    panel = _parse_panel(arg)
    if panel is None:
        await _panel_create_test.finish(
            f"❌ JSON 解析失败：{arg}\n用法：面板创建 <panel JSON>"
        )

    try:
        result = await bot.call_api(
            "create_panel", scope="c2c", target_type="all", panel=panel
        )
    except Exception as e:
        await _panel_create_test.finish(f"❌ 创建面板失败：{e}")
    await _panel_create_test.finish(
        f"✅ 面板创建成功，panel_id={result.get('panel_id')}（机器人最多 20 个面板）"
    )


@_panel_detail_test.handle()
async def handle_panel_detail_test(bot: Bot, args: Message = CommandArg()) -> None:
    panel_id = args.extract_plain_text().strip()
    if not panel_id:
        await _panel_detail_test.finish("用法：面板详情 <panel_id>")

    try:
        r = await bot.call_api("get_panel", panel_id=panel_id)
    except Exception as e:
        await _panel_detail_test.finish(f"❌ 查询面板失败：{e}")

    lines = [f"📋 面板 [{r.get('panel_id', '')}]："]
    lines.append(
        f"· scope={r.get('scope')} target_type={r.get('target_type')} "
        f"version={r.get('version')}"
    )
    lines.append("· panel：" + json.dumps(r.get("panel"), ensure_ascii=False))
    # target_type=specific 时返回关联的 user_openids/group_openids
    if r.get("user_openids"):
        lines.append(f"· 关联用户：{r.get('user_openids')}")
    if r.get("group_openids"):
        lines.append(f"· 关联群：{r.get('group_openids')}")
    await _panel_detail_test.finish("\n".join(lines))


@_panel_update_test.handle()
async def handle_panel_update_test(bot: Bot, args: Message = CommandArg()) -> None:
    parts = [p for p in args.extract_plain_text().strip().split(maxsplit=1) if p]
    if len(parts) < 2:
        await _panel_update_test.finish("用法：面板修改 <panel_id> <panel JSON>")
    panel_id, panel_json = parts[0], parts[1].strip()
    panel = _parse_panel(panel_json)
    if panel is None:
        await _panel_update_test.finish(
            f"❌ JSON 解析失败：{panel_json}\n用法：面板修改 <panel_id> <panel JSON>"
        )

    try:
        result = await bot.call_api("set_panel", panel_id=panel_id, panel=panel)
    except Exception as e:
        await _panel_update_test.finish(f"❌ 修改面板失败：{e}")
    await _panel_update_test.finish(
        f"✅ 面板修改成功，新 version={result.get('version')}"
    )


@_panel_delete_test.handle()
async def handle_panel_delete_test(bot: Bot, args: Message = CommandArg()) -> None:
    panel_id = args.extract_plain_text().strip()
    if not panel_id:
        await _panel_delete_test.finish("用法：面板删除 <panel_id>")

    try:
        await bot.call_api("delete_panel", panel_id=panel_id)
    except Exception as e:
        await _panel_delete_test.finish(f"❌ 删除面板失败：{e}")
    await _panel_delete_test.finish(f"✅ 面板 {panel_id} 删除成功")


@_panel_target_test.handle()
async def handle_panel_target_test(bot: Bot, args: Message = CommandArg()) -> None:
    parts = [p for p in args.extract_plain_text().strip().split() if p]
    if len(parts) < 3 or parts[1] not in ("add", "del"):
        await _panel_target_test.finish(
            "用法：面板关联 <panel_id> add|del <虚拟群ID> [虚拟群ID2 ...]"
        )
    panel_id, op, group_ids = parts[0], parts[1], parts[2:]

    try:
        await bot.call_api(
            "set_panel_target",
            panel_id=panel_id,
            op=op,
            group_openids=group_ids,
        )
    except Exception as e:
        await _panel_target_test.finish(f"❌ 面板关联操作失败：{e}")
    action = "关联" if op == "add" else "解除关联"
    await _panel_target_test.finish(
        f"✅ 面板 {panel_id} 已提交{action} {len(group_ids)} 个目标群"
    )
