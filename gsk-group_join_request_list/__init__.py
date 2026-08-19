"""
get_group_join_request_list 测试插件

触发指令：申请列表
功能：调用 Gensokyo 扩展 API get_group_join_request_list 拉取 q群 的
入群申请列表。返回的 group_id/user_id/flag 可直接回传
set_group_add_request 审批（与入站 request 事件一致）。

参数：
- group_id 必填（当前群，自动获取；支持虚拟群ID或群OpenID）
- next_index 可选分页游标（不填从第一页开始）

用法（群聊触发）：
  申请列表                → 拉取第一页申请
  申请列表 <next_index>   → 从指定游标继续拉取
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.params import CommandArg

join_request_list_test = on_command("申请列表", priority=5)


def mask_id(value) -> str:
    """长 ID（OpenID/虚拟ID/flag）脱敏：保留前 4 后 4，中间掩码。"""
    s = str(value)
    if len(s) <= 8:
        return s
    return f"{s[:4]}***{s[-4:]}"


@join_request_list_test.handle()
async def handle_join_request_list_test(
    bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()
) -> None:
    arg = args.extract_plain_text().strip()
    params = {"group_id": str(event.group_id)}
    if arg.isdigit():
        params["next_index"] = int(arg)

    try:
        result = await bot.call_api("get_group_join_request_list", **params)
    except Exception as e:
        await join_request_list_test.finish(f"❌ 拉取申请列表失败：{e}")

    join_requests = result.get("join_requests") or []
    next_index = result.get("next_index")

    if not join_requests:
        lines = ["📭 当前没有入群申请"]
        if next_index:
            lines.append(f"（next_index={next_index}）")
        await join_request_list_test.finish("\n".join(lines))

    lines = [f"📋 共 {len(join_requests)} 条入群申请："]
    for item in join_requests:
        lines.append(
            f"· 用户[{mask_id(item.get('user_id'))}] {item.get('username', '')} "
            f"flag={mask_id(item.get('flag'))} "
            f"申请于 {item.get('apply_at', '')} "
            f"验证信息: {mask_id(item.get('verify_info', ''))}"
        )
    if next_index:
        lines.append(f"（next_index={next_index}，可继续翻页）")
    lines.append("如需审批：入群审批测试 <flag> 通过|拒绝（[CQ:set_group,action=add_request]）")
    await join_request_list_test.finish("\n".join(lines))
