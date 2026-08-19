import json
import base64
import re
import logging
from nonebot import on_notice
from nonebot.adapters.onebot.v11 import Bot, GroupIncreaseNoticeEvent, GroupDecreaseNoticeEvent, Message

# ===================== 日志 =====================
logger = logging.getLogger("nonebot.plugin.member_notice")

# ===================== 注册通知处理器 =====================
member_handler = on_notice(priority=1, block=False)


# ===================== 辅助函数：构建 Markdown CQ 码 =====================
def build_markdown_cq(user_id: int, cq_type: str = "add") -> str:
    """
    构建自定义 Markdown 卡片的 CQ 码（非模板）
    :param user_id: 虚拟用户 ID
    :param cq_type: 'add' 或 'remove'
    """
    if cq_type == "add":
        content = "## 新成员加入"
    else:
        content = "## 成员离开"

    md_payload = {
        "markdown": {"content": content},
        "keyboard": {
            "rows": [
                {
                    "buttons": [
                        {
                            "id": "welcome_ok",
                            "render_data": {
                                "label": "✅ 了解",
                                "visited_label": "已了解"
                            },
                            "action": {
                                "type": 2,
                                "permission": {"type": 2},
                                "data": "已阅",
                                "unsupport_tips": "请升级QQ版本"
                            }
                        }
                    ]
                }
            ]
        }
    }

    json_str = json.dumps(md_payload, ensure_ascii=False)
    b64_data = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    return f"[CQ:markdown,data={b64_data}]"


# ===================== 主处理逻辑 =====================
@member_handler.handle()
async def handle_member_cq(bot: Bot, event: GroupIncreaseNoticeEvent | GroupDecreaseNoticeEvent):
    """
    处理群成员增减 notice 事件，发送欢迎/告别 Markdown 卡片
    """
    # 从 message 字段提取 [CQ:member] 的 type 参数
    raw_msg = getattr(event, 'message', '') or ''
    if not isinstance(raw_msg, str):
        raw_msg = str(raw_msg)

    # 确定是入群还是退群
    if isinstance(event, GroupIncreaseNoticeEvent):
        cq_type = "add"
    else:
        cq_type = "remove"

    if cq_type == "add":
        at_cq = f"[CQ:at,qq={event.user_id}]"
        md_cq = build_markdown_cq(event.user_id, "add")
        reply_msg = Message(raw_msg + at_cq + md_cq)

    elif cq_type == "remove":
        at_cq = f"[CQ:at,qq={event.user_id}]"
        md_cq = build_markdown_cq(event.user_id, "remove")
        reply_msg = Message(raw_msg + at_cq + md_cq)

    else:
        logger.warning(f"未知的事件类型")
        return

    await bot.send_group_msg(group_id=event.group_id, message=reply_msg)
    logger.info(f"已发送回复消息，group={event.group_id}, type={cq_type}")