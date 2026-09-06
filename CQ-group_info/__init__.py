"""
[CQ:group_info] 群信息占位 CQ 码测试插件

出站单向，Gensokyo 会将 CQ 码替换为实际群信息后发送。
需 Gensokyo 端 cq_parse_mode: new 才生效，legacy/shadow 下该码会原文发出。

四种 field：
- name         → 群名称
- memo         → 群公告/简介
- member_count → 群成员数
- all          → 以上全部

fallback：API 查询失败时用该文本替换整个 CQ 码（缺省无替换文本）。
group_id：可选跨群，缺省回退当前群。

用法（群聊触发）：
  群信息测试                        → 查询群名称
  群信息测试 memo                   → 查询群简介
  群信息测试 member_count           → 查询群成员数
  群信息测试 all                    → 查询全部信息
  群信息测试 name 获取失败          → 指定失败时替换文本
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message
from nonebot.params import CommandArg

_FIELDS = ("name", "memo", "member_count", "all")

group_info_test = on_command("群信息测试", priority=5)


@group_info_test.handle()
async def handle_group_info_test(
    event: GroupMessageEvent, args: Message = CommandArg()
) -> None:
    arg = args.extract_plain_text().strip()
    field, fallback = "name", ""
    if arg:
        parts = arg.split(maxsplit=1)
        if parts[0] in _FIELDS:
            field = parts[0]
            fallback = parts[1].strip() if len(parts) > 1 else ""
        else:
            fallback = arg

    cq = f"[CQ:group_info,field={field}"
    if fallback:
        cq += f",fallback={fallback}"
    cq += f",group_id={event.group_id}]"
    note = (
        f" 正在查询 {field}"
        "（该码需 Gensokyo cq_parse_mode=new，legacy/shadow 会原文发出）"
    )
    await group_info_test.finish(Message(cq) + note)
