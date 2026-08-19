"""
lib_msg.py —— 统一消息构建与发送模块（硬编码 Markdown 模式）
- USE_MARKDOWN = True  → Gensokyo Markdown（### 标题 + > 引用内容 + 蓝色按钮）
- 按钮仅支持扁平键名格式：{"render_data.label": "同意", "action.data": "指令"}
- 默认值：action.type=2, action.permission.type=2, action.reply=False, render_data.style=1
- 按钮优先级（从左往右，从上到下）：舞萌帮助、查看绑定、预览用户、同步成绩、查看队列
- 舞萌帮助消息自身按钮布局：舞萌帮助 设置类型1 设置类型2 / 查看绑定 查看队列 预览用户 / 同步成绩
- 扩展帮助在 Markdown 下直接拼接 ### 标题 + > 格式；非 Markdown 下自动转换为纯文本缩进风格
"""

# ==================== 按钮构建说明 ====================
# 所有按钮均使用扁平键名字典定义，格式如下：
#   {"render_data.label": "文字", "render_data.visited_label": "点击后文字", ...}
# 最简形式只需提供 label 和 data：
#   {"render_data.label": "按钮文字", "action.data": "指令或URL"}

# 完整字段列表（均为扁平键名）：
# ┌──────────────────────────────┬──────────┬───────────────────────────────┐
# │ 键名                          │ 默认值    │ 说明                          │
# ├──────────────────────────────┼──────────┼───────────────────────────────┤
# │ render_data.label            │ 必填      │ 按钮上显示的文字               │
# │ render_data.visited_label    │ 同 label │ 点击后显示的文字               │
# │ render_data.style            │ 1         │ 0 灰色线框, 1 蓝色线框        │
# │ action.data                  │ 必填      │ 指令文本或跳转 URL            │
# │ action.type                  │ 2         │ 0 跳转, 1 回调, 2 指令       │
# │ action.permission.type       │ 2         │ 0 指定用户, 1 仅管理者, 2 所有人 │
# │ action.permission.specify_user_ids │ []  │ True 表示仅当前用户，或直接填列表 │
# │ action.reply                 │ False     │ 指令是否带引用回复 (仅 type=2) │
# │ action.enter                 │ False     │ 点击后直接发送 data (仅 type=2) │
# │ action.anchor                │ 0         │ 1 唤起选图器 (仅 type=2)       │
# │ action.unsupport_tips        │ 默认提示   │ 客户端不支持时的 toast          │
# └──────────────────────────────┴──────────┴───────────────────────────────┘

# 常见示例：
# 1. 普通指令按钮（蓝色，所有人，不带引用）：
#    {"render_data.label": "同步成绩", "action.data": "同步成绩"}
#
# 2. 带引用回复的指令按钮：
#    {"render_data.label": "同步成绩", "action.data": "同步成绩", "action.reply": True}
#
# 3. 跳转按钮（打开网页）：
#    {"render_data.label": "官网", "action.data": "https://example.com", "action.type": 0}
#
# 4. 仅当前用户可点击的指令按钮：
#    {"render_data.label": "个人", "action.data": "个人信息", "action.permission.specify_user_ids": True}
#
# 5. 灰色按钮 + 跳转 + 仅自己可见：
#    {"render_data.label": "打开", "action.data": url, "action.type": 0,
#     "render_data.style": 0, "action.permission.specify_user_ids": True}
#
# 注：所有字段均为可选，未提供的字段将自动使用默认值。
#     specify_user_ids 为 True 时，会自动替换为当前用户 ID。


import asyncio
import os
from typing import Union, Optional, List, Dict, Any
from nonebot import get_bot
from nonebot.adapters.onebot.v11 import (
    Message,
    MessageEvent,
    GroupMessageEvent,
    MessageSegment,
)
from nonebot.log import logger

# ==================== 硬编码开关 ====================
USE_MARKDOWN = True  # True 开启 Gensokyo Markdown 模式，False 使用普通文本消息

# ==================== 按钮定义类型 ====================
ButtonDef = Dict[str, Any]

# ==================== 基础发送工具 ====================
def build_mention(event: MessageEvent) -> MessageSegment:
    """生成 @用户 消息段，Markdown 模式下返回空文本段"""
    if isinstance(event, GroupMessageEvent):
        if not USE_MARKDOWN:
            return MessageSegment.at(event.user_id)
    return MessageSegment.text("")

def build_text(text: str) -> MessageSegment:
    return MessageSegment.text(text)

def build_image(file: Union[str, bytes]) -> MessageSegment:
    if isinstance(file, bytes):
        return MessageSegment.image(file)
    return MessageSegment.image(file)

def build_message_with_mention(event: MessageEvent, text: str) -> Message:
    """构建带 @ 的文本消息（仅普通文本，Markdown 模式下不添加 @）"""
    if isinstance(event, GroupMessageEvent):
        if USE_MARKDOWN:
            return Message(MessageSegment.text(text))
        else:
            return Message(build_mention(event)) + Message(build_text("\n" + text))
    return Message(build_text(text))

# ==================== Gensokyo Markdown 构造 ====================

def _normalize_button(btn: Dict[str, Any]) -> Dict[str, Any]:
    """
    将扁平键名的按钮字典转换为标准的嵌套字典。
    例如 {"render_data.label": "文字"} -> {"render_data": {"label": "文字"}}
    """
    nested: Dict[str, Any] = {}
    for key, value in btn.items():
        parts = key.split(".")
        current = nested
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    return nested

def _build_button_row(buttons: List[ButtonDef]) -> dict:
    """
    将按钮 dict 列表补全默认值并转换为 Gensokyo 行格式。
    所有按钮必须使用扁平键名定义。
    """
    btn_list = []
    for btn in buttons:
        # 先转换为嵌套结构，然后补全默认值
        b = _normalize_button(btn)

        # ---- render_data ----
        rd = b.setdefault("render_data", {})
        label = rd.get("label", "按钮")
        rd.setdefault("visited_label", label)
        rd.setdefault("style", 1)

        # ---- action ----
        action = b.setdefault("action", {})
        action.setdefault("type", 2)
        # permission.type 始终默认为 2（所有人）
        action.setdefault("permission", {})
        perm = action["permission"]
        perm.setdefault("type", 2)
        if perm.get("specify_user_ids") is True:
            perm["specify_user_ids"] = ["__USER_ID__"]
        elif "specify_user_ids" not in perm:
            # 未显式指定白名单时，不添加 specify_user_ids 字段
            pass
        action.setdefault("data", "")
        action.setdefault("unsupport_tips", "欸，当前客户端不支持该文本捏，更新一下试试吧~")

        # 指令按钮专属字段
        if action["type"] == 2:
            action.setdefault("reply", False)
            action.setdefault("enter", False)
            action.setdefault("anchor", 0)
        elif action["type"] == 0:          # 跳转按钮需要 enter=true，移除 reply
            action["enter"] = True
            action.pop("reply", None)

        # ---- id ----
        if "id" not in b:
            b["id"] = f"btn_{hash(label) & 0xffff}"

        btn_list.append(b)
    return {"buttons": btn_list}

def _build_keyboard_rows(buttons_config: List[List[ButtonDef]]) -> dict:
    rows = []
    for row_btns in buttons_config:
        rows.append(_build_button_row(row_btns))
    return {"content": {"rows": rows}}

def _build_markdown_segment(content: str, buttons_config: Optional[List[List[ButtonDef]]] = None) -> MessageSegment:
    md_data = {"markdown": {"content": content}}
    if buttons_config:
        md_data["keyboard"] = _build_keyboard_rows(buttons_config)
    return MessageSegment(type="markdown", data={"data": md_data})

def _md_msg(text: str) -> Message:
    return Message(_build_markdown_segment(text))

# ==================== 统一发送接口 ====================
async def send_message(
    event: MessageEvent,
    text_or_msg: Union[str, Message, MessageSegment],
    at: bool = True,
) -> bool:
    try:
        bot = get_bot()
        if isinstance(text_or_msg, str):
            if at:
                msg = build_message_with_mention(event, text_or_msg)
            else:
                msg = Message(build_text(text_or_msg))
        elif isinstance(text_or_msg, MessageSegment):
            msg = Message(text_or_msg)
        else:
            msg = text_or_msg

        # 自动替换 specify_user_ids 占位符
        if isinstance(event, GroupMessageEvent) and isinstance(msg, Message):
            for seg in msg:
                if seg.type == "markdown":
                    md_data = seg.data.get("data")
                    if isinstance(md_data, dict) and "keyboard" in md_data:
                        rows = md_data["keyboard"].get("content", {}).get("rows", [])
                        for row in rows:
                            for btn in row.get("buttons", []):
                                perm = btn.get("action", {}).get("permission", {})
                                if perm.get("specify_user_ids") == ["__USER_ID__"]:
                                    perm["specify_user_ids"] = [str(event.user_id)]
                    break

        from .lib_error_tracker import get_error_tracker
        tracker = get_error_tracker()
        content = str(msg) if isinstance(msg, Message) else str(text_or_msg)
        tracker.add_bot_message(event, content)

        await bot.send(event, msg)
        return True
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        return False

async def send_private_msg(user_id: Union[int, str], text: str) -> bool:
    try:
        bot = get_bot()
        msg = Message(build_text(text))
        await bot.send_private_msg(user_id=int(user_id), message=msg)
        return True
    except Exception as e:
        logger.error(f"发送私聊消息给 {user_id} 失败: {e}")
        return False

async def send_image(event: MessageEvent, file: Union[str, bytes]) -> bool:
    try:
        msg = Message(build_image(file))
        bot = get_bot()
        await bot.send(event, msg)
        return True
    except Exception as e:
        logger.error(f"发送图片失败: {e}")
        return False

async def delete_message(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    try:
        bot = get_bot()
        await bot.delete_msg(message_id=event.message_id)
        return True
    except Exception as e:
        logger.debug(f"删除消息失败: {e}")
        return False

# ==================== 辅助函数 ====================
def _auto_msg(
    plain_text: str,
    md_text: str = None,
    buttons: Optional[List[ButtonDef]] = None
) -> Union[str, Message]:
    """统一消息构建：Markdown 下自动排序并注入默认按钮，非 Markdown 返回纯文本"""
    if USE_MARKDOWN:
        content = md_text if md_text is not None else plain_text
        if buttons is not None:
            # _sorted_markdown_segment 接收扁平额外按钮列表，自动补全并排序
            return _sorted_markdown_segment(content, buttons)
        return _md_msg(content)
    else:
        return plain_text

def _convert_md_ext_to_plain(ext_text: str) -> str:
    """将 Markdown 格式的扩展帮助文本转换为纯文本格式（去掉 ### 和 >）"""
    lines = ext_text.splitlines()
    result_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("### "):
            result_lines.append(stripped[4:])
        elif stripped.startswith("> "):
            result_lines.append("  " + stripped[2:])
        elif stripped == ">":
            result_lines.append("")
        else:
            result_lines.append(stripped)
    return "\n".join(result_lines)

def _quote_lines(text: str) -> str:
    """将多行文本的每一行前面加上 > ，空行保留 >"""
    lines = text.splitlines()
    return "\n".join(f"> {line}" if line.strip() else ">" for line in lines)

# 按钮排序基准：按全局优先级排序
BUTTON_PRIORITY = ["舞萌帮助", "查看绑定", "预览用户", "同步成绩", "查看队列"]

def _sort_buttons(buttons: List[ButtonDef]) -> List[ButtonDef]:
    """按全局优先级排序按钮，未在优先级列表中的放在最后"""
    priority_dict = {name: i for i, name in enumerate(BUTTON_PRIORITY)}
    return sorted(buttons, key=lambda x: priority_dict.get(
        x.get("render_data", {}).get("label", ""), len(BUTTON_PRIORITY)))

def _make_button_rows(buttons: List[ButtonDef], max_per_row=3) -> List[List[ButtonDef]]:
    """将按钮列表按 max_per_row 分组，每组一行"""
    if not buttons:
        return []
    rows = []
    for i in range(0, len(buttons), max_per_row):
        rows.append(buttons[i:i+max_per_row])
    return rows

def _sorted_markdown_segment(md_text: str, extra_buttons: List[ButtonDef] = None) -> Message:
    """自动合并必需按钮（舞萌帮助等）并排序，生成 Markdown 消息段"""
    # 将扁平键名转换为嵌套结构
    all_buttons = [_normalize_button(b) for b in (extra_buttons or [])]
    if not any(b.get("render_data", {}).get("label") == "舞萌帮助" for b in all_buttons):
        all_buttons.insert(0, _normalize_button({"render_data.label": "舞萌帮助", "action.data": "舞萌帮助"}))
    all_buttons = _sort_buttons(all_buttons)
    rows = _make_button_rows(all_buttons)
    return Message(_build_markdown_segment(md_text, rows))