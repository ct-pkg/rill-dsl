"""RILL 0.1.x Shell 宿主能力层（PH-10）。

只实现 OS 能力，不改语法、parser 与求值规则：
- ``ShellPolicy`` 是外部能力清单（``--host-profile``），声明 process/fs/env/stdio 的
  allow 与 ``exit_codes``；脚本无权声明授权（§五.1）；
- ``ProcessCapability`` 把 DSL 字符串按 ``shlex.split`` 切 argv，stdin 接受文本或
  ``Bytes``，stdout/stderr 捕获为文本；非法 UTF-8 转为 ``Bytes``；
- 未声明的危险操作抛 ``CapabilityDenied``，错误串写明 ``slot.operation``。

规范缺口与裁定见 ``docs/phases/PH-10/card.md`` §8。
"""

import base64
import json
import os
import shlex
import subprocess

from .. import result
from ..value import Bytes

DENIED_CODE = "E-HOST-CAPABILITY-DENIED"
PROFILE_SCHEMA = "rill.shell-profile/0"
PROFILE_KEYS = ("schema", "name", "allow", "exit_codes")
ALLOW_SLOTS = ("process", "fs", "env", "stdio")
DEFAULT_ALLOW = {
    "process": (),
    "fs": ("read",),
    "env": ("get",),
    "stdio": ("write",),
}
DEFAULT_EXIT_CODES = {"ok": 0, "unhandled": 1}
DEFAULT_TIMEOUT = 10.0


class CapabilityDenied(Exception):
    """能力清单未声明该操作；``slot`` / ``operation`` 供调用方转成 ``ok=false``。"""

    def __init__(self, slot, operation, profile_name="builtin"):
        self.code = DENIED_CODE
        self.slot = slot
        self.operation = operation
        self.profile_name = profile_name
        self.message = (
            "%s: Shell profile %r 未声明能力 %s.%s；"
            "在 --host-profile 的 allow.%s 中加入 %r"
            % (DENIED_CODE, profile_name, slot, operation, slot, operation)
        )
        Exception.__init__(self, self.message)


class HostError(Exception):
    """宿主操作失败；``code`` 进入 ``ok=false`` 的错误串，不冒充 DSL 诊断。"""

    def __init__(self, code, message):
        self.code = code
        self.message = message
        Exception.__init__(self, "%s: %s" % (code, message))


class ShellPolicy(object):
    """能力清单；缺省槽位表示没有任何授权。"""

    def __init__(self, allow=None, exit_codes=None, name="builtin", path=None):
        allow = allow or {}
        self.allow = {slot: tuple(allow.get(slot, ())) for slot in ALLOW_SLOTS}
        self.exit_codes = dict(DEFAULT_EXIT_CODES)
        self.exit_codes.update(exit_codes or {})
        self.name = name
        self.path = path

    def allows(self, slot, operation):
        return operation in self.allow.get(slot, ())

    def require(self, slot, operation):
        if not self.allows(slot, operation):
            raise CapabilityDenied(slot, operation, self.name)

    def exit_code(self, ok):
        return self.exit_codes["ok"] if ok else self.exit_codes["unhandled"]

    def __repr__(self):
        return "ShellPolicy(%s, allow=%r)" % (self.name, self.allow)


def default_shell_policy():
    """shell profile 的默认能力：只读文件、读 env、写 stdio；不起进程、不写文件。"""
    return ShellPolicy(DEFAULT_ALLOW, DEFAULT_EXIT_CODES, name="builtin-shell")


def load_shell_profile(path):
    """读外部能力清单；形状错误抛 ValueError，由 CLI 转成 run 诊断。"""
    try:
        with open(path, encoding="utf-8") as handle:
            doc = json.load(handle)
    except (OSError, ValueError) as exc:
        raise ValueError("%s: 无法读取能力清单（%s）" % (path, exc))

    if not isinstance(doc, dict):
        raise ValueError("%s: 顶层必须是对象" % path)
    for key in sorted(doc):
        if key not in PROFILE_KEYS:
            raise ValueError("%s: 未知字段 %r" % (path, key))
    if doc.get("schema") != PROFILE_SCHEMA:
        raise ValueError("%s.schema: 必须是 %s" % (path, PROFILE_SCHEMA))
    if not isinstance(doc.get("name"), str) or not doc["name"]:
        raise ValueError("%s.name: 必须是非空字符串" % path)

    allow = doc.get("allow")
    if not isinstance(allow, dict):
        raise ValueError("%s.allow: 必须是对象" % path)
    for slot in sorted(allow):
        if slot not in ALLOW_SLOTS:
            raise ValueError("%s.allow: 未知槽位 %r" % (path, slot))
        operations = allow[slot]
        if not isinstance(operations, list) or not all(
            isinstance(item, str) and item for item in operations
        ):
            raise ValueError("%s.allow.%s: 必须是非空字符串数组" % (path, slot))

    exit_codes = doc.get("exit_codes", {})
    if not isinstance(exit_codes, dict):
        raise ValueError("%s.exit_codes: 必须是对象" % path)
    for key in sorted(exit_codes):
        if key not in DEFAULT_EXIT_CODES:
            raise ValueError("%s.exit_codes: 未知字段 %r" % (path, key))
        if not isinstance(exit_codes[key], int):
            raise ValueError("%s.exit_codes.%s: 必须是整数" % (path, key))

    return ShellPolicy(allow, exit_codes, name=doc["name"], path=path)


def _decode_bytes(raw):
    """UTF-8 文本优先；非法 UTF-8 保留为 ``Bytes``，不做有损替换。"""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return Bytes(raw)


def jsonable(value):
    """把 ``Bytes`` / ``Opaque`` 转成 CLI 可序列化的形状；其余原样返回。"""
    if isinstance(value, Bytes):
        return {"$bytes": base64.b64encode(value.data).decode("ascii")}
    return value


class ProcessResult(object):
    """进程能力的结果：``code`` / ``stdout`` / ``stderr`` 全部可观察。"""

    def __init__(self, argv, code, stdout, stderr, timed_out=False, spawn_error=""):
        self.argv = argv
        self.code = code
        self.stdout = stdout
        self.stderr = stderr
        self.timed_out = timed_out
        self.spawn_error = spawn_error

    @property
    def ok(self):
        return self.spawn_error == "" and self.code == 0 and not self.timed_out

    @property
    def value(self):
        return self.stdout

    def as_meta(self):
        return {
            "argv": list(self.argv),
            "code": self.code,
            "stdout": jsonable(self.stdout),
            "stderr": jsonable(self.stderr),
            "timed_out": self.timed_out,
        }

    def error(self):
        if self.timed_out:
            return "E-HOST-PROCESS-TIMEOUT: 进程超时（argv=%r）" % (self.argv,)
        if self.spawn_error:
            return "E-HOST-PROCESS-SPAWN: %s" % self.spawn_error
        text = self.stderr if isinstance(self.stderr, str) else ""
        return text or "E-HOST-PROCESS-EXIT: 进程退出码 %r" % (self.code,)

    def __repr__(self):
        return "ProcessResult(code=%r, stdout=%r, stderr=%r)" % (
            self.code,
            self.stdout,
            self.stderr,
        )


class ProcessCapability(object):
    """进程能力：spawn/exec、cwd/env/timeout、stdout/stderr 捕获。"""

    def __init__(self, policy, cwd=None, env=None, timeout=DEFAULT_TIMEOUT):
        self.policy = policy
        self.cwd = cwd
        self.env = dict(env or {})
        self.timeout = timeout

    def run(self, command, stdin=None):
        self.policy.require("process", "run")
        argv = shlex.split(command)
        if not argv:
            raise ValueError("进程命令为空：%r" % (command,))

        if stdin is None:
            raw = b""
        elif isinstance(stdin, Bytes):
            raw = stdin.data
        elif isinstance(stdin, str):
            raw = stdin.encode("utf-8")
        else:
            raise TypeError("进程 stdin 只接受文本或 Bytes，实际 %r" % type(stdin))

        merged = dict(os.environ)
        merged.update(self.env)
        try:
            proc = subprocess.run(
                argv,
                cwd=self.cwd,
                env=merged,
                input=raw,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired as exc:
            return ProcessResult(
                argv,
                None,
                _decode_bytes(exc.stdout or b""),
                _decode_bytes(exc.stderr or b""),
                timed_out=True,
            )
        except OSError as exc:
            return ProcessResult(argv, None, "", "", spawn_error=str(exc))

        return ProcessResult(
            argv,
            proc.returncode,
            _decode_bytes(proc.stdout or b""),
            _decode_bytes(proc.stderr or b""),
        )


class FsCapability(object):
    """文件能力：只做 read/write；相对路径按宿主 cwd 解析，不额外强加 root。"""

    def __init__(self, policy, cwd=None):
        self.policy = policy
        self.cwd = cwd or os.getcwd()

    def _resolve(self, path):
        return path if os.path.isabs(path) else os.path.join(self.cwd, path)

    def read(self, path):
        self.policy.require("fs", "read")
        target = self._resolve(path)
        try:
            with open(target, "rb") as handle:
                raw = handle.read()
        except OSError as exc:
            raise HostError("E-HOST-FS-READ", "%s（%s）" % (path, exc))
        return _decode_bytes(raw)

    def write(self, path, content):
        self.policy.require("fs", "write")
        if isinstance(content, Bytes):
            raw = content.data
        elif isinstance(content, str):
            raw = content.encode("utf-8")
        else:
            raise TypeError("写文件内容只接受文本或 Bytes，实际 %r" % type(content))
        target = self._resolve(path)
        try:
            with open(target, "wb") as handle:
                handle.write(raw)
        except OSError as exc:
            raise HostError("E-HOST-FS-WRITE", "%s（%s）" % (path, exc))
        return path


class EnvCapability(object):
    """环境变量能力：进程级快照，不做全局可变环境。"""

    def __init__(self, policy, env=None):
        self.policy = policy
        self._env = dict(os.environ if env is None else env)

    def get(self, name):
        self.policy.require("env", "get")
        if name not in self._env:
            raise HostError("E-HOST-ENV-MISSING", "环境变量 %r 未定义" % name)
        return self._env[name]


class ShellHost(object):
    """一次 ``rill run`` 的宿主句柄；能力对象共享同一份 policy。"""

    def __init__(self, policy, cwd=None, env=None, stdin=None, stdout=None, stderr=None):
        self.policy = policy
        self.cwd = cwd
        self.process = ProcessCapability(policy, cwd=cwd)
        self.fs = FsCapability(policy, cwd=cwd)
        self.env = EnvCapability(policy, env=env)
        self.stdio = None
        self.exit = None


def _require_text(value, message):
    if not isinstance(value, str) or value == "":
        raise HostError("E-HOST-VERB-ARGS", message)
    return value


class ShellVerbRegistry(object):
    """真实宿主动词表；没有映射的动词直接抛 KeyError，由解释器转成
    ``E-RUN-VERB-UNREGISTERED``，不静默当作空操作。
    """

    VERB_MAP = {
        "read": ("fs", "read"),
        "write": ("fs", "write"),
        "run": ("process", "run"),
        "env": ("env", "get"),
    }

    def __init__(self, host):
        self.host = host

    def call(self, name, entry):
        if name not in self.VERB_MAP:
            raise KeyError(
                "E-RUN-VERB-UNREGISTERED: 动词 %r 没有真实宿主映射；已映射：%s"
                % (name, ", ".join(sorted(self.VERB_MAP)))
            )
        try:
            return self._dispatch(name, entry)
        except CapabilityDenied as exc:
            return result.ExecOutcome.failure(
                str(exc),
                host_meta={
                    "denied": {
                        "code": exc.code,
                        "slot": exc.slot,
                        "operation": exc.operation,
                    }
                },
            )
        except HostError as exc:
            return result.ExecOutcome.failure(
                str(exc), host_meta={"host_error": {"code": exc.code}}
            )

    def _dispatch(self, name, entry):
        if name == "read":
            path = _require_text(entry["object"], "read 需要一个文件路径")
            return result.ExecOutcome.success(self.host.fs.read(path))

        if name == "write":
            path = _require_text(entry["object"], "write 需要一个文件路径")
            content = entry["subject"] if entry["subject"] is not None else entry["input"]
            if not isinstance(content, (str, Bytes)):
                raise HostError(
                    "E-HOST-VERB-ARGS", "write 的内容只接受文本或 Bytes"
                )
            return result.ExecOutcome.success(
                self.host.fs.write(path, content), host_meta={"fs": {"path": path}}
            )

        if name == "run":
            command = _require_text(entry["object"], "run 需要一个命令字符串")
            stdin = entry["input"]
            if stdin is not None and not isinstance(stdin, (str, Bytes)):
                raise HostError("E-HOST-VERB-ARGS", "run 的 stdin 只接受文本或 Bytes")
            proc = self.host.process.run(command, stdin=stdin)
            meta = {"process": proc.as_meta()}
            if proc.ok:
                return result.ExecOutcome.success(proc.value, host_meta=meta)
            return result.ExecOutcome.failure(proc.error(), host_meta=meta)

        if name == "env":
            return result.ExecOutcome.success(
                self.host.env.get(_require_text(entry["object"], "env 需要一个变量名"))
            )

        raise KeyError("E-RUN-VERB-UNREGISTERED: 动词 %r 没有真实宿主映射" % name)
