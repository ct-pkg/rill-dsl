"""PH-10-T4：stdio 落点与退出码映射。

用法：python3 tests/phase10/test_stdio_exit.py（退出 0 = 通过）。
覆盖 E-2/E-3：send 写 stderr 且值可观察、stdio 未声明时拒绝、
真实宿主未处理失败按能力清单退出、[error] 处理后退出 0、
--fakes 保持 harness 协议（失败仍退出 0）、Bytes 输出不崩。
"""

import base64
import io
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from support import payload_of, run_cli, write_script

from rill.host.shell import (
    ExitCapability,
    ShellHost,
    ShellPolicy,
    ShellVerbRegistry,
    StdioCapability,
)


def policy(**slots):
    allow = {"process": ["run"], "fs": ["read", "write"], "env": ["get"], "stdio": ["write"]}
    allow.update({key: value for key, value in slots.items()})
    return ShellPolicy(allow)


def entry(verb, subject=None, object=None, input_value=None):
    return {
        "verb": verb,
        "subject": subject,
        "object": object,
        "post": [],
        "input": input_value,
    }


def sent(policy_obj, text=None, input_value=None):
    sink = io.StringIO()
    host = ShellHost(policy_obj)
    host.stdio = StdioCapability(policy_obj, stderr=sink)
    outcome = ShellVerbRegistry(host).call(
        "send", entry("send", subject=text, object=text, input_value=input_value)
    )
    return outcome, sink.getvalue()


def case_send_writes_stderr():
    outcome, captured = sent(policy(), text="hello")
    assert outcome.ok is True, outcome
    assert outcome.value == "hello", outcome.value
    assert outcome.host_meta["stdio"]["channel"] == "stderr", outcome.host_meta
    assert captured == "hello\n", repr(captured)


def case_send_denied():
    denied = ShellPolicy({"stdio": []})
    outcome, captured = sent(denied, text="hello")
    assert outcome.ok is False, outcome
    assert "E-HOST-CAPABILITY-DENIED" in outcome.error, outcome.error
    assert "stdio.write" in outcome.error, outcome.error
    assert captured == "", repr(captured)


def case_exit_capability_maps_table():
    assert ExitCapability(ShellPolicy()).code(True) == 0
    assert ExitCapability(ShellPolicy()).code(False) == 1
    custom = ShellPolicy(exit_codes={"ok": 4, "unhandled": 9})
    assert ExitCapability(custom).code(True) == 4
    assert ExitCapability(custom).code(False) == 9


def case_cli_send_ok():
    with tempfile.TemporaryDirectory() as tmp:
        write_script(tmp, "script.rill", '<send> "hello" [to] user\n')
        result = run_cli(["run", "script.rill", "--profile", "shell"], cwd=tmp)
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        payload = payload_of(result)
        assert payload["ok"] is True and payload["value"] == "hello", payload
        assert "hello" in result.stderr, result.stderr


def case_cli_unhandled_failure_exits_nonzero():
    with tempfile.TemporaryDirectory() as tmp:
        write_script(tmp, "script.rill", "<read> missing.txt\n")
        result = run_cli(["run", "script.rill", "--profile", "shell"], cwd=tmp)
        assert result.returncode == 1, (result.returncode, result.stdout, result.stderr)
        payload = payload_of(result)
        assert payload["ok"] is False, payload
        assert "E-HOST-FS-READ" in payload["error"], payload


def case_cli_handled_failure_exits_zero():
    with tempfile.TemporaryDirectory() as tmp:
        write_script(
            tmp,
            "script.rill",
            '<read> missing.txt [error] { <send> "handled" [to] user }\n',
        )
        result = run_cli(["run", "script.rill", "--profile", "shell"], cwd=tmp)
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        payload = payload_of(result)
        assert payload["ok"] is True and payload["value"] == "handled", payload
        assert "handled" in result.stderr, result.stderr


def case_cli_exit_codes_come_from_profile():
    with tempfile.TemporaryDirectory() as tmp:
        profile = os.path.join(tmp, "custom.json")
        with open(profile, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "schema": "rill.shell-profile/0",
                    "name": "custom",
                    "allow": {"fs": ["read"]},
                    "exit_codes": {"ok": 0, "unhandled": 7},
                },
                handle,
            )
        write_script(tmp, "script.rill", "<read> missing.txt\n")
        result = run_cli(
            ["run", "script.rill", "--profile", "shell", "--host-profile", profile],
            cwd=tmp,
        )
        assert result.returncode == 7, (result.returncode, result.stdout, result.stderr)


def case_fakes_keep_harness_exit_code():
    with tempfile.TemporaryDirectory() as tmp:
        write_script(tmp, "script.rill", "<read> missing.txt\n")
        fakes = os.path.join(tmp, "fakes.json")
        with open(fakes, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "schema": "rill-fakes-tools/0",
                    "tools": {
                        "read": {
                            "queue": [{"ok": False, "error": "E_FAKE_FAIL"}],
                            "default": {"ok": False, "error": "E_FAKE_FAIL"},
                        }
                    },
                },
                handle,
            )
        result = run_cli(
            ["run", "script.rill", "--profile", "shell", "--fakes", fakes], cwd=tmp
        )
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        payload = payload_of(result)
        assert payload["ok"] is False and payload["error"] == "E_FAKE_FAIL", payload


def case_bytes_survive_json_output():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "blob.bin"), "wb") as handle:
            handle.write(b"\x00\xff")
        write_script(tmp, "script.rill", "<read> blob.bin\n")
        result = run_cli(["run", "script.rill", "--profile", "shell"], cwd=tmp)
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        payload = payload_of(result)
        assert payload["value"] == {
            "$bytes": base64.b64encode(b"\x00\xff").decode("ascii")
        }, payload


def main():
    case_send_writes_stderr()
    case_send_denied()
    case_exit_capability_maps_table()
    case_cli_send_ok()
    case_cli_unhandled_failure_exits_nonzero()
    case_cli_handled_failure_exits_zero()
    case_cli_exit_codes_come_from_profile()
    case_fakes_keep_harness_exit_code()
    case_bytes_survive_json_output()
    print("PASS phase10 stdio/exit: send→stderr、退出码表、fakes 协议、Bytes 输出")


if __name__ == "__main__":
    main()
