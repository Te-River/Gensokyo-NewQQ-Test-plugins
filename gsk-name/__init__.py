from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message

# 定义命令触发器
name_cmd = on_command("name", aliases={"我的昵称", "昵称"}, priority=5)


@name_cmd.handle()
async def handle_name(event: MessageEvent):
    """
    处理 /name 命令：
    - 从消息事件中获取发送者的昵称
    - 回复用户其当前昵称
    """
    # 获取昵称：群聊中会优先取群名片（card），否则取 QQ 昵称
    nickname = event.sender.card or event.sender.nickname

    # 发送回复（自动 at 发送者）
    await name_cmd.finish(f"你的昵称是：{nickname}")