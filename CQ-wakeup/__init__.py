"""
[CQ:wakeup] 测试插件

触发指令：唤醒码测试
功能：测试 [CQ:wakeup,userid=xxx] CQ 码 —— 在 send_private_msg 出站消息中
内嵌召回标记，将消息作为 C2C 互动召回（is_wakeup=true）发送给指定目标用户。

覆盖三种解析路径（string / 数组段 / TRSS map）：
1. 字符串格式: "[CQ:wakeup,userid=<目标>]<内容>" → ProcessCQWakeup 正则提取
2. 数组段格式: {"type":"wakeup","data":{"userid":"<目标>"}} → message_parser case "wakeup"
3. TRSS 格式: {"type":"wakeup","data":{"userid":"<目标>"}} → TRSS map 路径

用法（私聊或群聊触发均可）：
  唤醒码测试 @某人 内容          → 目标取 @ 段的虚拟 ID
  唤醒码测试 <OpenID> 内容        → 目标取 32 位 OpenID（字符串格式）
  唤醒码测试 <虚拟ID> 内容        → 目标取虚拟数字 ID（自动转 OpenID）
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event, Message, MessageSegment
from nonebot.params import CommandArg

wakeup_cq_test = on_command("唤醒码测试", priority=5)


def mask_id(value) -> str:
    """长 ID（OpenID/虚拟ID）脱敏：保留前 4 后 4，中间掩码。"""
    s = str(value)
    if len(s) <= 8:
        return s
    return f"{s[:4]}***{s[-4:]}"


def _extract_target(args: Message) -> tuple[str, str]:
    """从参数中提取 (目标用户, 消息内容)。@ 段优先。"""
    target = None
    for seg in args:
        if seg.type == "at":
            target = str(seg.data.get("qq", ""))
            break

    text = args.extract_plain_text().strip()

    if not target:
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return "", ""
        target, msg_text = parts[0], parts[1]
    else:
        msg_text = text

    return target, msg_text


@wakeup_cq_test.handle()
async def handle_wakeup_cq_test(bot: Bot, event: Event, args: Message = CommandArg()):
    target, msg_text = _extract_target(args)
    if not target or not msg_text:
        await wakeup_cq_test.finish(
            "用法：唤醒码测试 @某人 内容 或 唤醒码测试 <OpenID/虚拟ID> 内容"
        )

    results = []

    # 1. 字符串格式（ProcessCQWakeup 正则路径）
    try:
        await bot.send_private_msg(
            user_id=event.user_id,  # 会被 [CQ:wakeup] 中的目标覆盖
            message=f"[CQ:wakeup,userid={target}]{msg_text}",
        )
        results.append("✅ 字符串格式 [CQ:wakeup,userid=...] 已发送")
    except Exception as e:
        results.append(f"❌ 字符串格式失败: {e}")

    # 2. 数组段格式（message_parser []interface{} 路径）
    try:
        seg_msg = Message(
            [
                MessageSegment(type="wakeup", data={"userid": target}),
                MessageSegment(type="text", data={"text": msg_text}),
            ]
        )
        await bot.send_private_msg(
            user_id=event.user_id,
            message=seg_msg,
        )
        results.append("✅ 数组段格式 wakeup 段已发送")
    except Exception as e:
        results.append(f"❌ 数组段格式失败: {e}")

    # 3. TRSS map 格式（message_parser map 路径）
    try:
        trss_msg = {
            "type": "wakeup",
            "data": {"userid": target},
        }
        text_msg = {
            "type": "text",
            "data": {"text": msg_text},
        }
        await bot.send_private_msg(
            user_id=event.user_id,
            message=[trss_msg, text_msg],
        )
        results.append("✅ TRSS map 格式 wakeup 段已发送")
    except Exception as e:
        results.append(f"❌ TRSS map 格式失败: {e}")

    await wakeup_cq_test.finish(
        f"目标: {mask_id(target)}\n" + "\n".join(results)
    )
