"""PH-11-T1：工具注册表→进程/stdio 能力适配。

用法：python3 tests/phase11/test_tools_process_stdio.py（退出 0 = 通过）。
覆盖 E-1/E-3：run/exec 只经工具、不直接 spawn；工具值即 ``$``；
send 走 send/emit 工具；工具错误只进字符串；CLI 的 agent 宿主可用；
agent 加载期接受 run/env；--fakes 仍然优先。
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from support import (
    entry,
    manifest_doc,
    payload_of,
    run_cli,
    write_json,
    write_manifest,
    write_script,
    write_tools,
)

from rill import lexer, loader, parser
from rill.host.agent import (
    AgentHost,
    AgentVerbRegistry,
    default_agent_policy,
    load_agent_profile,
)
from rill.result import ExecOutcome


class RecordingTools(object):
    """记录工具调用参数；结果由测试给定。"""

    def __init__(self, results=None, names=None):
        self.results = dict(results or {})
        self.names = set(names or self.results)
        self.calls = []

    def has(self, name):
        return name in self.names

    def call(self, name, args):
        self.calls.append((name, args))
        return self.results.get(name, ExecOutcome.success("ok"))


def build(tmp, tools=None, **overrides):
    write_tools(tmp, {})
    path = write_manifest(tmp, **overrides)
    policy = load_agent_profile(path, cwd=tmp)
    host = AgentHost(policy, tools=tools)
    return host, AgentVerbRegistry(host)


def parse_source(text):
    return parser.parse(lexer.tokenize(text))


def case_verb_map_boundary():
    mapping = AgentVerbRegistry.VERB_MAP
    assert mapping["read"] == ("fs", "read"), mapping
    assert mapping["write"] == ("fs", "write"), mapping
    assert mapping["run"] == ("process", "run"), mapping
    assert mapping["env"] == ("env", "get"), mapping
    assert mapping["send"] == ("stdio", "write"), mapping


def case_process_is_tool_not_spawn():
    with tempfile.TemporaryDirectory() as tmp:
        marker = os.path.join(tmp, "spawned.txt")
        tools = RecordingTools(
            {
                "run": ExecOutcome.success(
                    {"code": 0, "stdout": "hi\n", "stderr": ""}
                )
            }
        )
        host, registry = build(tmp, tools=tools)
        outcome = registry.call(
            "run", entry("run", object="touch %s" % marker, input_value="payload")
        )
        assert outcome.ok is True, outcome
        assert outcome.value == {"code": 0, "stdout": "hi\n", "stderr": ""}, outcome.value
        assert not os.path.exists(marker), "agent 宿主不得直接 spawn 进程"
        assert tools.calls == [
            ("run", {"command": "touch %s" % marker, "stdin": "payload"})
        ], tools.calls
        assert outcome.host_meta["process"]["tool"] == "run", outcome.host_meta


def case_exec_alias():
    with tempfile.TemporaryDirectory() as tmp:
        tools = RecordingTools({"exec": ExecOutcome.success("task-1")})
        host, registry = build(tmp, tools=tools)
        outcome = registry.call("run", entry("run", object="deploy"))
        assert outcome.ok is True and outcome.value == "task-1", outcome
        assert outcome.host_meta["process"]["tool"] == "exec", outcome.host_meta


def case_tool_failure_is_string():
    with tempfile.TemporaryDirectory() as tmp:
        tools = RecordingTools(
            {"read": ExecOutcome.failure("E_TOOL_DENIED")}
        )
        host, registry = build(tmp, tools=tools)
        outcome = registry.call("read", entry("read", object="config.yml"))
        assert outcome.ok is False, outcome
        assert outcome.error == "E_TOOL_DENIED", outcome.error
        assert isinstance(outcome.error, str), type(outcome.error)
        assert outcome.host_meta["tool"]["name"] == "read", outcome.host_meta


def case_send_uses_tool():
    with tempfile.TemporaryDirectory() as tmp:
        tools = RecordingTools({"send": ExecOutcome.success(None)})
        host, registry = build(tmp, tools=tools)
        outcome = registry.call("send", entry("send", subject="hello"))
        assert outcome.ok is True, outcome
        assert outcome.value == "hello", outcome.value
        assert tools.calls == [("send", {"text": "hello"})], tools.calls
        assert outcome.host_meta["stdio"]["channel"] == "tool", outcome.host_meta


def case_unregistered_tool():
    policy = default_agent_policy()
    host = AgentHost(policy)
    outcome = AgentVerbRegistry(host).call("read", entry("read", object="x"))
    assert outcome.ok is False, outcome
    assert "E-HOST-TOOL-UNREGISTERED" in outcome.error, outcome.error
    assert host.policy.tools.names == (), host.policy.tools.names


def case_cli_agent_host_is_available():
    with tempfile.TemporaryDirectory() as tmp:
        write_script(tmp, "script.rill", "<read> x\n")
        result = run_cli(["run", "script.rill", "--profile", "agent"], cwd=tmp)
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        payload = payload_of(result)
        assert payload["ok"] is False, payload
        assert "E-HOST-TOOL-UNREGISTERED" in payload["error"], payload
        assert "E-RUN-HOST-UNAVAILABLE" not in payload["error"], payload


def case_cli_agent_tool_value():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "config.txt"), "w", encoding="utf-8") as handle:
            handle.write("REAL\n")
        write_tools(tmp, {"read": {"queue": [{"ok": True, "value": "FAKE"}]}})
        manifest = write_manifest(tmp)
        write_script(tmp, "script.rill", "engineer <read> config.txt\n")
        result = run_cli(
            ["run", "script.rill", "--profile", "agent", "--host-profile", manifest],
            cwd=tmp,
        )
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        payload = payload_of(result)
        assert payload["ok"] is True and payload["value"] == "FAKE", payload
        assert result.stderr == "", result.stderr
        assert payload["host_meta"]["fs"]["path"] == "config.txt", payload


def case_fakes_win_over_agent_host():
    with tempfile.TemporaryDirectory() as tmp:
        write_tools(tmp, {"read": {"queue": [{"ok": True, "value": "HOST"}]}})
        manifest = write_manifest(tmp)
        fakes = write_json(
            os.path.join(tmp, "fakes.json"),
            {
                "schema": "rill-fakes-tools/0",
                "tools": {"read": {"queue": [{"ok": True, "value": "FAKE"}]}},
            },
        )
        write_script(tmp, "script.rill", "<read> config.txt\n")
        result = run_cli(
            [
                "run",
                "script.rill",
                "--profile",
                "agent",
                "--host-profile",
                manifest,
                "--fakes",
                fakes,
            ],
            cwd=tmp,
        )
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        assert payload_of(result)["value"] == "FAKE", payload_of(result)


def case_agent_accepts_host_verbs():
    tables = loader.check_program(parse_source('<run> "echo hi"\n'), "agent")
    assert "run" in tables.verbs and "env" in tables.verbs, tables.verbs
    tables = loader.check_program(parse_source("<env> HOME\n"), "agent")
    assert "env" in tables.verbs, tables.verbs


def main():
    case_verb_map_boundary()
    case_process_is_tool_not_spawn()
    case_exec_alias()
    case_tool_failure_is_string()
    case_send_uses_tool()
    case_unregistered_tool()
    case_cli_agent_host_is_available()
    case_cli_agent_tool_value()
    case_fakes_win_over_agent_host()
    case_agent_accepts_host_verbs()
    print("PASS phase11 tools: run/exec→工具、send→工具、工具错误只进字符串")


if __name__ == "__main__":
    main()
