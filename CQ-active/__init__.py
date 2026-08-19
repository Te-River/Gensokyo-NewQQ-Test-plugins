from nonebot import on_command, on_notice
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent, NoticeEvent
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.plugin import PluginMetadata
from nonebot.params import CommandArg
import json

__plugin_meta__ = PluginMetadata(
    name="主动消息",
    description="C2C 唤醒 + 群聊主动推送",
    usage="""
指令:
  唤醒 <用户名/@某人> <消息>   — 向用户发送唤醒私聊
  推送 <消息>                   — 向当前群主动推送
  推送 <群号> <消息>            — 向指定群主动推送
  群列表                        — 获取可推送的群列表
  推送状态                      — 查看主动推送说明
    """,
    type="application",
)

# ── 主动消息自动标记 ──────────────────────────

def active_msg(text: str) -> Message:
    """给消息加上 [CQ:active] 标记"""
    # 用 MessageSegment 构建，避免 nonebot 解析 [CQ:active] 时吞掉后续文本
    segs = [MessageSegment.text("[CQ:active]")]
    if text:
        segs.append(MessageSegment.text(text))
    return Message(segs)

# ── 推送状态 ──────────────────────────────────

status_cmd = on_command("推送状态")

@status_cmd.handle()
async def handle_status(bot: Bot, event: GroupMessageEvent):
    await status_cmd.finish(
        "请在机器人资料页 → 群消息推送 确认是否已开启\n"
        "开启后无需@即可向该群发消息"
    )

# ── 群列表 ────────────────────────────────────

groups_cmd = on_command("群列表")

@groups_cmd.handle()
async def handle_groups(bot: Bot, event: MessageEvent):
    group_list = await bot.get_group_list()
    if not group_list:
        await groups_cmd.finish("当前没有加入任何群")
    lines = ["可推送的群列表："]
    for g in group_list:
        gid = g.get("group_id", "?")
        name = g.get("group_name", "") or g.get("name", "") or "(未获取到群名)"
        lines.append(f"  [{gid}] {name}")
    await groups_cmd.finish("\n".join(lines))

# ── 主动群推送 ────────────────────────────────

push_cmd = on_command("推送")

@push_cmd.handle()
async def handle_push(bot: Bot, event: MessageEvent, arg: Message = CommandArg()):
    text = arg.extract_plain_text().strip()
    if not text:
        await push_cmd.finish("用法: 推送 <消息> 或 推送 <群号> <消息>")

    parts = text.split(maxsplit=1)

    # 推送至指定群
    if len(parts) == 2 and parts[0].isdigit():
        group_id = int(parts[0])
        msg = parts[1]
        try:
            group_info = await bot.get_group_info(group_id=group_id)
            group_name = group_info.get("group_name", "") or group_info.get("name", "") or str(group_id)
        except Exception:
            group_name = str(group_id)
        try:
            await bot.send_group_msg(group_id=group_id, message=active_msg(msg))
        except Exception as e:
            await push_cmd.finish(f"推送到群 [{group_id}] 失败: {e}")
        await push_cmd.finish(f"已向群 [{group_id}]{group_name} 推送: {msg}")

    # 推送至当前群
    if not isinstance(event, GroupMessageEvent):
        await push_cmd.finish("私聊中请指定群号: 推送 <群号> <消息>")
    try:
        await bot.send_group_msg(group_id=event.group_id, message=active_msg(text))
    except Exception as e:
        await push_cmd.finish(f"推送到当前群失败: {e}")
    await push_cmd.finish(f"已向当前群推送: {text}")

# ── C2C 唤醒私聊 ──────────────────────────────

wakeup_cmd = on_command("唤醒")

@wakeup_cmd.handle()
async def handle_wakeup(bot: Bot, event: MessageEvent, arg: Message = CommandArg()):
    # 优先从 @ 段提取 OpenID
    openid = None
    for seg in arg:
        if seg.type == "at":
            openid = str(seg.data.get("qq", ""))
            break

    # 提取纯文本内容用于分割
    text = arg.extract_plain_text().strip()

    # 如果有 @，去掉命令前缀后剩下的纯文本就是消息
    # 注意: on_command("唤醒") 已剥离命令前缀，text 不含"唤醒"
    # 例: 唤醒 @张三 你好 → arg 为 at+text(" 你好") → text="你好"
    if openid:
        msg_text = text  # 命令前缀已被 on_command 剥离
        if not msg_text:
            await wakeup_cmd.finish("用法: 唤醒 @某人 <消息>")
        target = event.sender.nickname if hasattr(event, 'sender') and event.sender else (openid[:8] + "...")
    else:
        # 无 @，用文本分割
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await wakeup_cmd.finish("用法: 唤醒 <用户名/@某人> <消息>")
        target = parts[0]
        msg_text = parts[1]

        # 32 位 OpenID
        if not openid and len(target) == 32:
            openid = target

        # 群内按用户名查找
        if not openid and isinstance(event, GroupMessageEvent):
            try:
                members = await bot.get_group_member_list(group_id=event.group_id)
                for m in members:
                    name = (m.get("nickname") or m.get("card") or "").lower()
                    if target.lower() in name:
                        openid = str(m.get("user_id", ""))
                        break
            except Exception:
                pass

    if not openid:
        await wakeup_cmd.finish("找不到该用户")

    try:
        await bot.call_api(
            "send_private_msg_wakeup",
            user_id=openid,
            message=active_msg(msg_text),
        )
    except Exception as e:
        await wakeup_cmd.finish(f"唤醒失败: {e}")
    await wakeup_cmd.finish(f"已向 {target} 发送唤醒消息")

# ── 监听主动推送开关事件 ─────────────────────

@on_notice().handle()
async def handle_group_msg_switch(bot: Bot, event: NoticeEvent):
    try:
        data = json.loads(event.json())
    except Exception:
        return
    if data.get("notice_type") == "group_msg_receive":
        gid = data.get("group_id", "?")
        try:
            info = await bot.get_group_info(group_id=int(gid))
            name = info.get("group_name", str(gid))
        except Exception:
            name = str(gid)
        await bot.send_group_msg(
            group_id=int(gid),
            message=active_msg(f"本群已开启主动推送！可用「推送 <消息>」来推送了~"),
        )
