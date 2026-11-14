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
    CapabilityDenied,
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
    sink = io.StringIO()
    host = ShellHost(denied)
    host.stdio = StdioCapability(denied, stderr=sink)
    try:
        ShellVerbRegistry(host).call("send", entry("send", object="hello"))
    except CapabilityDenied as exc:
        assert "stdio.write" in str(exc), str(exc)
        assert sink.getvalue() == "", repr(sink.getvalue())
        return
    raise AssertionError("未声明 stdio.write 时应拒绝输出")


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
        # §4.10 的隐式 [error]：未处理失败的 DSL 层错误串固定为规范串。
        assert payload["error"] == "RILL DSL ERROR", payload


def case_cli_denial_is_diagnostic():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "in.txt"), "w", encoding="utf-8") as handle:
            handle.write("x")
        write_script(tmp, "script.rill", "<read> in.txt |> <write> out.txt\n")
        result = run_cli(["run", "script.rill", "--profile", "shell"], cwd=tmp)
        assert result.returncode == 2, (result.returncode, result.stdout, result.stderr)
        error = payload_of(result)["error"]
        assert error["code"] == "E-HOST-CAPABILITY-DENIED", error
        assert "fs.write" in error["message"], error
        assert not os.path.exists(os.path.join(tmp, "out.txt"))


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
        # [error] 块内没有改写 $，块输出仍是错误串（PH-7 的块输出规则）。
        assert payload["ok"] is True, payload
        assert "E-HOST-FS-READ" in payload["value"], payload
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
        write_script(
            tmp,
            "script.rill",
            "<read> missing.txt [error] { <send> $ [to] user }\n",
        )
        fakes = os.path.join(tmp, "fakes.json")
        with open(fakes, "w", encoding="utf-8") as handle:
            json.dump(
                {
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
                },
                handle,
            )
        result = run_cli(
            ["run", "script.rill", "--profile", "shell", "--fakes", fakes], cwd=tmp
        )
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        payload = payload_of(result)
        # 错误串来自 fake（真实宿主会给 E-HOST-FS-READ），证明 fake 路径优先。
        assert payload["ok"] is True and payload["value"] == "E_FAKE_FAIL", payload


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
    case_cli_denial_is_diagnostic()
    case_cli_handled_failure_exits_zero()
    case_cli_exit_codes_come_from_profile()
    case_fakes_keep_harness_exit_code()
    case_bytes_survive_json_output()
    print("PASS phase10 stdio/exit: send→stderr、退出码表、fakes 协议、Bytes 输出")


if __name__ == "__main__":
    main()
