from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, PrivateMessageEvent, Message, MessageSegment
from nonebot.rule import Rule
from nonebot.log import logger
import asyncio


def is_private(event: PrivateMessageEvent) -> bool:
    return True


matcher = on_command("流式测试", rule=Rule(is_private))


@matcher.handle()
async def handle_flow_test(bot: Bot, event: PrivateMessageEvent):
    user_id = str(event.user_id)
    stages = [
        ("start", "这是"),
        ("mid", "这是一个流"),
        ("mid", "这是一个流式传输的"),
        ("finish", "这是一个流式传输的测试"),
    ]

    for idx, (stage_type, text) in enumerate(stages, start=1):
        try:
            stream_seg = MessageSegment("stream", {"type": stage_type, "qq": user_id})
            text_seg = MessageSegment.text(text)
            message = Message([stream_seg, text_seg])

            await bot.send_private_msg(user_id=event.user_id, message=message)
            logger.info(f"第 {idx} 段发送成功: [{stage_type}] {text}")

        except Exception as e:
            # 无论什么错误，只记录日志，不影响后续发送
            logger.error(f"第 {idx} 段发送失败 ({stage_type}): {e}")