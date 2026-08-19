# plugins/get_avatar.py
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.typing import T_State
import re

# 创建命令匹配器
avatar = on_command("头像", aliases={"获取头像", "avatar"}, priority=5, block=True)


@avatar.handle()
async def handle_avatar(bot: Bot, event: Event, state: T_State, args: Message = CommandArg()):
    # 提取可能的参数（纯数字或 @某人）
    user_id_str = args.extract_plain_text().strip()
    target_user_id = None

    if user_id_str and user_id_str.isdigit():
        # 直接传了 QQ 号（虚拟 ID）
        target_user_id = int(user_id_str)
    elif event.message:
        # 检查消息中是否有 @某人
        for seg in event.message:
            if seg.type == "at":
                target_user_id = int(seg.data["qq"])
                break

    # 如果没有指定目标，默认获取发送者自己的头像
    if target_user_id is None:
        target_user_id = event.user_id

    # 构造请求参数
    params = {"user_id": target_user_id}
    # 如果是在群聊中，同时传递 group_id 以提升 idmap_pro 模式下的准确率
    if hasattr(event, "group_id"):
        params["group_id"] = str(event.group_id)

    try:
        # 调用 Gensokyo 扩展 API
        result = await bot.call_api("get_avatar", **params)
        avatar_url = result.get("message")
        if not avatar_url:
            await avatar.finish("获取头像失败：未返回头像链接。")
        # 发送头像图片
        await avatar.finish(MessageSegment.image(avatar_url))
    except Exception as e:
        await avatar.finish(f"获取头像时出错：{e}")