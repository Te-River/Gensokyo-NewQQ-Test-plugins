from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.typing import T_State
from .lib_msg import _build_markdown_segment, USE_MARKDOWN

# 存储每个用户最近一次检测的 at 虚拟ID列表（供按钮回调使用）
at_list_storage: dict[str, list[str]] = {}

# ---- 主命令：at检测 ----
at_check = on_command("at检测", priority=5, block=True)

@at_check.handle()
async def handle_at_check(bot: Bot, event: GroupMessageEvent, state: T_State):
    message = event.get_message()
    at_segments = [seg for seg in message if seg.type == "at"]
    at_qqs = [seg.data.get("qq", "") for seg in at_segments if seg.data.get("qq")]

    # 存储虚拟ID列表
    key = f"{event.group_id}_{event.user_id}"
    at_list_storage[key] = at_qqs

    # 构造检测结果文本
    lines = []
    to_me = getattr(event, "to_me", None)
    if to_me is True:
        lines.append("✅ 消息 @ 了机器人")
    elif to_me is False:
        lines.append("❌ 消息未 @ 机器人")
    else:
        lines.append("⚠️ 当前不是群聊消息")

    if at_qqs:
        lines.append(f"👥 共 {len(at_qqs)} 个 @")
    else:
        lines.append("👤 没有 @ 任何人")

    if USE_MARKDOWN:
        # 构建 Markdown 内容，直接嵌入 [CQ:at,qq=...] 实现蓝色 @ 渲染
        md_parts = ["### AT 检测结果"]
        md_parts.extend(f"> {line}" for line in lines)

        if at_qqs:
            md_parts.append("> ")
            for idx, qq in enumerate(at_qqs, start=1):
                # Markdown 内支持 [CQ:at] 自动转换为 <qqbot-at-user> 标签
                md_parts.append(f"> {idx}. [CQ:at,qq={qq}]")

        md_content = "\n".join(md_parts)

        # 构造数字按钮（每行最多 3 个）
        button_rows = []
        row_buttons = []
        for idx in range(1, len(at_qqs) + 1):
            row_buttons.append({
                "render_data.label": str(idx),
                "action.data": f"at_reply {idx}",
                "action.reply": False,
            })
        for i in range(0, len(row_buttons), 3):
            button_rows.append(row_buttons[i:i+3])

        md_seg = _build_markdown_segment(md_content, button_rows)
        await bot.send(event, Message(md_seg))
    else:
        # 纯文本模式（无按钮，简单列表）
        text_lines = ["AT 检测结果"]
        text_lines.extend(lines)
        if at_qqs:
            text_lines.append("")
            for idx, qq in enumerate(at_qqs, start=1):
                text_lines.append(f"{idx}. {qq}")
        await bot.send(event, Message(MessageSegment.text("\n".join(text_lines))))


# ---- 按钮回调命令：at_reply ----
at_reply = on_command("at_reply", priority=5, block=True)

@at_reply.handle()
async def handle_at_reply(bot: Bot, event: GroupMessageEvent,
                          args: Message = CommandArg()):
    arg_text = args.extract_plain_text().strip()
    if not arg_text.isdigit():
        await at_reply.finish("参数错误，请重新检测。")
    idx = int(arg_text)

    key = f"{event.group_id}_{event.user_id}"
    at_qqs = at_list_storage.get(key, [])
    if not at_qqs:
        await at_reply.finish("未找到检测记录，请先发送 /at检测。")
    if idx < 1 or idx > len(at_qqs):
        await at_reply.finish(f"序号超出范围，当前有 {len(at_qqs)} 个 @。")

    target_qq = at_qqs[idx - 1]

    if USE_MARKDOWN:
        # 用 Markdown 卡片发送，直接嵌入 [CQ:at] 渲染蓝色 @
        md_content = f"[CQ:at,qq={target_qq}]"
        # 不需要额外按钮，传空列表
        md_seg = _build_markdown_segment(md_content, [])
        await bot.send(event, Message(md_seg))
    else:
        await bot.send(event, Message(MessageSegment.at(target_qq)))