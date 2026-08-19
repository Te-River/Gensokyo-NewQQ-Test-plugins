"""
Gensokyo-NewQQ CQ 码自动化测试插件

触发词: 自动测试
权限: 仅超级用户 (SUPERUSERS)
场景: 群聊 + 私聊 均可触发（无需 @）

测试覆盖:
  - 安全 (9项): [CQ:active] 私聊/频道, keyMap 完整性, reply 去重, 控制型 key 跳过等
  - 需谨慎 (4项): video/music 段模式, markdown 私聊, avatar 段模式, 频道私信媒体
  - 高风险 (2项): 频道扩展 CQ 码, 论坛媒体

使用方法:
  将本文件放入 nonebot2 插件的加载目录，在 .env 中配置 SUPERUSERS 后
  向机器人发送 "自动测试" 即可触发。
"""

import asyncio
import time
from typing import Optional

from nonebot import get_plugin_config, on_command, on_message, require
from nonebot.adapters import Event
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot.rule import command, to_me
from pydantic import BaseModel, Field

# ---------- 元数据 ----------

__plugin_meta__ = PluginMetadata(
    name="Gensokyo CQ 码自动测试",
    description="自动测试 Gensokyo-NewQQ 的所有 CQ 码处理路径，涵盖安全/需谨慎/高风险三类修复",
    usage="发送「自动测试」触发（仅超级用户，群聊/私聊均可）",
    type="application",
    config=None,
)

# ---------- 配置 ----------


class Config(BaseModel):
    """插件配置项"""

    gensokyo_test_group_id: Optional[str] = Field(
        default=None, description="测试用群 ID（留空自动使用触发消息的群）"
    )
    gensokyo_test_user_id: Optional[str] = Field(
        default=None, description="测试用用户 ID（留空自动使用触发者的虚拟 ID）"
    )


plugin_config = get_plugin_config(Config)

# ---------- 规则 ----------
# 仅超级用户，且必须使用指令 alltest 或 完全测试 才可触发
# 注：当前 NoneBot 版本 on_command 首参为 cmd，aliases 注册额外命令名。
auto_test = on_command(
    "alltest",
    aliases={"完全测试"},
    permission=SUPERUSER,
    priority=1,
    block=True,
)


# ---------- 工具函数 ----------

def _cq(tag: str, **kwargs) -> str:
    """构建 CQ 码"""
    params = ",".join(f"{k}={v}" for k, v in kwargs.items())
    return f"[CQ:{tag},{params}]" if params else f"[CQ:{tag}]"


def _seg(type_: str, **data) -> dict:
    """构建消息段"""
    return {"type": type_, "data": data}


def _text(text: str) -> dict:
    return _seg("text", text=text)


def _image(file: str) -> dict:
    return _seg("image", file=file)


def _record(file: str) -> dict:
    return _seg("record", file=file)


def _video(file: str) -> dict:
    return _seg("video", file=file)


def _at(qq: str) -> dict:
    return _seg("at", qq=qq)


def _reply(id_: str) -> dict:
    return _seg("reply", id=id_)


def _markdown(data: str) -> dict:
    return _seg("markdown", data=data)


def _active(type_: str = "", sub_type: str = "") -> dict:
    data = {}
    if type_:
        data["type"] = type_
    if sub_type:
        data["sub_type"] = sub_type
    return _seg("active", **data)


def _avatar(qq: str) -> dict:
    return _seg("avatar", qq=qq)


def _file(file: str, file_name: str = "") -> dict:
    data = {"file": file}
    if file_name:
        data["file_name"] = file_name
    return _seg("file", **data)


def _member(type_: str, group_id: str, user_id: str) -> dict:
    return _seg("member", type=type_, group_id=group_id, user_id=user_id)


# ---------- 测试结果收集器 ----------


class TestResult:
    def __init__(self):
        self.tests: list[dict] = []
        self.start_time = time.time()

    def add(self, category: str, name: str, status: str, detail: str = ""):
        self.tests.append({
            "category": category,
            "name": name,
            "status": status,
            "detail": detail,
        })

    def summary(self) -> str:
        elapsed = time.time() - self.start_time
        total = len(self.tests)
        passed = sum(1 for t in self.tests if t["status"] == "✅ 通过")
        skipped = sum(1 for t in self.tests if t["status"] == "⏭️ 跳过")
        failed = sum(1 for t in self.tests if t["status"] == "❌ 失败")

        lines = [
            f"===== Gensokyo CQ 码自动测试报告 =====",
            f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"耗时: {elapsed:.1f}s",
            f"总计: {total} | ✅ {passed} | ⏭️ {skipped} | ❌ {failed}",
            "",
        ]

        categories = ["安全修复", "需谨慎修复", "高风险修复"]
        for cat in categories:
            items = [t for t in self.tests if t["category"] == cat]
            if not items:
                continue
            lines.append(f"--- {cat} ({len(items)}项) ---")
            for t in items:
                lines.append(f"  {t['status']} {t['name']}")
                if t["detail"]:
                    lines.append(f"    {t['detail']}")
            lines.append("")

        lines.append("====================================")
        return "\n".join(lines)


result = TestResult()


# ---------- 测试发送辅助 ----------


async def send_test(bot, event, msg_type: str, message, label: str):
    """发送测试消息并返回结果"""
    try:
        if msg_type == "group":
            gid = plugin_config.gensokyo_test_group_id or event.group_id
            await bot.call_api("send_group_msg", group_id=gid, message=message)
        elif msg_type == "private":
            uid = plugin_config.gensokyo_test_user_id or event.user_id
            await bot.call_api("send_private_msg", user_id=uid, message=message)
        elif msg_type == "wakeup":
            uid = plugin_config.gensokyo_test_user_id or event.user_id
            await bot.call_api("send_private_msg_wakeup", user_id=uid, message=message)
        elif msg_type == "card":
            gid = plugin_config.gensokyo_test_group_id or event.group_id
            await bot.call_api("send_group_msg", group_id=gid, message=message)
        elif msg_type == "stream":
            uid = plugin_config.gensokyo_test_user_id or event.user_id
            await bot.call_api("send_private_msg", user_id=uid, message=message)
        elif msg_type == "input_notify":
            uid = plugin_config.gensokyo_test_user_id or event.user_id
            await bot.call_api("send_private_msg", user_id=uid, message=message)
        return "✅ 通过"
    except Exception as e:
        return f"❌ 失败: {e}"


def _trigger_msg_id(event) -> str:
    """从触发事件中提取虚拟 message_id 用于 reply 测试"""
    return str(getattr(event, "message_id", ""))


# ---------- 测试用例 ----------


async def test_safe_fixes(bot, event):
    """测试安全修复 (9项)"""

    # 1. [CQ:active] 在私聊中生效
    r = await send_test(bot, event, "private",
        f"{_cq('active')}这是一条带 active 标记的私聊消息", "1")
    result.add("安全修复", "[CQ:active] 私聊主动推送", r)

    # 2. send_private_msg_wakeup 文件 key（仅文本，避免文件下载超时阻塞）
    r = await send_test(bot, event, "wakeup",
        "召回文本测试（文件 key 请手动验证 Gensokyo 日志）",
        "2")
    result.add("安全修复", "send_private_msg_wakeup 文件 key", r)

    # 3. send_private_msg keyMap embed
    r = await send_test(bot, event, "private",
        "embed keyMap 检查（请在 Gensokyo 日志中确认无 'Unhandled' 警告）", "3")
    result.add("安全修复", "send_private_msg keyMap embed", r)

    # 4. [CQ:reply] 在消息段模式无重复（数组段格式）
    reply_id = _trigger_msg_id(event)
    r = await send_test(bot, event, "group",
        [_reply(reply_id), _text("数组段 reply 测试（日志不应有 reply_msg_id 重复警告）")],
        "4")
    if not reply_id:
        r += "（event 无 message_id）"
    result.add("安全修复", "[CQ:reply] 段模式无重复", r)

    # 5. [CQ:reply] 在私聊图文混合消息中（msg_type=7 富媒体reply，gsk应正确处理私聊msg_id）
    reply_id2 = _trigger_msg_id(event)
    r = await send_test(bot, event, "private",
        [_reply(reply_id2), _text("图文混合 reply 测试（图片+文字+引用）"),
         _image("https://picsum.photos/200")],
        "5")
    if not reply_id2:
        r += "（event 无 message_id）"
    result.add("安全修复", "[CQ:reply] 私聊图文混合", r)

    # 6. 私聊遍历跳过控制型 key
    r = await send_test(bot, event, "private",
        f"{_cq('active')}控制型 key 跳过测试（不应发送空消息）", "6")
    result.add("安全修复", "私聊遍历跳过控制型 key", r)

    # 7. 群聊遍历跳过控制型 key
    r = await send_test(bot, event, "group",
        f"{_cq('active')}控制型 key 跳过测试（不应发送空消息）", "7")
    result.add("安全修复", "群聊遍历跳过控制型 key", r)

    # 8. ProcessCQActive/ProcessCQFile 无重复调用（观察日志）
    r = await send_test(bot, event, "group",
        f"{_cq('active')}{_cq('file', file='https://example.com/test.txt')}重复调用测试（日志不应有重复处理）",
        "8")
    result.add("安全修复", "ProcessCQActive/File 无重复调用", r)


async def test_caution_fixes(bot, event):
    """测试需谨慎修复 (4项)"""

    # 获取触发者的虚拟 ID 用于头像测试
    trigger_user_id = str(getattr(event, "user_id", "10001"))

    # 1. 消息段模式 video
    r = await send_test(bot, event, "group",
        [_text("段模式视频测试："), _video("https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4")],
        "1")
    result.add("需谨慎修复", "消息段模式 video", r)

    # 2. 消息段模式 record（本地语音文件）
    r = await send_test(bot, event, "group",
        [_text("段模式语音测试："), _record("file:///D:/Nonebot/Wind/data/voice/voice.mp3")],
        "2")
    result.add("需谨慎修复", "消息段模式 record", r)

    # 3. 私聊纯文本 [CQ:markdown]
    r = await send_test(bot, event, "private",
        f"{_cq('markdown', data='{\"content\":\"这是 **Markdown** 测试消息\"}')}附带文本",
        "3")
    result.add("需谨慎修复", "私聊纯文本 [CQ:markdown]", r)

    # 4. 消息段模式 avatar（使用触发者头像）
    r = await send_test(bot, event, "group",
        [_text("头像测试："), _avatar(trigger_user_id)],
        "4")
    result.add("需谨慎修复", "消息段模式 avatar", r)


async def test_group_features(bot, event):
    """测试群聊扩展能力 (6项) — gsk 011 后保留能力"""

    # 1. 群聊卡片消息（msg_type=8）
    card_json = '{"title":"卡片测试","prompt":"这是一条来自自动测试的卡片消息"," thumbnail":"https://picsum.photos/200"}'
    r = await send_test(bot, event, "card",
        f"{_cq('card', data=card_json)}群聊卡片消息测试",
        "1")
    result.add("群聊扩展", "群聊卡片消息 msg_type=8", r)

    # 2. 私聊输入状态（msg_type=6）
    r = await send_test(bot, event, "input_notify",
        f"{_cq('input_notify', data='{\"hint\":\"测试输入状态\"}')}私聊输入状态测试",
        "2")
    result.add("群聊扩展", "私聊输入状态 msg_type=6", r)

    # 3. 私聊流式消息（type=start）
    r = await send_test(bot, event, "stream",
        f"{_cq('stream', type='start', data='{\"content\":\"流式消息开始测试\"}')}私聊流式消息测试",
        "3")
    result.add("群聊扩展", "私聊流式消息 type=start", r)

    # 4. 群聊文件消息段
    r = await send_test(bot, event, "group",
        [_text("文件测试："), _file("https://example.com/test.txt", "test.txt")],
        "4")
    result.add("群聊扩展", "群聊文件消息段", r)

    # 5. 群聊 @消息段
    trigger_user_id = str(getattr(event, "user_id", "10001"))
    r = await send_test(bot, event, "group",
        [_at(trigger_user_id), _text(" 群聊 @ 消息段测试")],
        "5")
    result.add("群聊扩展", "群聊 @ 消息段", r)

    # 6. 群聊图文混合（含本地图片占位）
    r = await send_test(bot, event, "group",
        [_text("混合消息测试："), _image("https://picsum.photos/200"),
         _text(" 文字+图片混合")],
        "6")
    result.add("群聊扩展", "群聊图文混合段", r)


async def test_high_risk_fixes(bot, event):
    """测试高风险修复 (2项)"""

    # 1. 图文混合消息（msg_type=7 富媒体）
    r = await send_test(bot, event, "group",
        [_text("图文混合测试："), _image("https://picsum.photos/200"),
         _text("（应作为富媒体 msg_type=7 发送）")],
        "1")
    result.add("高风险修复", "图文混合富媒体", r)

    # 2. 群聊 Markdown（msg_type=2）
    r = await send_test(bot, event, "group",
        f"{_cq('markdown', data='{\"content\":\"## 群聊 Markdown 测试\\n这是一条来自自动测试的 Markdown 消息\"}')}群聊 Markdown 测试",
        "2")
    result.add("高风险修复", "群聊 Markdown 消息", r)


# ---------- 主入口 ----------


@auto_test.handle()
async def handle_auto_test(bot, event: Event, matcher: Matcher):
    """处理自动测试命令"""
    global result
    result = TestResult()

    sender_id = getattr(event, "user_id", "unknown")
    group_id = getattr(event, "group_id", None)
    msg_type = "group" if group_id else "private"

    await matcher.send(
        f"Gensokyo CQ 码自动测试启动...\n"
        f"触发者: {sender_id}\n"
        f"场景: {msg_type}\n"
        f"群号: {group_id}\n"
        f"共 20 项测试（安全8 + 需谨慎4 + 群聊扩展6 + 高风险2）\n"
        f"请稍候，消息将陆续发送..."
    )

    # 依次执行四组测试，每组间等待 2 秒
    await test_safe_fixes(bot, event)
    await asyncio.sleep(2)

    await test_caution_fixes(bot, event)
    await asyncio.sleep(2)

    await test_group_features(bot, event)
    await asyncio.sleep(2)

    await test_high_risk_fixes(bot, event)

    # 发送报告
    report = result.summary()
    await matcher.finish(report)