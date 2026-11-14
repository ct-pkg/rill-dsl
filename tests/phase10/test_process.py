"""PH-10-T1：进程能力。

用法：python3 tests/phase10/test_process.py（退出 0 = 通过）。
覆盖 E-1/E-2 的进程半边：成功、非零退出、stdin 文本、stdin 二进制、timeout，
以及 profile 未声明 process 能力时的可观察拒绝。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from support import ROOT

from rill.host.shell import (
    CapabilityDenied,
    ProcessCapability,
    ShellPolicy,
    default_shell_policy,
)
from rill.value import Bytes


def policy(process=("run",)):
    return ShellPolicy({"process": list(process)})


def case_success():
    result = ProcessCapability(policy(), cwd=ROOT).run("python3 -c \"print('hi')\"")
    assert result.ok is True, result
    assert result.code == 0, result
    assert result.stdout == "hi\n", repr(result.stdout)
    assert result.stderr == "", repr(result.stderr)
    assert result.argv == ["python3", "-c", "print('hi')"], result.argv
    assert result.timed_out is False


def case_nonzero_exit():
    result = ProcessCapability(policy(), cwd=ROOT).run(
        "python3 -c \"import sys; sys.stderr.write('bad'); sys.exit(3)\""
    )
    assert result.ok is False, result
    assert result.code == 3, result
    assert result.stderr == "bad", repr(result.stderr)
    meta = result.as_meta()
    assert meta["code"] == 3 and meta["stderr"] == "bad", meta


def case_stdin_text():
    result = ProcessCapability(policy(), cwd=ROOT).run(
        "python3 -c \"import sys; sys.stdout.write(sys.stdin.read().upper())\"",
        stdin="abc\n",
    )
    assert result.ok is True, result
    assert result.stdout == "ABC\n", repr(result.stdout)


def case_stdin_bytes():
    result = ProcessCapability(policy(), cwd=ROOT).run(
        "python3 -c \"import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())\"",
        stdin=Bytes(b"\x00\xff"),
    )
    assert result.ok is True, result
    assert isinstance(result.stdout, Bytes), type(result.stdout)
    assert result.stdout.data == b"\x00\xff", result.stdout


def case_timeout_is_observable():
    result = ProcessCapability(policy(), cwd=ROOT, timeout=0.2).run(
        "python3 -c \"import time; time.sleep(1)\""
    )
    assert result.timed_out is True, result
    assert result.ok is False, result
    assert result.as_meta()["timed_out"] is True, result.as_meta()


def case_denied_without_capability():
    try:
        ProcessCapability(policy(()), cwd=ROOT).run("echo hi")
    except CapabilityDenied as exc:
        assert exc.code == "E-HOST-CAPABILITY-DENIED", exc.code
        assert exc.slot == "process", exc.slot
        assert exc.operation == "run", exc.operation
        assert "process.run" in str(exc), str(exc)
        return
    raise AssertionError("未声明 process 能力时不应执行进程")


def case_default_policy_denies_process():
    assert default_shell_policy().allows("process", "run") is False


def main():
    case_success()
    case_nonzero_exit()
    case_stdin_text()
    case_stdin_bytes()
    case_timeout_is_observable()
    case_denied_without_capability()
    case_default_policy_denies_process()
    print("PASS phase10 process: 成功/非零/stdin 文本与二进制/timeout/拒绝")


if __name__ == "__main__":
    main()
