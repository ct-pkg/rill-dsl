"""fake 工具与外部能力桩的最小加载器。

两类资产：
  fakes/tools.json  工具层：read / write / search / parse / send / replace，按队列返回 {value, ok}
  fakes/host.json   能力桩：process / fs / env / stdio / exit，内容词汇不是宿主契约

这里只做“加载 + 统一形状 + 可重复取用”，不接真实文件系统、网络或进程。
"""

import copy
import json
import os

TOOLS_SCHEMA = "rill-fakes-tools/0"
HOST_SCHEMA = "rill-fakes-host/0"
TOOL_NAMES = ("read", "write", "search", "parse", "send", "replace")
HOST_SLOTS = ("process", "fs", "env", "stdio", "exit")


class FakeError(ValueError):
    pass


def _load_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as exc:
        raise FakeError("%s: 无法读取（%s）" % (path, exc))


def _validate_outcome(outcome, where):
    if not isinstance(outcome, dict):
        raise FakeError("%s: outcome 必须是对象" % where)
    if not isinstance(outcome.get("ok"), bool):
        raise FakeError("%s.ok: 必须是布尔值" % where)
    if outcome["ok"]:
        if "value" not in outcome:
            raise FakeError("%s.value: ok=true 时必须给出 value（可为 null）" % where)
    else:
        if not isinstance(outcome.get("error"), str) or not outcome["error"]:
            raise FakeError("%s.error: ok=false 时必须给出非空错误串" % where)


class FakeTools(object):
    def __init__(self, path, scripts):
        self.path = path
        self.scripts = scripts
        self.calls = []

    def invoke(self, tool, args=None):
        if tool not in self.scripts:
            raise FakeError("未注册的 fake 工具 %r（%s）" % (tool, self.path))
        entry = self.scripts[tool]
        queue = entry["queue"]
        if queue:
            outcome = queue.pop(0)
        else:
            outcome = entry["default"]
        self.calls.append({"tool": tool, "args": copy.deepcopy(args), "outcome": copy.deepcopy(outcome)})
        return copy.deepcopy(outcome)

    def scripted_calls(self):
        return sum(len(entry["queue"]) for entry in self.scripts.values())


def load_tools(path):
    doc = _load_json(path)
    if not isinstance(doc, dict):
        raise FakeError("%s: 顶层必须是对象" % path)
    if doc.get("schema") != TOOLS_SCHEMA:
        raise FakeError("%s.schema: 必须是 %s" % (path, TOOLS_SCHEMA))
    tools = doc.get("tools")
    if not isinstance(tools, dict):
        raise FakeError("%s.tools: 必须是对象" % path)
    missing = [name for name in TOOL_NAMES if name not in tools]
    if missing:
        raise FakeError("%s.tools: 缺少工具 %s" % (path, ", ".join(missing)))

    scripts = {}
    for name, entry in tools.items():
        where = "%s.tools.%s" % (path, name)
        if not isinstance(entry, dict):
            raise FakeError("%s: 必须是对象" % where)
        queue = entry.get("queue", [])
        if not isinstance(queue, list):
            raise FakeError("%s.queue: 必须是数组" % where)
        for index, outcome in enumerate(queue):
            _validate_outcome(outcome, "%s.queue[%d]" % (where, index))
        default = entry.get("default")
        if default is None:
            raise FakeError("%s.default: 必填（队列耗尽后的确定性结果）" % where)
        _validate_outcome(default, where + ".default")
        scripts[name] = {"queue": copy.deepcopy(queue), "default": copy.deepcopy(default)}
    return FakeTools(path, scripts)


class HostStubs(object):
    def __init__(self, path, slots):
        self.path = path
        self.slots = slots

    def slot(self, name):
        if name not in self.slots:
            raise FakeError("未知能力桩 %r（%s）" % (name, self.path))
        return copy.deepcopy(self.slots[name])


def load_host(path):
    doc = _load_json(path)
    if not isinstance(doc, dict):
        raise FakeError("%s: 顶层必须是对象" % path)
    if doc.get("schema") != HOST_SCHEMA:
        raise FakeError("%s.schema: 必须是 %s" % (path, HOST_SCHEMA))
    slots = {}
    for name in HOST_SLOTS:
        if name not in doc:
            raise FakeError("%s: 缺少能力桩 %s" % (path, name))
        if not isinstance(doc[name], dict):
            raise FakeError("%s.%s: 必须是对象" % (path, name))
        slots[name] = copy.deepcopy(doc[name])
    extra = [key for key in doc if key not in HOST_SLOTS and key not in ("schema", "description")]
    if extra:
        raise FakeError("%s: 未知字段 %s" % (path, ", ".join(sorted(extra))))
    return HostStubs(path, slots)
