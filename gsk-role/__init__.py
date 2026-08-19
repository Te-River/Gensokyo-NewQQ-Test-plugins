from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.rule import Rule

# ---------- 1. 定义规则：仅限群聊触发 ----------
def is_group_event(event: GroupMessageEvent) -> bool:
    return isinstance(event, GroupMessageEvent)

# ---------- 2. 创建命令处理器，触发词为 "role" ----------
# 用户发送 "role" 或 "/role" 均可触发（取决于 NoneBot 配置）
role_matcher = on_command("role", rule=is_group_event, priority=5, block=True)

@role_matcher.handle()
async def handle_role_command(event: GroupMessageEvent):
    # ---------- 3. 核心：获取 Gensokyo-NewQQ 填充的 role 字段 ----------
    sender = event.sender
    role = sender.role  # 值: "owner" | "admin" | "member"
    user_id = sender.user_id
    nickname = sender.nickname or "未知昵称"
    
    # 获取新增的 to_me 字段（判断是否 @ 了机器人）
    to_me = getattr(event, "to_me", False)
    
    # ---------- 4. 身份映射 ----------
    role_map = {
        "owner": " 群主",
        "admin": " 管理员",
        "member": " 普通成员"
    }
    role_text = role_map.get(role, "❓ 未知身份（可能是私聊）")
    
    # ---------- 5. 拼接回复消息 ----------
    reply = (
        f"📋 您的群内身份信息如下：\n"
        f"━━━━━━━━━━━━\n"
        f"👤 昵称：{nickname}\n"
        f"🆔 QQ号：{user_id}\n"
        f"🏷️ 身份：{role_text}\n"
        f"📌 是否@了Bot：{'是' if to_me else '否'}\n"
        f"━━━━━━━━━━━━"
    )
    
    await role_matcher.finish(reply)