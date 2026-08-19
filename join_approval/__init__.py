"""
入群申请转发审批插件

功能：将入群申请以 Markdown 卡片（头像 + 昵称 + 验证信息）转发到目标群，
群主/管理员点击按钮后直接审批放行/拒绝。

流程：
1. 监听 request 事件（request_type=group, sub_type=add）
2. 获取申请人头像（get_avatar）与昵称（get_stranger_info），构造
   Markdown 卡片 + 同意/拒绝按钮，发送到申请群
3. 按钮回调（join_approve 命令，Gensokyo 将按钮 data 作为消息事件上报）
4. 校验点击者是否为群主/管理员，通过后调用 set_group_add_request 审批

按钮 data 编码：join_approve <flag> <group_id> <user_id> approve|reject
"""

from typing import Optional

from nonebot import on_command, on_request
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    GroupRequestEvent,
    Message,
    MessageSegment,
)
from nonebot.log import logger
from nonebot.params import CommandArg

# 待审批申请缓存：flag -> {group_id, user_id, comment}
_pending_requests: dict[str, dict[str, str]] = {}

# 允许审批的群内身份
_ADMIN_ROLES = ("owner", "admin")

# 按钮回调参数个数：flag group_id user_id decision
_ARGS_COUNT = 4

join_request = on_request(priority=5, block=True)


@join_request.handle()
async def handle_join_request(bot: Bot, event: GroupRequestEvent) -> None:
    """监听入群申请：转发 Markdown 审批卡片到目标群"""
    if event.request_type != "group" or event.sub_type != "add":
        return

    group_id = str(event.group_id)
    user_id = str(event.user_id)
    flag = str(event.flag)
    comment = getattr(event, "comment", "") or ""

    # 防重复：同一申请只转发一次
    if flag in _pending_requests:
        return
    _pending_requests[flag] = {
        "group_id": group_id,
        "user_id": user_id,
        "comment": comment,
    }

    # 申请人头像（失败则无头像）
    avatar_url = await _fetch_avatar(bot, user_id, group_id)

    # 申请人昵称：优先取事件 username（Gensokyo 已填充），缺失回退显示 QQ 号
    nickname = getattr(event, "username", "") or f"用户 {user_id}"

    # 构造 Markdown 卡片（头像用 QQ 尺寸语法，文档-图片尺寸：必须两个都指定）
    md_lines = ["## 🙋 新的入群申请"]
    if avatar_url:
        md_lines.append(f"![头像 #100px #100px]({avatar_url})")
    md_lines.append(f"**申请人**：{nickname}")
    md_lines.append(f"**QQ**：{user_id}")
    # 验证信息为空时显示"未填写"，不隐藏该行
    md_lines.append(f"**验证信息**：{comment or '未填写'}")
    md_lines.append("")
    md_lines.append("请群主/管理员点击下方按钮审批：")
    md_content = "\n".join(md_lines)

    buttons: list[list[dict[str, str]]] = [
        [
            {
                "label": "✅ 同意",
                "data": (
                    f"join_approve {flag} {group_id} {user_id} approve"
                ),
                "style": "1",
            },
            {
                "label": "❌ 拒绝",
                "data": (
                    f"join_approve {flag} {group_id} {user_id} reject"
                ),
                "style": "2",
            },
        ]
    ]
    seg = _build_markdown_segment(md_content, buttons)

    try:
        await bot.send_group_msg(group_id=int(group_id), message=Message(seg))
        logger.info(f"入群申请已转发: flag={flag} group={group_id} user={user_id}")
    except Exception as e:  # noqa: BLE001 - 外部 API 调用容错
        logger.error(f"入群申请转发失败: flag={flag} err={e}")
        del _pending_requests[flag]


# ---- 按钮回调审批 ----
approve_cmd = on_command("join_approve", priority=5, block=True)


@approve_cmd.handle()
async def handle_approve(
    bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()
) -> None:
    """按钮回调：校验群主/管理员身份后审批入群申请"""
    parts = args.extract_plain_text().strip().split()
    if len(parts) < _ARGS_COUNT:
        await approve_cmd.finish("参数错误，请重新发起申请审批。")
    flag, group_id, user_id, decision = parts[0], parts[1], parts[2], parts[3]

    # 仅群主/管理员可审批
    role = getattr(event.sender, "role", "member")
    if role not in _ADMIN_ROLES:
        await approve_cmd.finish("仅群主/管理员可以审批入群申请。")

    # 必须在申请对应的群内操作
    if str(event.group_id) != group_id:
        await approve_cmd.finish("请在该申请对应的群内操作。")

    info = _pending_requests.get(flag)
    if info is None:
        await approve_cmd.finish("该申请已处理或不存在。")

    approve = decision == "approve"
    try:
        await bot.call_api(
            "set_group_add_request",
            group_id=group_id,
            user_id=user_id,
            flag=flag,
            approve=approve,
        )
        del _pending_requests[flag]
    except Exception as e:  # noqa: BLE001 - 外部 API 调用容错
        logger.error(f"入群申请审批失败: flag={flag} err={e}")
        await approve_cmd.finish(f"审批失败：{e}")
    # finish 抛出 FinishedException，必须放在 try 块外，否则会被 except 捕获
    result = "✅ 已同意该入群申请" if approve else "❌ 已拒绝该入群申请"
    await approve_cmd.finish(result)


# ---------- 辅助函数 ----------

async def _fetch_avatar(bot: Bot, user_id: str, group_id: str) -> str:
    """获取申请人头像直链（get_avatar 扩展 API），失败返回空串"""
    try:
        result = await bot.call_api("get_avatar", user_id=user_id, group_id=group_id)
        url = result.get("message", "")
        return url if isinstance(url, str) else ""
    except Exception as e:  # noqa: BLE001 - 外部 API 调用容错
        logger.warning(f"获取头像失败: user={user_id} err={e}")
        return ""


def _build_markdown_segment(
    content: str, buttons: Optional[list[list[dict[str, str]]]] = None
) -> MessageSegment:
    """构造 Gensokyo markdown 消息段（含内嵌键盘按钮）"""
    md_data: dict = {"markdown": {"content": content}}
    if buttons:
        rows = []
        for row_btns in buttons:
            btn_list = []
            for btn in row_btns:
                label = btn.get("label", "按钮")
                b = {
                    "id": f"btn_{abs(hash(label)) & 0xFFFF}",
                    "render_data": {
                        "label": label,
                        "visited_label": label,
                        "style": int(btn.get("style", 1)),
                    },
                    "action": {
                        "type": 2,
                        "data": btn.get("data", ""),
                        "permission": {"type": 2},
                        "unsupport_tips": "当前客户端不支持该操作，请更新后重试~",
                    },
                }
                btn_list.append(b)
            rows.append({"buttons": btn_list})
        # Gensokyo 文档推荐 keyboard.rows 简写格式（无需 content 嵌套）
        md_data["keyboard"] = {"rows": rows}
    # 对象格式：data.data.markdown + data.data.keyboard 双层嵌套（文档 39 行）
    return MessageSegment(type="markdown", data={"data": md_data})
