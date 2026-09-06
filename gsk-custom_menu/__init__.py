"""
get/set_custom_menu 测试插件

触发指令：菜单查询 / 菜单设置
功能：调用 Gensokyo 扩展 API get_custom_menu 与 set_custom_menu，
查询/设置机器人自定义菜单（无群维度，机器人级别生效）。

官方校验：items ≤ 10、name ≤ 10 字符、link 必须 https://、
type ∈ switch|send_message|link|menu、sub_menu_items ≤ 5。

用法（任意会话触发）：
  菜单查询               → 查询当前菜单版本与内容
  菜单设置 <JSON>        → 设置菜单（JSON 为 menu 对象）
最小合法示例：
  菜单设置 {"items":[{"type":"link","name":"官网","link":"https://qq.com"}]}
"""

import json

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Message
from nonebot.params import CommandArg

menu_query_test = on_command("菜单查询", priority=5)
menu_set_test = on_command("菜单设置", priority=5)


@menu_query_test.handle()
async def handle_menu_query_test(bot: Bot) -> None:
    try:
        result = await bot.call_api("get_custom_menu")
    except Exception as e:
        await menu_query_test.finish(f"❌ 查询菜单失败：{e}")

    menu = result.get("menu") or {}
    version = result.get("version")
    if not menu:
        await menu_query_test.finish("📭 未设置过自定义菜单")
    await menu_query_test.finish(
        f"📋 自定义菜单（version={version}）：\n"
        + json.dumps(menu, ensure_ascii=False, indent=2)
    )


@menu_set_test.handle()
async def handle_menu_set_test(bot: Bot, args: Message = CommandArg()) -> None:
    arg = args.extract_plain_text().strip()
    if not arg:
        await menu_set_test.finish(
            "用法：菜单设置 <menu JSON>\n"
            '最小合法示例：{"items":[{"type":"link","name":"官网",'
            '"link":"https://qq.com"}]}'
        )
    try:
        menu = json.loads(arg)
    except json.JSONDecodeError as e:
        await menu_set_test.finish(
            f"❌ JSON 解析失败：{e}\n"
            "用法：菜单设置 <menu JSON>\n"
            '最小合法示例：{"items":[{"type":"link","name":"官网",'
            '"link":"https://qq.com"}]}'
        )

    try:
        result = await bot.call_api("set_custom_menu", menu=menu)
    except Exception as e:
        await menu_set_test.finish(f"❌ 设置菜单失败：{e}")
    await menu_set_test.finish(f"✅ 菜单设置成功，version={result.get('version')}")
