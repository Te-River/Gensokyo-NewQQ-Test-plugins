from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent, Message

# 监听群聊中的 "card" 关键词
card_matcher = on_keyword({"card"}, priority=10, block=True)

@card_matcher.handle()
async def handle_fixed_card(bot: Bot, event: Event):
    if not isinstance(event, GroupMessageEvent):
        await card_matcher.finish("❌ 仅支持群聊")

    # 固定卡片内容
    title = "卡片测试标题"
    desc = "卡片测试内容"
    pic = "D:/Nonebot/Wind/data/pic/1784604627284.jpeg"   # 你的本地图片路径
    url = "www.bilibili.com"

    # 构造 CQ 码
    cq_code = f"[CQ:card,title={title},desc={desc},pic={pic},url={url}]"

    await card_matcher.send(Message(cq_code))
    await card_matcher.finish("✅ 卡片已发送")