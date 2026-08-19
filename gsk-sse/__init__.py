"""
send_private_msg_sse 测试插件

触发指令：SSE测试
功能：调用 Gensokyo 扩展 API send_private_msg_sse 发送 C2C SSE 私聊消息。
SSE 消息本质是流式 Markdown（msg_type=2），支持 state / prompt_keyboard /
action_button / callback_data 等 InterfaceBody 字段。

用法：SSE测试 <消息内容> [state]   （私聊场景）
示例：
  SSE测试 你好，这是SSE消息          → state=0（普通流式）
  SSE测试 你好 1                    → state=1
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, PrivateMessageEvent, Message
from nonebot.params import CommandArg

sse_test = on_command("SSE测试", priority=5)


@sse_test.handle()
async def handle_sse_test(bot: Bot, event: PrivateMessageEvent, args: Message = CommandArg()):
    parts = args.extract_plain_text().strip().split(maxsplit=1)
    if not parts:
        await sse_test.finish("用法：SSE测试 <消息内容> [state]，例如：SSE测试 你好 1")
    content = parts[0]
    state = 0
    if len(parts) > 1 and parts[1].isdigit():
        state = int(parts[1])

    # InterfaceBody 结构：content / state / prompt_keyboard / action_button / callback_data
    body = {
        "content": content,
        "state": state,
        "prompt_keyboard": ["👍 收到", "👎 忽略"],
    }
    try:
        await bot.call_api("send_private_msg_sse", user_id=str(event.user_id), message=body)
        await sse_test.finish(f"SSE 消息已发送：{content}（state={state}）")
    except Exception as e:
        await sse_test.finish(f"调用失败：{e}")
