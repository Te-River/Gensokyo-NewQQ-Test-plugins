import json
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event, Message, MessageSegment
from nonebot.params import CommandArg

embed_cmd = on_command("embed", aliases={"发送embed"}, priority=5, block=True)

@embed_cmd.handle()
async def handle_embed(bot: Bot, event: Event, args: Message = CommandArg()):
    raw_text = args.extract_plain_text().strip()

    # 没有参数 -> 发送示例 embed
    if not raw_text:
        embed_obj = {
            "title": "Embed 示例",
            "description": "这是一个 Gensokyo Embed 卡片消息",
            "prompt": "Embed 卡片",          # 必填
            "thumbnail": {"url": "https://q.qlogo.cn/qqapp/1103188784/xxxxxxxxx/640"},
            "fields": [
                {"name": "项目", "value": "Gensokyo-NoneBot2"},
                {"name": "版本", "value": "1.0.0"},
                {"name": "msg_type", "value": "4"}
            ]
        }
    else:
        # 尝试解析 JSON
        try:
            embed_obj = json.loads(raw_text)
        except json.JSONDecodeError:
            await embed_cmd.finish("参数不是有效的 JSON，请检查格式。")
        if "prompt" not in embed_obj:
            await embed_cmd.finish("缺少必填字段 'prompt'，Embed 消息必须包含 prompt。")

    # 构造符合 Gensokyo 格式的 segment：data 字段内再包一层 data
    seg = MessageSegment("embed", {"data": embed_obj})

    try:
        # 发送消息（自动适配群聊/私聊）
        await bot.send(event, Message(seg))
    except Exception as e:
        await embed_cmd.finish(f"发送 Embed 失败：{e}")