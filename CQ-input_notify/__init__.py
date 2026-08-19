# input_notify_only.py
from nonebot import on_command
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Bot, PrivateMessageEvent, Message
from nonebot.params import CommandArg

notify_only = on_command("输入测试", rule=to_me(), priority=10, block=True)

@notify_only.handle()
async def handle_only(bot: Bot, event: PrivateMessageEvent, arg: Message = CommandArg()):
    second = 60
    if arg:
        text = arg.extract_plain_text().strip()
        if text.isdigit():
            sec = int(text)
            if 1 <= sec <= 60:
                second = sec
    # 构造 CQ 码，后面跟一个空格（作为最小正文）
    msg = Message(f"[CQ:input_notify,type=1,second={second}] ")
    # 发送，用户会看到“正在输入”提示持续 second 秒，然后消失，无其他回复
    await bot.send_private_msg(user_id=event.user_id, message=msg)