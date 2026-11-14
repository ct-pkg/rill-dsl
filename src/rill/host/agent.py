"""RILL 0.1.x 智能体宿主能力层（PH-11）。

把工具注册表映射到与 Shell 相同的 ``HostCapabilities`` 槽位，不直接碰 OS：
- ``ToolRegistry`` 读 ``ril-fakes-tools/0``（与 harness 的 fake 工具同形），
  返回 ``{value, ok}``；工具错误只进错误字符串；
- ``run`` / ``exec`` 是工具，不是进程；``send`` / ``emit`` 是工具，不写 OS stdout；
- manifest 是外部能力声明（``--host-profile``），脚本无权声明授权（§五.1）。

规范缺口与裁定见 ``docs/phases/PH-11/card.md`` §7。
"""

import json
import os
import time

from .. import fakes as fakes_mod
from .. import result
from ..value import Bytes

PROFILE_SCHEMA = "rill.agent-profile/0"
PROFILE_KEYS = (
    "schema",
    "name",
    "description",
    "role",
    "roles",
    "types",
    "workspace",
    "tools",
    "context",
    "limits",
)
TOOLS_SCHEMA = "rill-fakes-tools/0"
TYPE_CONSTRAINTS = ("path", "text")
LIMIT_KEYS = ("steps", "time_ms", "bytes")
DEFAULT_LIMITS = {"steps": 64, "time_ms": 5000, "bytes": 65536}
DEFAULT_VERBS = (
    "read",
    "write",
    "parse",
    "send",
    "search",
    "replace",
    "contains",
    "review",
    "env",
    "run",
)

TOOL_UNREGISTERED = "E-HOST-TOOL-UNREGISTERED"
TOOL_ARGS = "E-HOST-TOOL-ARGS"
ENV_MISSING = "E-HOST-ENV-MISSING"
FS_OUTSIDE = "E-HOST-FS-OUTSIDE"
FS_TYPE = "E-HOST-FS-TYPE"
ROLE_UNKNOWN = "E-HOST-ROLE-UNKNOWN"
ROLE_DENIED = "E-HOST-ROLE-DENIED"
LIMIT_STEPS = "E-HOST-LIMIT-STEPS"
LIMIT_TIME = "E-HOST-LIMIT-TIME"
LIMIT_BYTES = "E-HOST-LIMIT-BYTES"


class AgentHostError(Exception):
    """宿主能力错误；``code`` 由 CLI 转成 run 诊断。"""

    def __init__(self, code, message):
        self.code = code
        self.message = message
        Exception.__init__(self, "%s: %s" % (code, message))


class AgentRoleError(AgentHostError):
    """角色表校验失败；加载期语义，由 CLI 转成 run 诊断。"""


class ToolFailure(Exception):
    """工具调用失败；转成 ``ok=false`` 的错误串，不冒充 DSL 诊断。"""

    def __init__(self, code, message, meta=None):
        self.code = code
        self.message = message
        self.meta = meta or {}
        Exception.__init__(self, "%s: %s" % (code, message))


class RoleTable(object):
    """角色 → 允许动词；``roles`` 的取值是 ``{"verbs": [...]}``。"""

    def __init__(self, roles, default):
        self.roles = {
            name: set(item["verbs"]) for name, item in (roles or {}).items()
        }
        self.default = default

    def role_for(self, subject):
        """字面量主语是角色；省略或动态主语（``$x``）用默认角色。"""
        if not isinstance(subject, dict):
            return self.default
        kind = subject.get("kind")
        if kind == "String":
            return subject["value"]
        if kind == "Bare":
            return subject["text"]
        return self.default

    def require(self, role, verb):
        if role not in self.roles:
            raise AgentRoleError(
                ROLE_UNKNOWN,
                "角色 %r 不在 roles 表；已知角色：%s"
                % (role, ", ".join(sorted(self.roles)) or "无"),
            )
        if verb not in self.roles[role]:
            raise AgentRoleError(
                ROLE_DENIED,
                "角色 %r 无权限调用动词 %r；允许：%s"
                % (role, verb, ", ".join(sorted(self.roles[role])) or "无"),
            )


class ExecLimits(object):
    """执行上限：steps 数工具调用，time_ms 墙钟，bytes 是结果 JSON 的 UTF-8 字节。"""

    def __init__(self, limits=None, clock=None):
        merged = dict(DEFAULT_LIMITS)
        merged.update(limits or {})
        self.limits = merged
        self.clock = clock
        self.started = None
        self.used = 0

    def _now(self):
        return (self.clock or time.monotonic)()

    def before_call(self):
        now = self._now()
        if self.started is None:
            self.started = now
        elapsed = (now - self.started) * 1000
        if elapsed > self.limits["time_ms"]:
            raise ToolFailure(
                LIMIT_TIME,
                "agent 执行超时：%.3fms > %dms" % (elapsed, self.limits["time_ms"]),
                {
                    "limits": {
                        "kind": "time_ms",
                        "limit": self.limits["time_ms"],
                        "observed": round(elapsed, 3),
                    }
                },
            )
        self.used += 1
        if self.used > self.limits["steps"]:
            raise ToolFailure(
                LIMIT_STEPS,
                "agent 工具调用次数超限：%d > %d"
                % (self.used, self.limits["steps"]),
                {
                    "limits": {
                        "kind": "steps",
                        "limit": self.limits["steps"],
                        "used": self.used,
                    }
                },
            )

    def after_call(self, value):
        observed = 0
        if value is not None:
            observed = len(
                json.dumps(value, ensure_ascii=False, default=str).encode("utf-8")
            )
        if observed > self.limits["bytes"]:
            raise ToolFailure(
                LIMIT_BYTES,
                "agent 工具结果超限：%d bytes > %d bytes"
                % (observed, self.limits["bytes"]),
                {
                    "limits": {
                        "kind": "bytes",
                        "limit": self.limits["bytes"],
                        "observed": observed,
                    }
                },
            )


class ToolRegistry(object):
    """工具注册表；队列/默认值语义复用 PH-6 的 ``FakeVerbRegistry``。"""

    def __init__(self, spec=None, path=None):
        spec = spec or {}
        self.path = path
        self._names = tuple(sorted(spec))
        self._verbs = fakes_mod.FakeVerbRegistry()
        for name, item in spec.items():
            if not isinstance(item, dict):
                raise ValueError("工具 %r 的描述必须是对象" % name)
            self._verbs.register(name, item.get("queue", []), default=item.get("default"))

    @classmethod
    def load(cls, path):
        try:
            with open(path, encoding="utf-8") as handle:
                doc = json.load(handle)
        except (OSError, ValueError) as exc:
            raise ValueError("%s: 无法读取工具注册表（%s）" % (path, exc))
        if not isinstance(doc, dict):
            raise ValueError("%s: 顶层必须是对象" % path)
        if doc.get("schema") != TOOLS_SCHEMA:
            raise ValueError("%s.schema: 必须是 %s" % (path, TOOLS_SCHEMA))
        tools = doc.get("tools")
        if not isinstance(tools, dict):
            raise ValueError("%s.tools: 必须是对象" % path)
        return cls(tools, path=path)

    @property
    def names(self):
        return self._names

    def has(self, name):
        return name in self._names

    def call(self, name, args):
        try:
            return self._verbs.call(name, args)
        except KeyError:
            return result.ExecOutcome.failure(
                "%s: 工具 %r 未注册；已注册：%s"
                % (TOOL_UNREGISTERED, name, ", ".join(self._names) or "无"),
                host_meta={
                    "tool": {"name": name, "args": args, "code": TOOL_UNREGISTERED}
                },
            )


def _attach(outcome, meta):
    """保留工具自己的 host_meta，再叠加能力槽位的可观察字段。"""
    merged = dict(meta)
    if outcome.host_meta:
        merged["tool_meta"] = outcome.host_meta
    return result.ExecOutcome(
        value=outcome.value,
        ok=outcome.ok,
        error=outcome.error,
        host_meta=merged,
        exit_code=outcome.exit_code,
    )


class AgentPolicy(object):
    """agent 宿主的外部能力声明；不含任何 OS 能力语义。"""

    def __init__(
        self,
        name,
        workspace,
        role,
        roles,
        types,
        context,
        limits,
        tools,
        path=None,
        description="",
    ):
        self.name = name
        self.workspace = workspace
        self.role = role
        self.roles = roles
        self.types = types
        self.context = context
        self.limits = limits
        self.tools = tools
        self.path = path
        self.description = description

    def exit_code(self, ok):
        """agent 不产生 OS 退出码；脚本完成即 0（PH-11 卡 §7 #5）。"""
        return 0

    def __repr__(self):
        return "AgentPolicy(%s, role=%r)" % (self.name, self.role)


def _load_tools(path):
    if not path:
        return ToolRegistry({}, path=None)
    return ToolRegistry.load(path)


def load_agent_profile(path, cwd=None):
    """读外部 agent manifest；形状错误抛 ValueError，由 CLI 转成 run 诊断。"""
    try:
        with open(path, encoding="utf-8") as handle:
            doc = json.load(handle)
    except (OSError, ValueError) as exc:
        raise ValueError("%s: 无法读取 agent manifest（%s）" % (path, exc))

    if not isinstance(doc, dict):
        raise ValueError("%s: 顶层必须是对象" % path)
    for key in sorted(doc):
        if key not in PROFILE_KEYS:
            raise ValueError("%s: 未知字段 %r" % (path, key))
    if doc.get("schema") != PROFILE_SCHEMA:
        raise ValueError("%s.schema: 必须是 %s" % (path, PROFILE_SCHEMA))
    if not isinstance(doc.get("name"), str) or not doc["name"]:
        raise ValueError("%s.name: 必须是非空字符串" % path)
    description = doc.get("description", "")
    if not isinstance(description, str):
        raise ValueError("%s.description: 必须是字符串" % path)

    roles = doc.get("roles")
    if not isinstance(roles, dict) or not roles:
        raise ValueError("%s.roles: 必须是非空对象" % path)
    for name in sorted(roles):
        item = roles[name]
        if not isinstance(item, dict) or set(item) != {"verbs"}:
            raise ValueError("%s.roles.%s: 必须只有 verbs 字段" % (path, name))
        verbs = item["verbs"]
        if not isinstance(verbs, list) or not all(
            isinstance(verb, str) and verb for verb in verbs
        ):
            raise ValueError("%s.roles.%s.verbs: 必须是非空字符串数组" % (path, name))

    role = doc.get("role", "default")
    if not isinstance(role, str) or not role:
        raise ValueError("%s.role: 必须是非空字符串" % path)
    if role not in roles:
        raise ValueError("%s.role: %r 不在 roles 表里" % (path, role))

    types = doc.get("types", {})
    if not isinstance(types, dict):
        raise ValueError("%s.types: 必须是对象" % path)
    for name in sorted(types):
        if types[name] not in TYPE_CONSTRAINTS:
            raise ValueError(
                "%s.types.%s: 必须是 %s" % (path, name, " / ".join(TYPE_CONSTRAINTS))
            )

    context = doc.get("context", {})
    if not isinstance(context, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in context.items()
    ):
        raise ValueError("%s.context: 必须是字符串到字符串的对象" % path)

    limits = dict(DEFAULT_LIMITS)
    declared = doc.get("limits", {})
    if not isinstance(declared, dict):
        raise ValueError("%s.limits: 必须是对象" % path)
    for key in sorted(declared):
        if key not in LIMIT_KEYS:
            raise ValueError("%s.limits: 未知字段 %r" % (path, key))
        if not isinstance(declared[key], int) or declared[key] <= 0:
            raise ValueError("%s.limits.%s: 必须是正整数" % (path, key))
        limits[key] = declared[key]

    workspace = doc.get("workspace")
    if workspace is None:
        workspace = cwd or os.getcwd()
    elif not isinstance(workspace, str) or not workspace:
        raise ValueError("%s.workspace: 必须是非空字符串" % path)
    else:
        workspace = os.path.normpath(os.path.join(cwd or os.getcwd(), workspace))

    tools_ref = doc.get("tools", "")
    if tools_ref and not isinstance(tools_ref, str):
        raise ValueError("%s.tools: 必须是相对路径字符串" % path)
    tools_path = os.path.join(os.path.dirname(os.path.abspath(path)), tools_ref) if tools_ref else ""
    tools = _load_tools(tools_path)

    return AgentPolicy(
        doc["name"],
        workspace,
        role,
        RoleTable(roles, role),
        types,
        context,
        limits,
        tools,
        path=path,
        description=description,
    )


def default_agent_policy(cwd=None):
    """不带 manifest 的默认 agent 宿主：没有工具，但角色/limits 形状完整。"""
    roles = {"default": {"verbs": list(DEFAULT_VERBS)}}
    return AgentPolicy(
        "builtin-agent",
        cwd or os.getcwd(),
        "default",
        RoleTable(roles, "default"),
        {"file": "path"},
        {},
        dict(DEFAULT_LIMITS),
        ToolRegistry({}),
    )


class AgentProcessCapability(object):
    """进程能力：映射到 ``run`` / ``exec`` 工具，不直接 spawn。"""

    def __init__(self, host):
        self.host = host

    def _tool(self):
        for name in ("run", "exec"):
            if self.host.tools.has(name):
                return name
        return "run"

    def run(self, command, stdin=None):
        if not isinstance(command, str) or not command.strip():
            raise ToolFailure(TOOL_ARGS, "run 需要一个非空命令字符串")
        if stdin is not None and not isinstance(stdin, (str, Bytes)):
            raise ToolFailure(TOOL_ARGS, "run 的 stdin 只接受文本或 Bytes")
        name = self._tool()
        outcome = self.host.tools.call(name, {"command": command, "stdin": stdin})
        return _attach(
            outcome, {"process": {"tool": name, "command": command}}
        )


class AgentStdioCapability(object):
    """标准输入输出：映射到 ``send`` / ``emit`` 工具，没有 OS stdout/stderr。"""

    CHANNEL = "tool"

    def __init__(self, host):
        self.host = host

    def _tool(self):
        for name in ("send", "emit"):
            if self.host.tools.has(name):
                return name
        return "send"

    def write(self, text):
        if isinstance(text, Bytes):
            payload = text.data.decode("utf-8", "replace")
        elif isinstance(text, str):
            payload = text
        else:
            payload = json.dumps(text, ensure_ascii=False, sort_keys=True)
        name = self._tool()
        outcome = self.host.tools.call(name, {"text": payload})
        if outcome.ok and outcome.value is None:
            outcome = result.ExecOutcome.success(payload, host_meta=outcome.host_meta)
        return _attach(
            outcome,
            {"stdio": {"tool": name, "channel": self.CHANNEL, "text": payload}},
        )


class AgentFsCapability(object):
    """文件能力：只把路径交给工具；workspace root 与类型约束在宿主侧校验。"""

    def __init__(self, host):
        self.host = host

    def _split_type(self, raw, operation):
        if not isinstance(raw, str) or raw == "":
            raise ToolFailure(TOOL_ARGS, "%s 需要一个非空路径字符串" % operation)
        type_name = None
        value = raw
        if ":" in raw:
            prefix, rest = raw.split(":", 1)
            if prefix in self.host.policy.types:
                type_name = prefix
                if self.host.policy.types[prefix] != "path":
                    raise ToolFailure(
                        FS_TYPE,
                        "%s 只接受 path 类型，%r 是 %s"
                        % (operation, prefix, self.host.policy.types[prefix]),
                        {"fs": {"code": FS_TYPE, "path": raw}},
                    )
                value = rest
        if value == "":
            raise ToolFailure(TOOL_ARGS, "%s 的路径为空" % operation)
        return value, type_name

    def _resolve(self, raw, operation):
        value, type_name = self._split_type(raw, operation)
        root = os.path.normpath(self.host.policy.workspace)
        target = os.path.normpath(
            value if os.path.isabs(value) else os.path.join(root, value)
        )
        if target != root and not target.startswith(root + os.sep):
            raise ToolFailure(
                FS_OUTSIDE,
                "%s 的路径 %r 越出 workspace %r" % (operation, raw, root),
                {"fs": {"code": FS_OUTSIDE, "path": raw, "root": root}},
            )
        relative = os.path.relpath(target, root).replace(os.sep, "/")
        return relative, type_name, root

    def read(self, raw):
        path, type_name, root = self._resolve(raw, "read")
        args = {"path": path}
        outcome = self.host.tools.call("read", args)
        return _attach(
            outcome,
            {
                "fs": {
                    "tool": "read",
                    "path": path,
                    "root": root,
                    "type": type_name,
                },
                "tool": {"name": "read", "args": args},
            },
        )

    def write(self, raw, content):
        path, type_name, root = self._resolve(raw, "write")
        if not isinstance(content, (str, Bytes)):
            raise ToolFailure(TOOL_ARGS, "write 的内容只接受文本或 Bytes")
        args = {"path": path, "content": content}
        outcome = self.host.tools.call("write", args)
        if outcome.ok and outcome.value is None:
            outcome = result.ExecOutcome.success(path, host_meta=outcome.host_meta)
        return _attach(
            outcome,
            {
                "fs": {
                    "tool": "write",
                    "path": path,
                    "root": root,
                    "type": type_name,
                },
                "tool": {"name": "write", "args": args},
            },
        )


class AgentEnvCapability(object):
    """环境变量能力：只读 manifest 的 kernel context，不读 OS env。"""

    def __init__(self, host):
        self.host = host

    def get(self, name):
        if not isinstance(name, str) or name == "":
            raise ToolFailure(TOOL_ARGS, "env 需要一个非空变量名")
        if name not in self.host.policy.context:
            raise ToolFailure(
                ENV_MISSING,
                "环境变量 %r 未在 agent context 中注入" % name,
                {"env": {"code": ENV_MISSING, "name": name, "source": "context"}},
            )
        return result.ExecOutcome.success(
            self.host.policy.context[name],
            host_meta={"env": {"name": name, "source": "context"}},
        )


class AgentHost(object):
    """一次 ``rill run`` 的 agent 宿主句柄。"""

    def __init__(self, policy, cwd=None, clock=None, tools=None):
        self.policy = policy
        self.cwd = cwd or policy.workspace
        self.clock = clock
        self.tools = tools if tools is not None else policy.tools
        self.process = AgentProcessCapability(self)
        self.stdio = AgentStdioCapability(self)
        self.fs = AgentFsCapability(self)
        self.env = AgentEnvCapability(self)
        self.limits = ExecLimits(policy.limits, clock=clock)

    def validate_program(self, program):
        """在 exec 之前按角色表校验每个 VerbCall；字面量主语才是角色。"""
        self._walk_roles(program)

    def _walk_roles(self, node):
        if isinstance(node, list):
            for item in node:
                self._walk_roles(item)
            return
        if not isinstance(node, dict):
            return
        if node.get("kind") == "VerbCall":
            role = self.policy.roles.role_for(node.get("subject"))
            self.policy.roles.require(role, node["verb"])
        for key, value in node.items():
            if key in ("kind", "span"):
                continue
            self._walk_roles(value)


def _require_text(value, message):
    if not isinstance(value, str) or value == "":
        raise ToolFailure(TOOL_ARGS, message)
    return value


class AgentVerbRegistry(object):
    """把 DSL 动词映射到工具/能力槽位；未映射动词不静默成功。"""

    VERB_MAP = {
        "read": ("fs", "read"),
        "write": ("fs", "write"),
        "run": ("process", "run"),
        "env": ("env", "get"),
        "send": ("stdio", "write"),
        "search": ("tool", "search"),
        "parse": ("tool", "parse"),
        "replace": ("tool", "replace"),
        "contains": ("tool", "contains"),
        "review": ("tool", "review"),
    }

    def __init__(self, host):
        self.host = host

    def call(self, name, entry):
        if name not in self.VERB_MAP:
            raise KeyError(
                "E-RUN-VERB-UNREGISTERED: 动词 %r 没有 agent 宿主映射；已映射：%s"
                % (name, ", ".join(sorted(self.VERB_MAP)))
            )
        try:
            self.host.limits.before_call()
            outcome = self._dispatch(name, entry)
            self.host.limits.after_call(outcome.value)
            return outcome
        except ToolFailure as exc:
            return result.ExecOutcome.failure(str(exc), host_meta=exc.meta)

    def _dispatch(self, name, entry):
        if name == "read":
            return self.host.fs.read(entry["object"])

        if name == "write":
            content = entry["subject"] if entry["subject"] is not None else entry["input"]
            return self.host.fs.write(entry["object"], content)

        if name == "run":
            command = _require_text(entry["object"], "run 需要一个命令字符串")
            return self.host.process.run(command, stdin=entry["input"])

        if name == "env":
            return self.host.env.get(entry["object"])

        if name == "send":
            text = entry["subject"]
            if text is None:
                text = entry["object"]
            if text is None:
                text = entry["input"]
            if text is None:
                text = ""
            return self.host.stdio.write(text)

        args = {
            "object": entry["object"],
            "input": entry["input"],
            "post": entry["post"],
        }
        outcome = self.host.tools.call(name, args)
        return _attach(outcome, {"tool": {"name": name, "args": args}})
