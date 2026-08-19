"""
get_robot_share_link 测试插件

触发指令：分享链接
功能：调用 Gensokyo 扩展 API get_robot_share_link 获取机器人资料页分享链接。
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event

share_link_test = on_command("分享链接", priority=5)


@share_link_test.handle()
async def handle_share_link_test(bot: Bot, event: Event):
    try:
        result = await bot.call_api("get_robot_share_link")
        url = result.get("url") if isinstance(result, dict) else result
        await share_link_test.finish(f"机器人分享链接：{url}")
    except Exception as e:
        await share_link_test.finish(f"调用失败：{e}")
