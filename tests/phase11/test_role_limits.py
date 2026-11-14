"""PH-11-T3：角色表与 ExecLimits。

用法：python3 tests/phase11/test_role_limits.py（退出 0 = 通过）。
覆盖 E-3：角色在 exec 前校验、越权/未知角色是 run 诊断；
Shell 继续无角色；steps/time/bytes 超限返回 ok=false + host_meta.limits。
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
    AgentHost,
    AgentRoleError,
    AgentVerbRegistry,
    ExecLimits,
    RoleTable,
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


class Clock(object):
    def __init__(self, values):
        self.values = list(values)

    def __call__(self):
        if len(self.values) > 1:
            return self.values.pop(0)
        return self.values[0]


def build(tmp, tools=None, clock=None, **overrides):
    write_tools(tmp, {})
    manifest = write_manifest(tmp, **overrides)
    policy = load_agent_profile(manifest, cwd=tmp)
    host = AgentHost(policy, clock=clock, tools=tools)
    return host, AgentVerbRegistry(host)


def case_role_table_allows_and_denies():
    table = RoleTable(
        {"engineer": {"verbs": ["read", "write"]}}, "engineer"
    )
    table.require("engineer", "read")
    try:
        table.require("engineer", "run")
    except AgentRoleError as exc:
        assert exc.code == "E-HOST-ROLE-DENIED", exc.code
        assert "engineer" in exc.message and "run" in exc.message, exc.message
    else:
        raise AssertionError("engineer 不应允许 run")

    try:
        table.require("hacker", "read")
    except AgentRoleError as exc:
        assert exc.code == "E-HOST-ROLE-UNKNOWN", exc.code
    else:
        raise AssertionError("未知角色必须报错")


def case_cli_role_denied():
    with tempfile.TemporaryDirectory() as tmp:
        write_tools(
            tmp,
            {
                "read": {"queue": [{"ok": True, "value": "ok"}]},
                "write": {"queue": [{"ok": True, "value": "ok"}]},
            },
        )
        manifest = write_manifest(
            tmp,
            roles={
                "engineer": {"verbs": ["read"]},
                "auditor": {"verbs": ["read", "review"]},
            },
        )
        write_script(tmp, "deny.rill", "auditor <write> out.txt\n")
        result = run_cli(
            ["run", "deny.rill", "--profile", "agent", "--host-profile", manifest],
            cwd=tmp,
        )
        assert result.returncode == 2, (result.returncode, result.stdout, result.stderr)
        error = payload_of(result)["error"]
        assert error["code"] == "E-HOST-ROLE-DENIED", error
        assert "auditor" in error["message"] and "write" in error["message"], error

        write_script(tmp, "unknown.rill", "hacker <read> out.txt\n")
        result = run_cli(
            ["run", "unknown.rill", "--profile", "agent", "--host-profile", manifest],
            cwd=tmp,
        )
        assert result.returncode == 2, (result.returncode, result.stdout)
        assert payload_of(result)["error"]["code"] == "E-HOST-ROLE-UNKNOWN"


def case_default_role_and_omitted_subject():
    with tempfile.TemporaryDirectory() as tmp:
        tools = RecordingTools({"read": ExecOutcome.success("ok")})
        host, registry = build(tmp, tools=tools)
        outcome = registry.call("read", entry("read", object="config.txt"))
        assert outcome.ok is True and outcome.value == "ok", outcome

        # 字面量主语按角色校验；省略主语时用 manifest 的默认角色。
        host.validate_program(
            {
                "kind": "Program",
                "body": [
                    {
                        "kind": "SimpleStmt",
                        "call": {
                            "kind": "VerbCall",
                            "subject": None,
                            "verb": "read",
                            "object": {"kind": "String", "value": "x"},
                            "post": [],
                        },
                    }
                ],
            }
        )


def case_shell_stays_role_free():
    with tempfile.TemporaryDirectory() as tmp:
        write_script(tmp, "script.rill", '<send> "hello" [to] user\n')
        result = run_cli(["run", "script.rill", "--profile", "shell"], cwd=tmp)
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        assert payload_of(result)["ok"] is True, payload_of(result)


def case_steps_limit():
    with tempfile.TemporaryDirectory() as tmp:
        tools = RecordingTools(
            {"read": ExecOutcome.success("one"), "send": ExecOutcome.success(None)}
        )
        host, registry = build(tmp, tools=tools, limits={"steps": 1})
        first = registry.call("read", entry("read", object="a.txt"))
        assert first.ok is True, first
        second = registry.call("read", entry("read", object="b.txt"))
        assert second.ok is False, second
        assert "E-HOST-LIMIT-STEPS" in second.error, second.error
        assert second.host_meta["limits"]["kind"] == "steps", second.host_meta
        assert second.host_meta["limits"]["limit"] == 1, second.host_meta


def case_bytes_limit():
    with tempfile.TemporaryDirectory() as tmp:
        tools = RecordingTools({"read": ExecOutcome.success("x" * 100)})
        host, registry = build(tmp, tools=tools, limits={"bytes": 10})
        outcome = registry.call("read", entry("read", object="a.txt"))
        assert outcome.ok is False, outcome
        assert "E-HOST-LIMIT-BYTES" in outcome.error, outcome.error
        meta = outcome.host_meta["limits"]
        assert meta["kind"] == "bytes" and meta["observed"] > meta["limit"], meta


def case_time_limit():
    with tempfile.TemporaryDirectory() as tmp:
        tools = RecordingTools({"read": ExecOutcome.success("ok")})
        clock = Clock([0.0, 0.0, 0.001, 0.02])
        host, registry = build(
            tmp, tools=tools, clock=clock, limits={"time_ms": 10}
        )
        first = registry.call("read", entry("read", object="a.txt"))
        assert first.ok is True, first
        second = registry.call("read", entry("read", object="b.txt"))
        assert second.ok is True, second
        third = registry.call("read", entry("read", object="c.txt"))
        assert third.ok is False, third
        assert "E-HOST-LIMIT-TIME" in third.error, third.error
        assert third.host_meta["limits"]["kind"] == "time_ms", third.host_meta


def case_exec_limits_shape():
    limits = ExecLimits({"steps": 3, "time_ms": 4, "bytes": 5})
    assert limits.limits == {"steps": 3, "time_ms": 4, "bytes": 5}, limits.limits


def main():
    case_role_table_allows_and_denies()
    case_cli_role_denied()
    case_default_role_and_omitted_subject()
    case_shell_stays_role_free()
    case_steps_limit()
    case_bytes_limit()
    case_time_limit()
    case_exec_limits_shape()
    print("PASS phase11 role/limits: 角色诊断、steps/time/bytes 超限")


if __name__ == "__main__":
    main()
