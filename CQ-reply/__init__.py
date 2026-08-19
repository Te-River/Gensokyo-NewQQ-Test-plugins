"""
引用插件 - 演示 Gensokyo-NewQQ 的 message_reference 引用功能
触发命令: 引用 [自定义回复内容]
特性: 回复的消息会引用用户触发指令的原消息，并以 Markdown + 按钮形式发送
"""

import base64
import json

from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent
from nonebot.exception import FinishedException
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="引用回复",
    description="引用用户的消息进行回复，展示 CQ:reply 转 message_reference 功能，支持 Markdown + 按钮",
    usage="发送：引用 [可选回复内容]  # 机器人会引用你的消息并回复对应内容",
    type="application",
    homepage="https://github.com/Te-River/Gensokyo-NewQQ",
    supported_adapters={"~onebot.v11"},
)

quote_cmd = on_command("引用", aliases={"quote"}, priority=5, block=True)


def build_markdown_content(reply_text: str) -> str:
    """构造 [CQ:markdown] base64 CQ 码（纯 MD 内容，不含 keyboard）。"""
    md_payload = {
        "markdown": {
            "content": f"## 引用回复\n\n{reply_text}",
        },
    }
    b64 = base64.b64encode(
        json.dumps(md_payload, ensure_ascii=False).encode("utf-8")
    ).decode("ascii")
    return f"[CQ:markdown,data=base64://{b64}]"


def build_keyboard_cq() -> str:
    """构造独立 [CQ:keyboard] base64 CQ 码（按钮）。

    Gensokyo 的 parseKeyboardData 支持结构：{"content":{"rows":[...]}}
    """
    kb_payload = {
        "content": {
            "rows": [
                {
                    "buttons": [
                        {
                            "id": "btn_reply_ok",
                            "render_data": {"label": "👍 收到", "style": 1},
                            "action": {
                                "type": 2,  # 指令按钮：自动在输入框插入 @bot data
                                "permission": {"type": 2},  # 所有人可点
                                "data": "/收到",
                            },
                        }
                    ]
                }
            ]
        }
    }
    b64 = base64.b64encode(
        json.dumps(kb_payload, ensure_ascii=False).encode("utf-8")
    ).decode("ascii")
    return f"[CQ:keyboard,data=base64://{b64}]"


@quote_cmd.handle()
async def handle_quote(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    # 获取用户输入的回复内容（去除命令本身）
    reply_text = args.extract_plain_text().strip()
    if not reply_text:
        reply_text = "已引用您的消息（无附加内容）"

    # 获取当前消息的 message_id（用于构造 reply 引用）
    msg_id = str(event.message_id)

    # 构造带引用的 Markdown + 独立 [CQ:keyboard] 按钮 回复消息
    # Gensokyo-NewQQ 会将 [CQ:reply,id=...] 自动转换为 message_reference 字段
    quoted_message = Message(
        f"[CQ:reply,id={msg_id}]{build_markdown_content(reply_text)}{build_keyboard_cq()}"
    )

    # 注意：finish() 成功发送后会抛出 FinishedException 作为正常控制流终止当前 handler，
    # 必须放行它，否则会被误判为发送失败并补发一条错误消息。
    try:
        await quote_cmd.send(quoted_message)
        logger.info(f"引用回复成功 | 用户: {event.user_id} | 被引用消息ID: {msg_id}")
    except FinishedException:
        raise
    except Exception as e:
        logger.error(f"引用回复发送失败: {e}")
        await quote_cmd.finish("引用消息失败，请稍后再试。")
    await quote_cmd.finish()
