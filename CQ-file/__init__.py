from pathlib import Path
import random
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message

file_test = on_command("文件测试", priority=10)

@file_test.handle()
async def handle_file_test():
    data_dir = Path.cwd() / "data" / "file"

    if not data_dir.exists():
        await file_test.finish("❌ 文件夹 data/file 不存在")
    
    files = [f for f in data_dir.iterdir() if f.is_file()]
    if not files:
        await file_test.finish("❌ 文件夹中没有文件")
    
    chosen = random.choice(files)
    file_uri = chosen.absolute().as_uri()
    file_name = chosen.name  # 含扩展名

    # 使用正确的参数名 file_name
    msg = Message(f"[CQ:file,file={file_uri},file_name={file_name}]")
    
    await file_test.finish(msg)