"""
[CQ:markdown] 测试插件

触发指令：md测试
功能：发送独立 Markdown 消息，验证 [CQ:markdown,data=JSON] 解析路径。
"""

import json
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message

md_test = on_command("md测试", priority=5)

_MD_DATA = {
    "content": "## 这是 Markdown 测试\n\n- 支持 **加粗**\n- 支持 `行内代码`\n- 支持 [链接](https://example.com)"
}


@md_test.handle()
async def handle_md_test():
    data = json.dumps(_MD_DATA, ensure_ascii=False)
    msg = Message(f"[CQ:markdown,data={data}]")
    await md_test.finish(msg)
