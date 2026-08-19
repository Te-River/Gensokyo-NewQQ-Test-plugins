"""
join_approval_strategy 系列 API 测试插件

触发指令：策略创建 / 策略列表 / 策略修改 / 策略白名单 / 策略执行 / 策略删除
功能：调用 Gensokyo 扩展 API 管理入群自动审批策略
（join_approval_strategy_create / list / update / whitelist / execute / delete）。
[CQ:set_group,action=strategy_execute/strategy_delete] 的 CQ 码形式已在
CQ-set_group 插件覆盖，本插件补齐 API 形式。

参数（对齐 handler 实现）：
- create:  group_openids/group_ids 二选一必填, is_enable(on/off 默认 on),
           expire_at(RFC3339 可选), remark(可选)
- list:    cursor(可选分页游标), limit(可选单页数量 默认20 最大100)
- update:  strategy_id 必填, is_enable/expire_at/remark 可选,
           op(add/del)+group_openids/group_ids 增删关联群
- whitelist: strategy_id 必填, op(add/del) 必填, whitelist_users(QQ号列表)
- execute/delete: strategy_id 必填

用法：
  策略创建 <群OpenID> [remark]              → group_openids 创建
  策略创建 群号:<群号> [remark]              → group_ids 创建（多个用逗号分隔）
  策略列表 [limit]                          → 查询策略列表
  策略修改 <strategy_id> [on|off] [remark]  → 修改启用状态/备注
  策略白名单 <strategy_id> add|del <QQ号,QQ号,...>
  策略执行 <strategy_id>
  策略删除 <strategy_id>
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.params import CommandArg

# ---------- 脱敏辅助 ----------

def mask_id(value) -> str:
    """长 ID（OpenID/虚拟ID/strategy_id）脱敏：保留前 4 后 4，中间掩码。"""
    s = str(value)
    if len(s) <= 8:
        return s
    return f"{s[:4]}***{s[-4:]}"


def mask_result(result) -> str:
    """对 API 返回 JSON 做脱敏（递归替换长 ID 字段值）。"""
    import json

    def _walk(obj):
        if isinstance(obj, dict):
            return {k: _walk(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_walk(v) for v in obj]
        if isinstance(obj, str):
            # 32 位 OpenID / strategy_id 或 9 位以上数字 ID 视为敏感
            if len(obj) >= 32 or (obj.isdigit() and len(obj) >= 9):
                return mask_id(obj)
            return obj
        return obj

    try:
        return json.dumps(_walk(json.loads(result)), ensure_ascii=False)
    except Exception:
        return mask_id(result)

# ── 创建策略 ─────────────────────────────────
strategy_create = on_command("策略创建", priority=5)


@strategy_create.handle()
async def handle_strategy_create(bot: Bot, event: Event, args: Message = CommandArg()):
    parts = args.extract_plain_text().strip().split()
    if not parts:
        await strategy_create.finish(
            "用法：策略创建 <群OpenID> [remark] 或 策略创建 群号:<群号> [remark]"
        )
    target = parts[0]
    remark = " ".join(parts[1:]) if len(parts) > 1 else ""

    params: dict = {"is_enable": "on"}
    if remark:
        params["remark"] = remark
    if target.startswith("群号:"):
        group_ids = [int(g) for g in target[3:].split(",") if g.isdigit()]
        if not group_ids:
            await strategy_create.finish("群号格式错误：策略创建 群号:123456,789012")
        params["group_ids"] = group_ids
    else:
        params["group_openids"] = [g.strip() for g in target.split(",") if g.strip()]

    try:
        result = await bot.call_api("join_approval_strategy_create", **params)
        await strategy_create.finish(f"✅ 策略已创建：{mask_result(result)}")
    except Exception as e:
        await strategy_create.finish(f"❌ 创建失败：{e}")


# ── 查询策略列表 ─────────────────────────────
strategy_list = on_command("策略列表", priority=5)


@strategy_list.handle()
async def handle_strategy_list(bot: Bot, event: Event, args: Message = CommandArg()):
    arg = args.extract_plain_text().strip()
    params: dict = {}
    if arg.isdigit():
        params["limit"] = int(arg)
    try:
        result = await bot.call_api("join_approval_strategy_list", **params)
        await strategy_list.finish(f"策略列表：{mask_result(result)}")
    except Exception as e:
        await strategy_list.finish(f"❌ 查询失败：{e}")


# ── 修改策略 ─────────────────────────────────
strategy_update = on_command("策略修改", priority=5)


@strategy_update.handle()
async def handle_strategy_update(bot: Bot, event: Event, args: Message = CommandArg()):
    parts = args.extract_plain_text().strip().split()
    if not parts:
        await strategy_update.finish("用法：策略修改 <strategy_id> [on|off] [remark]")
    sid = parts[0]
    params: dict = {}
    if len(parts) > 1:
        enable = parts[1].lower()
        if enable in ("on", "off"):
            params["is_enable"] = enable
        else:
            await strategy_update.finish("启用状态只接受 on/off")
    if len(parts) > 2:
        params["remark"] = " ".join(parts[2:])
    try:
        result = await bot.call_api(
            "join_approval_strategy_update", strategy_id=sid, **params
        )
        await strategy_update.finish(f"✅ 策略已修改：{mask_result(result)}")
    except Exception as e:
        await strategy_update.finish(f"❌ 修改失败：{e}")


# ── 修改白名单 ───────────────────────────────
strategy_whitelist = on_command("策略白名单", priority=5)


@strategy_whitelist.handle()
async def handle_strategy_whitelist(bot: Bot, event: Event, args: Message = CommandArg()):
    parts = args.extract_plain_text().strip().split()
    if len(parts) < 3:
        await strategy_whitelist.finish(
            "用法：策略白名单 <strategy_id> add|del <QQ号,QQ号,...>"
        )
    sid, op = parts[0], parts[1].lower()
    if op not in ("add", "del"):
        await strategy_whitelist.finish("操作只接受 add/del")
    whitelist_users = [u for u in parts[2].split(",") if u.strip()]
    try:
        result = await bot.call_api(
            "join_approval_strategy_whitelist",
            strategy_id=sid,
            op=op,
            whitelist_users=whitelist_users,
        )
        await strategy_whitelist.finish(f"✅ 白名单已{op}：{mask_result(result)}")
    except Exception as e:
        await strategy_whitelist.finish(f"❌ 白名单修改失败：{e}")


# ── 执行策略 ─────────────────────────────────
strategy_execute = on_command("策略执行API", priority=5)


@strategy_execute.handle()
async def handle_strategy_execute(bot: Bot, event: Event, args: Message = CommandArg()):
    sid = args.extract_plain_text().strip()
    if not sid:
        await strategy_execute.finish("用法：策略执行API <strategy_id>")
    try:
        result = await bot.call_api("join_approval_strategy_execute", strategy_id=sid)
        await strategy_execute.finish(f"✅ 策略已执行（异步约10分钟）：{mask_result(result)}")
    except Exception as e:
        await strategy_execute.finish(f"❌ 执行失败：{e}")


# ── 删除策略 ─────────────────────────────────
strategy_delete = on_command("策略删除API", priority=5)


@strategy_delete.handle()
async def handle_strategy_delete(bot: Bot, event: Event, args: Message = CommandArg()):
    sid = args.extract_plain_text().strip()
    if not sid:
        await strategy_delete.finish("用法：策略删除API <strategy_id>")
    try:
        result = await bot.call_api("join_approval_strategy_delete", strategy_id=sid)
        await strategy_delete.finish(f"✅ 策略已删除：{mask_result(result)}")
    except Exception as e:
        await strategy_delete.finish(f"❌ 删除失败：{e}")
