from pathlib import Path
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageSegment, MessageEvent
from nonebot.log import logger

VOICE_DIR = Path.cwd() / "data" / "voice"
VOICE_FILENAME = "voice.mp3"

voice = on_command("语音", priority=5, block=True)

@voice.handle()
async def send_voice(bot: Bot, event: MessageEvent):
    # 构建文件路径，支持 .mp3 和 .flac 备选
    voice_path = VOICE_DIR / VOICE_FILENAME
    if not voice_path.exists():
        voice_path = VOICE_DIR / "voice.flac"
    if not voice_path.exists():
        await voice.finish(f"找不到语音文件！期望路径：{voice_path}")

    try:
        # 使用本地文件路径（file:///）直接发送语音，并立即结束
        file_uri = voice_path.absolute().as_uri()
        await voice.finish(MessageSegment.record(file_uri))
    except Exception as e:
        logger.error(f"发送语音失败: {e}")
        await voice.finish("发送语音失败，请查看日志。")