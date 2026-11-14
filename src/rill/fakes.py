"""``--fakes`` 工具桩加载（PH-7-T4）。

只读 ``testdata/0.1.0/fakes/tools.json`` 的 schema 形状，装成
``FakeVerbRegistry``；不理解宿主能力，不碰真实文件/网络/进程。
"""

import json

from .verbs import FakeVerbRegistry

TOOLS_SCHEMA = "rill-fakes-tools/0"


def load_tools(path):
    with open(path, encoding="utf-8") as handle:
        doc = json.load(handle)
    if not isinstance(doc, dict):
        raise ValueError("fakes 顶层必须是对象：%s" % path)
    if doc.get("schema") != TOOLS_SCHEMA:
        raise ValueError(
            "fakes schema 必须是 %r，实际 %r" % (TOOLS_SCHEMA, doc.get("schema"))
        )
    tools = doc.get("tools")
    if not isinstance(tools, dict):
        raise ValueError("fakes 缺少 tools 对象：%s" % path)
    verbs = FakeVerbRegistry()
    for name, spec in tools.items():
        if not isinstance(spec, dict):
            raise ValueError("fake 工具 %r 的描述必须是对象" % name)
        verbs.register(name, spec.get("queue", []), default=spec.get("default"))
    return verbs
