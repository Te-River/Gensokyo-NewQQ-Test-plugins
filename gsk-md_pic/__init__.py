import json
from pathlib import Path
from typing import List, Optional

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.log import logger

__plugin_meta__ = PluginMetadata(
    name="本地图片发送（自定义尺寸语法）",
    description="将本地图片转为Markdown，使用 ![#100px #100px](path) 格式",
    usage="/pic [图片名] 或 /pic 列出所有图片",
    extra={
        "pic_dir": "bot根目录/src/plugins/md_pic/pic",
    },
)

BASE_DIR = Path(__file__).parent
PIC_DIR = BASE_DIR / "pic"
PIC_DIR.mkdir(exist_ok=True)

SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}

# 尺寸配置（可在此修改）
IMG_WIDTH = "1920px"
IMG_HEIGHT = "1080px"

pic_cmd = on_command("pic", aliases={"图片"}, priority=10, block=True)

@pic_cmd.handle()
async def handle_pic(bot: Bot, args: Message = CommandArg()):
    arg = args.extract_plain_text().strip()
    logger.info(f"收到 /pic 命令，参数：'{arg}'")

    if not arg:
        images = list_images()
        if not images:
            await pic_cmd.finish(f"📂 图片目录为空，请添加图片到：\n{PIC_DIR}")
        else:
            msg = "📂 可用的图片：\n" + "\n".join(f"- {name}" for name in images)
            await pic_cmd.finish(msg)
        return

    matched_path = find_image(arg)
    if matched_path is None:
        suggestions = fuzzy_match(arg)
        if suggestions:
            hint = "、".join(suggestions[:5])
            await pic_cmd.finish(f"❌ 未找到图片：{arg}\n💡 你是不是想找：{hint}")
        else:
            await pic_cmd.finish(f"❌ 未找到图片：{arg}\n📂 请确认文件名，或使用 /pic 列出所有图片")
        return

    # 获取图片绝对路径
    abs_path = matched_path.absolute().as_posix()
    file_uri = f"file://{abs_path}"

    title = matched_path.stem
    # 按用户要求：使用 ![#100px #100px](url) 格式
    markdown_content = f"# {title}\n\n![#{IMG_WIDTH} #{IMG_HEIGHT}]({file_uri})"

    # 构造 Gensokyo 的 markdown 消息段
    payload = {"markdown": {"content": markdown_content}}
    json_str = json.dumps(payload, ensure_ascii=False)
    import base64
    b64_payload = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    seg = MessageSegment("markdown", {"data": b64_payload})

    await pic_cmd.finish(seg)


# ---------- 辅助函数 ----------
def list_images() -> List[str]:
    files = []
    for f in PIC_DIR.iterdir():
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS:
            files.append(f.name)
    return sorted(files)

def find_image(name: str) -> Optional[Path]:
    target = PIC_DIR / name
    if target.is_file() and target.suffix.lower() in SUPPORTED_EXTS:
        return target
    return None

def fuzzy_match(name: str) -> List[str]:
    name_lower = name.lower()
    suggestions = []
    for f in PIC_DIR.iterdir():
        if not f.is_file() or f.suffix.lower() not in SUPPORTED_EXTS:
            continue
        if f.stem.lower() == name_lower or f.name.lower() == name_lower or name_lower in f.stem.lower():
            suggestions.append(f.name)
    seen = set()
    unique = []
    for s in suggestions:
        if s not in seen:
            seen.add(s)
            unique.append(s)
    return unique[:10]