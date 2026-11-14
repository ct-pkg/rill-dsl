"""PH-11-T6：Agent 工具的真实子进程传输。

用法：python3 tests/phase11/test_tool_transport.py（退出 0 = 通过）。
覆盖 E-8：``command`` 工具由宿主 spawn 真实子进程，请求/响应走 JSON
stdin/stdout；工具侧有本进程之外的副作用；工具超时/坏 JSON 只变
``ok=false``，不冒充 DSL 诊断。
"""

import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from support import (
    HOST_ROOT,
    payload_of,
    run_cli,
    write_json,
    write_manifest,
    write_script,
    write_tools,
)

from rill.host.agent import ToolRegistry

TOOL_SERVER = os.path.join(HOST_ROOT, "tools", "tool_server.py")


def tool_script(directory, name, text):
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def echo_tool(directory, value="from-tool", log_name="tool-calls.log"):
    """返回一个把 pid 写进日志、再回 JSON 的最小工具。"""
    log = os.path.join(directory, log_name)
    return tool_script(
        directory,
        "echo_tool.py",
        "\n".join(
            [
                "import json, os, sys",
                "request = json.load(sys.stdin)",
                "with open(%r, 'a', encoding='utf-8') as handle:" % log,
                "    handle.write(json.dumps({'pid': os.getpid(), 'tool': request['tool']}) + '\\n')",
                "print(json.dumps({'ok': True, 'value': %r}))" % value,
            ]
        ),
    )


def case_registry_accepts_command_spec():
    with tempfile.TemporaryDirectory() as tmp:
        echo_tool(tmp)
        registry = ToolRegistry(
            {"read": {"command": [sys.executable, "echo_tool.py"]}}, cwd=tmp
        )
        assert registry.has("read"), registry.names
        assert registry.has_command("read"), "command 工具没有被识别为真实传输"


def case_tool_leaves_process():
    with tempfile.TemporaryDirectory() as tmp:
        echo_tool(tmp)
        registry = ToolRegistry(
            {"read": {"command": [sys.executable, "echo_tool.py"]}}, cwd=tmp
        )
        outcome = registry.call("read", {"path": "config.txt"})
        assert outcome.ok is True, outcome
        assert outcome.value == "from-tool", outcome.value
        transport = outcome.host_meta.get("transport", {})
        assert transport.get("kind") == "process", outcome.host_meta
        assert isinstance(transport.get("pid"), int), outcome.host_meta
        assert transport["pid"] != os.getpid(), "工具必须跑在独立进程"

        with open(os.path.join(tmp, "tool-calls.log"), encoding="utf-8") as handle:
            calls = [json.loads(line) for line in handle if line.strip()]
        assert calls and calls[0]["pid"] == transport["pid"], calls


def case_transport_failure_is_string():
    with tempfile.TemporaryDirectory() as tmp:
        tool_script(tmp, "bad_tool.py", "print('not-json')\n")
        registry = ToolRegistry(
            {"read": {"command": [sys.executable, "bad_tool.py"]}}, cwd=tmp
        )
        outcome = registry.call("read", {"path": "x"})
        assert outcome.ok is False, outcome
        assert isinstance(outcome.error, str), type(outcome.error)
        assert "E-HOST-TOOL-TRANSPORT" in outcome.error, outcome.error


def case_transport_timeout():
    with tempfile.TemporaryDirectory() as tmp:
        tool_script(tmp, "slow_tool.py", "import time\ntime.sleep(2)\n")
        registry = ToolRegistry(
            {
                "read": {
                    "command": [sys.executable, "slow_tool.py"],
                    "timeout_ms": 50,
                }
            },
            cwd=tmp,
        )
        outcome = registry.call("read", {"path": "x"})
        assert outcome.ok is False, outcome
        assert "E-HOST-TOOL-TIMEOUT" in outcome.error, outcome.error


def case_cli_real_tools_read_and_run():
    assert os.path.isfile(TOOL_SERVER), "缺少 canonical 工具：%s" % TOOL_SERVER
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "tools"))
        shutil.copy(TOOL_SERVER, os.path.join(tmp, "tools", "tool_server.py"))
        with open(os.path.join(tmp, "config.txt"), "w", encoding="utf-8") as handle:
            handle.write("region=cn\n")
        write_tools(
            tmp,
            {
                "read": {"command": [sys.executable, "tools/tool_server.py"]},
                "run": {"command": [sys.executable, "tools/tool_server.py"]},
                "send": {"command": [sys.executable, "tools/tool_server.py"]},
            },
        )
        manifest = write_manifest(tmp)
        write_script(
            tmp,
            "read.rill",
            'engineer <read> file:config.txt |> <send> $ [to] user\n',
        )
        log = os.path.join(tmp, "calls.log")
        result = run_cli(
            ["run", "read.rill", "--profile", "agent", "--host-profile", manifest],
            cwd=tmp,
            env={"RILL_TOOL_LOG": log},
        )
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        payload = payload_of(result)
        assert payload["ok"] is True, payload
        assert payload["value"] == "region=cn\n", payload
        assert result.stderr == "", result.stderr

        with open(log, encoding="utf-8") as handle:
            calls = [json.loads(line) for line in handle if line.strip()]
        assert [item["tool"] for item in calls] == ["read", "send"], calls
        assert all(item["pid"] != os.getpid() for item in calls), calls

        write_script(tmp, "run.rill", 'engineer <run> "printf agent-egress"\n')
        result = run_cli(
            ["run", "run.rill", "--profile", "agent", "--host-profile", manifest],
            cwd=tmp,
            env={"RILL_TOOL_LOG": log},
        )
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        payload = payload_of(result)
        assert payload["ok"] is True, payload
        assert payload["value"]["code"] == 0, payload
        assert payload["value"]["stdout"] == "agent-egress", payload


def case_canonical_manifest_runs_real_tools():
    """canonical manifest 的工具是 command 形态；真实文件内容经工具进程返回。"""
    profile = os.path.join(HOST_ROOT, "profiles", "agent.json")
    script = os.path.join(HOST_ROOT, "real-transport.rill")
    with tempfile.TemporaryDirectory() as tmp:
        log = os.path.join(tmp, "calls.log")
        result = run_cli(
            ["run", script, "--profile", "agent", "--host-profile", profile],
            cwd=HOST_ROOT,
            env={"RILL_TOOL_LOG": log},
        )
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        payload = payload_of(result)
        assert payload["ok"] is True, payload
        assert payload["value"] == "region=cn\n", payload
        assert result.stderr == "", result.stderr
        with open(log, encoding="utf-8") as handle:
            calls = [json.loads(line) for line in handle if line.strip()]
        assert [item["tool"] for item in calls] == ["read", "send"], calls
        assert all(item["pid"] != os.getpid() for item in calls), calls


def main():
    case_registry_accepts_command_spec()
    case_tool_leaves_process()
    case_transport_failure_is_string()
    case_transport_timeout()
    case_cli_real_tools_read_and_run()
    case_canonical_manifest_runs_real_tools()
    print("PASS phase11 transport: command 工具走真实子进程、pid/日志可观察")


if __name__ == "__main__":
    main()
