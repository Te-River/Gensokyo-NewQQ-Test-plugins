"""
get_group_bot_state 测试插件

触发指令：群状态
功能：调用 Gensokyo 扩展 API get_group_bot_state 获取机器人在群内状态。
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent

bot_state_test = on_command("群状态", priority=5)


@bot_state_test.handle()
async def handle_bot_state_test(bot: Bot, event: GroupMessageEvent):
    try:
        result = await bot.call_api("get_group_bot_state", group_id=str(event.group_id))
        await bot_state_test.finish(f"机器人群状态：{result}")
    except Exception as e:
        await bot_state_test.finish(f"调用失败：{e}")
