"""PH-11-T2：工具文件与环境能力。

用法：python3 tests/phase11/test_fs_env.py（退出 0 = 通过）。
覆盖 E-1：read/write 只经工具；workspace root 与类型约束；越界是工具错误；
env 只读 manifest context，不暴露 OS 环境变量。
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from support import (
    entry,
    payload_of,
    run_cli,
    write_manifest,
    write_script,
    write_tools,
)

from rill.host.agent import (
    AgentEnvCapability,
    AgentFsCapability,
    AgentHost,
    AgentVerbRegistry,
    load_agent_profile,
)
from rill.result import ExecOutcome


class RecordingTools(object):
    def __init__(self, results=None):
        self.results = dict(results or {})
        self.names = set(self.results)
        self.calls = []

    def has(self, name):
        return name in self.names

    def call(self, name, args):
        self.calls.append((name, args))
        return self.results.get(name, ExecOutcome.success("ok"))


def build(tmp, tools=None, **overrides):
    write_tools(tmp, {})
    manifest = write_manifest(tmp, **overrides)
    policy = load_agent_profile(manifest, cwd=tmp)
    host = AgentHost(policy, tools=tools)
    return host, AgentVerbRegistry(host)


def case_fs_read_inside_workspace():
    with tempfile.TemporaryDirectory() as tmp:
        tools = RecordingTools({"read": ExecOutcome.success("port: 8080\n")})
        host, registry = build(tmp, tools=tools)
        outcome = registry.call("read", entry("read", object="config.txt"))
        assert outcome.ok is True and outcome.value == "port: 8080\n", outcome
        assert tools.calls == [("read", {"path": "config.txt"})], tools.calls
        meta = outcome.host_meta["fs"]
        assert meta["path"] == "config.txt" and meta["root"] == os.path.normpath(tmp), meta


def case_fs_write_inside_workspace():
    with tempfile.TemporaryDirectory() as tmp:
        tools = RecordingTools({"write": ExecOutcome.success(None)})
        host, registry = build(tmp, tools=tools)
        outcome = registry.call(
            "write", entry("write", object="out.txt", subject="copied\n")
        )
        assert outcome.ok is True and outcome.value == "out.txt", outcome
        assert tools.calls == [
            ("write", {"path": "out.txt", "content": "copied\n"})
        ], tools.calls
        assert not os.path.exists(os.path.join(tmp, "out.txt")), "不得越过工具写 OS 文件"


def case_fs_rejects_relative_escape():
    with tempfile.TemporaryDirectory() as tmp:
        tools = RecordingTools({"read": ExecOutcome.success("secret")})
        host, registry = build(tmp, tools=tools)
        outcome = registry.call("read", entry("read", object="../outside.txt"))
        assert outcome.ok is False, outcome
        assert "E-HOST-FS-OUTSIDE" in outcome.error, outcome.error
        assert tools.calls == [], tools.calls
        assert outcome.host_meta["fs"]["code"] == "E-HOST-FS-OUTSIDE", outcome.host_meta


def case_fs_rejects_absolute_escape():
    with tempfile.TemporaryDirectory() as tmp:
        tools = RecordingTools({"read": ExecOutcome.success("secret")})
        host, registry = build(tmp, tools=tools)
        outcome = registry.call("read", entry("read", object="/etc/passwd"))
        assert outcome.ok is False, outcome
        assert "E-HOST-FS-OUTSIDE" in outcome.error, outcome.error
        assert tools.calls == [], tools.calls


def case_fs_absolute_inside_workspace():
    with tempfile.TemporaryDirectory() as tmp:
        tools = RecordingTools({"read": ExecOutcome.success("ok")})
        host, registry = build(tmp, tools=tools)
        target = os.path.join(tmp, "config.txt")
        outcome = registry.call("read", entry("read", object=target))
        assert outcome.ok is True, outcome
        assert tools.calls == [("read", {"path": "config.txt"})], tools.calls


def case_type_slot_path_constraint():
    with tempfile.TemporaryDirectory() as tmp:
        tools = RecordingTools({"read": ExecOutcome.success("typed")})
        host, registry = build(tmp, tools=tools)
        outcome = registry.call("read", entry("read", object="file:config.txt"))
        assert outcome.ok is True and outcome.value == "typed", outcome
        assert outcome.host_meta["fs"]["type"] == "file", outcome.host_meta
        assert tools.calls == [("read", {"path": "config.txt"})], tools.calls

        denied = registry.call("read", entry("read", object="file:../x.txt"))
        assert denied.ok is False, denied
        assert "E-HOST-FS-OUTSIDE" in denied.error, denied.error


def case_env_reads_context_only():
    with tempfile.TemporaryDirectory() as tmp:
        host, registry = build(tmp, context={"RILL_TEST_PORT": "8080"})
        outcome = registry.call("env", entry("env", object="RILL_TEST_PORT"))
        assert outcome.ok is True and outcome.value == "8080", outcome
        assert outcome.host_meta["env"] == {
            "name": "RILL_TEST_PORT",
            "source": "context",
        }, outcome.host_meta

        os.environ["RILL_TEST_SECRET"] = "os-secret"
        try:
            missing = registry.call("env", entry("env", object="RILL_TEST_SECRET"))
        finally:
            os.environ.pop("RILL_TEST_SECRET", None)
        assert missing.ok is False, missing
        assert "E-HOST-ENV-MISSING" in missing.error, missing.error
        assert missing.host_meta["env"]["source"] == "context", missing.host_meta


def case_cli_fs_uses_tool_not_os():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "config.txt"), "w", encoding="utf-8") as handle:
            handle.write("REAL\n")
        write_tools(tmp, {"read": {"queue": [{"ok": True, "value": "FAKE"}]}})
        manifest = write_manifest(tmp)
        write_script(tmp, "script.ri", "<read> config.txt\n")
        result = run_cli(
            ["run", "script.ri", "--profile", "agent", "--host-profile", manifest],
            cwd=tmp,
        )
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        payload = payload_of(result)
        assert payload["value"] == "FAKE", payload
        assert payload["host_meta"]["fs"]["path"] == "config.txt", payload


def case_cli_escape_is_tool_error():
    with tempfile.TemporaryDirectory() as tmp:
        write_tools(tmp, {"read": {"queue": [{"ok": True, "value": "secret"}]}})
        manifest = write_manifest(tmp)
        write_script(tmp, "script.ri", "<read> ../outside.txt\n")
        result = run_cli(
            ["run", "script.ri", "--profile", "agent", "--host-profile", manifest],
            cwd=tmp,
        )
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        payload = payload_of(result)
        assert payload["ok"] is False, payload
        assert payload["error"] == "RILL DSL ERROR", payload
        assert payload["host_meta"]["fs"]["code"] == "E-HOST-FS-OUTSIDE", payload


def case_cli_env_context():
    with tempfile.TemporaryDirectory() as tmp:
        write_tools(tmp, {})
        manifest = write_manifest(tmp, context={"RILL_TEST_PORT": "8080"})
        write_script(tmp, "script.ri", "<env> RILL_TEST_PORT\n")
        result = run_cli(
            ["run", "script.ri", "--profile", "agent", "--host-profile", manifest],
            cwd=tmp,
        )
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        assert payload_of(result)["value"] == "8080", payload_of(result)


def main():
    case_fs_read_inside_workspace()
    case_fs_write_inside_workspace()
    case_fs_rejects_relative_escape()
    case_fs_rejects_absolute_escape()
    case_fs_absolute_inside_workspace()
    case_type_slot_path_constraint()
    case_env_reads_context_only()
    case_cli_fs_uses_tool_not_os()
    case_cli_escape_is_tool_error()
    case_cli_env_context()
    print("PASS phase11 fs/env: workspace 约束、类型表、context-only env")


if __name__ == "__main__":
    main()
