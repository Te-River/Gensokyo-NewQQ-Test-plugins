"""
put_interaction 测试插件

触发指令：交互测试
功能：调用 Gensokyo 扩展 API put_interaction 回复按钮交互。
用法：交互测试 <echo> [post_type]
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event, Message
from nonebot.params import CommandArg

interaction_test = on_command("交互测试", priority=5)


@interaction_test.handle()
async def handle_interaction_test(bot: Bot, event: Event, args: Message = CommandArg()):
    parts = args.extract_plain_text().strip().split()
    if len(parts) < 1:
        await interaction_test.finish("用法：交互测试 <echo> [post_type]，post_type: 0=成功 1=失败 2=限频 3=重复 4=无权限 5=管理员限制")
    echo = parts[0]
    post_type = parts[1] if len(parts) > 1 else "0"
    try:
        await bot.call_api("put_interaction", echo=echo, post_type=post_type)
        await interaction_test.finish(f"交互回复已发送：echo={echo} post_type={post_type}")
    except Exception as e:
        await interaction_test.finish(f"调用失败：{e}")
