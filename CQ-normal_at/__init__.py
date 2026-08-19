from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment
from nonebot.typing import T_State

# 定义指令触发器，用户发送“普通at”即可触发
at_cmd = on_command("普通at", priority=10, block=True)

@at_cmd.handle()
async def handle_at(bot: Bot, event: Event, state: T_State):
    # 获取触发者的 QQ 号（群聊或私聊都适用）
    user_id = event.get_user_id()

    # 构造普通文本下的 CQ:at 码
    at_cq = f"[CQ:at,qq={user_id}]"

    # 回复消息，可以直接将 CQ 码放在字符串中
    await at_cmd.finish(f"{at_cq} ")