"""PH-11-T7：宿主契约收口。

用法：python3 tests/phase11/test_host_contract.py（退出 0 = 通过）。
覆盖 E-9/E-10：
- ``--fakes`` 未处理失败退出 1，与真实 Shell 宿主一致；
- harness 把“退出 1 + ok=false”当运行结果，不是内部错误；
- ``E-RUN-HOST-UNAVAILABLE`` 从正常路径退役；
- ``payload.host.profile/principal`` 让调用方识别能力体系；
- 两个宿主共用 parser/lexer/Interpreter，只有能力映射不同；
- 独立 ``[ok]`` / ``[error]`` 的报错给出尾随块绕法。
"""

import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from support import ROOT, payload_of, run_cli, write_json, write_script

from rill.host.agent import AgentVerbRegistry
from rill.host.shell import ShellVerbRegistry

SRC = os.path.join(ROOT, "src")
HARNESS = os.path.join(ROOT, "tools", "check-0.1.0.sh")

FAKES_READ_FAIL = {
    "schema": "rill-fakes-tools/0",
    "tools": {
        "read": {
            "queue": [{"ok": False, "error": "E_FAKE_FAIL"}],
            "default": {"ok": False, "error": "E_FAKE_FAIL"},
        },
        "send": {
            "queue": [{"ok": True, "value": "sent"}],
            "default": {"ok": True, "value": "sent"},
        },
    },
}


def python_sources():
    for base, _, files in os.walk(SRC):
        for name in files:
            if name.endswith(".py"):
                yield os.path.join(base, name)


def case_fakes_unhandled_failure_exits_one():
    with tempfile.TemporaryDirectory() as tmp:
        write_script(tmp, "script.rill", "<read> missing.txt\n")
        fakes = write_json(os.path.join(tmp, "fakes.json"), FAKES_READ_FAIL)
        result = run_cli(
            ["run", "script.rill", "--profile", "shell", "--fakes", fakes], cwd=tmp
        )
        assert result.returncode == 1, (result.returncode, result.stdout, result.stderr)
        payload = payload_of(result)
        assert payload["ok"] is False, payload
        assert payload["error"] == "RILL DSL ERROR", payload


def case_fakes_handled_failure_exits_zero():
    with tempfile.TemporaryDirectory() as tmp:
        write_script(
            tmp,
            "script.rill",
            "<read> missing.txt [error] { <send> $ [to] user }\n",
        )
        fakes = write_json(os.path.join(tmp, "fakes.json"), FAKES_READ_FAIL)
        result = run_cli(
            ["run", "script.rill", "--profile", "shell", "--fakes", fakes], cwd=tmp
        )
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        payload = payload_of(result)
        assert payload["ok"] is True and payload["value"] == "E_FAKE_FAIL", payload


def case_harness_accepts_runtime_failure():
    result = subprocess.run(
        [
            "bash",
            HARNESS,
            "--case",
            "positive/run/segment/failure-plain",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
    assert "PASS" in result.stdout, result.stdout


def case_host_unavailable_is_retired():
    hits = []
    for path in python_sources():
        with open(path, encoding="utf-8") as handle:
            if "E-RUN-HOST-UNAVAILABLE" in handle.read():
                hits.append(os.path.relpath(path, ROOT))
    assert not hits, "E-RUN-HOST-UNAVAILABLE 仍在正常路径：%r" % hits

    with tempfile.TemporaryDirectory() as tmp:
        write_script(tmp, "script.rill", "<read> x\n")
        result = run_cli(["run", "script.rill", "--profile", "agent"], cwd=tmp)
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        payload = payload_of(result)
        assert "E-RUN-HOST-UNAVAILABLE" not in result.stdout, result.stdout
        assert payload["ok"] is False, payload


def case_payload_declares_host_identity():
    with tempfile.TemporaryDirectory() as tmp:
        write_script(tmp, "shell.rill", '<send> "hi" [to] user\n')
        result = run_cli(["run", "shell.rill", "--profile", "shell"], cwd=tmp)
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        shell = payload_of(result)["host"]
        assert shell["profile"] == "shell", shell
        assert shell["principal"]["kind"] == "os-user", shell

        write_script(tmp, "agent.rill", "<read> x\n")
        result = run_cli(["run", "agent.rill", "--profile", "agent"], cwd=tmp)
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        agent = payload_of(result)["host"]
        assert agent["profile"] == "agent", agent
        assert agent["principal"]["kind"] == "role", agent
        assert agent["principal"]["name"] == "default", agent


def case_shared_core_has_single_path():
    for name in ("lexer.py", "parser.py", "loader.py"):
        with open(os.path.join(SRC, "rill", name), encoding="utf-8") as handle:
            text = handle.read()
        assert "rill.host" not in text and "from .host" not in text, (
            "%s 不得 import 宿主能力层" % name
        )

    with open(os.path.join(SRC, "rill", "cli.py"), encoding="utf-8") as handle:
        cli = handle.read()
    assert cli.count("Interpreter(") == 1, "CLI 只应有一处构造 Interpreter"
    assert "Interpreter(verbs" in cli, cli

    slots = ("read", "write", "run", "env", "send")
    for verb in slots:
        assert verb in ShellVerbRegistry.VERB_MAP, verb
        assert verb in AgentVerbRegistry.VERB_MAP, verb
        assert ShellVerbRegistry.VERB_MAP[verb] == AgentVerbRegistry.VERB_MAP[verb], verb


def case_standalone_ok_error_points_to_trailing_block():
    with tempfile.TemporaryDirectory() as tmp:
        write_script(
            tmp,
            "script.rill",
            '<send> "hi" [to] user\n[ok] $x { <send> $x [to] user }\n',
        )
        fakes = write_json(
            os.path.join(tmp, "fakes.json"),
            {
                "schema": "rill-fakes-tools/0",
                "tools": {"send": {"queue": [{"ok": True, "value": None}]}},
            },
        )
        result = run_cli(
            ["run", "script.rill", "--profile", "shell", "--fakes", fakes], cwd=tmp
        )
        assert result.returncode == 2, (result.returncode, result.stdout, result.stderr)
        error = payload_of(result)["error"]
        assert error["code"] == "E-RUN-UNSUPPORTED", error
        assert "尾随块" in error["message"], error


def main():
    case_fakes_unhandled_failure_exits_one()
    case_fakes_handled_failure_exits_zero()
    case_harness_accepts_runtime_failure()
    case_host_unavailable_is_retired()
    case_payload_declares_host_identity()
    case_shared_core_has_single_path()
    case_standalone_ok_error_points_to_trailing_block()
    print("PASS phase11 contract: fakes 退出码、错误码退役、host 身份、共享核心")


if __name__ == "__main__":
    main()
