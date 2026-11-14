"""PH-10-T2：文件与环境能力，以及危险操作的可见拒绝。

用法：python3 tests/phase10/test_fs_env.py（退出 0 = 通过）。
覆盖 E-1 的文件/env 半边：读成功、读缺失、二进制不乱码、写成功、写被拒、
写失败，env 命中与缺失；拒绝信息必须带 ``slot.operation``。
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from support import ROOT  # noqa: F401  （保持 import 路径一致）

from rill.host.shell import (
    CapabilityDenied,
    EnvCapability,
    FsCapability,
    HostError,
    ShellPolicy,
    default_shell_policy,
)
from rill.value import Bytes


def policy(fs=("read",), env=("get",)):
    return ShellPolicy({"fs": list(fs), "env": list(env)})


def case_read_text():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "config.yml")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("port: 8080\n")
        value = FsCapability(policy()).read(path)
        assert value == "port: 8080\n", repr(value)


def case_read_missing():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "missing.yml")
        try:
            FsCapability(policy()).read(path)
        except HostError as exc:
            assert exc.code == "E-HOST-FS-READ", exc.code
            assert "missing.yml" in str(exc), str(exc)
            return
        raise AssertionError("读缺失文件不应成功")


def case_read_binary_is_bytes():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "blob.bin")
        with open(path, "wb") as handle:
            handle.write(b"\x00\xff")
        value = FsCapability(policy()).read(path)
        assert isinstance(value, Bytes), type(value)
        assert value.data == b"\x00\xff", value


def case_write_denied():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "out.txt")
        try:
            FsCapability(policy(fs=("read",))).write(path, "x")
        except CapabilityDenied as exc:
            assert exc.code == "E-HOST-CAPABILITY-DENIED", exc.code
            assert exc.slot == "fs" and exc.operation == "write", exc
            assert "fs.write" in str(exc), str(exc)
            assert not os.path.exists(path), "被拒绝的写入不应落盘"
            return
        raise AssertionError("未声明 fs.write 时不应写文件")


def case_write_allowed():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "out.txt")
        value = FsCapability(policy(fs=("read", "write"))).write(path, "done\n")
        assert value == path, value
        with open(path, encoding="utf-8") as handle:
            assert handle.read() == "done\n"


def case_write_missing_parent():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "no-such-dir", "out.txt")
        try:
            FsCapability(policy(fs=("write",))).write(path, "x")
        except HostError as exc:
            assert exc.code == "E-HOST-FS-WRITE", exc.code
            return
        raise AssertionError("父目录不存在时写入应报 E-HOST-FS-WRITE")


def case_env_hit_and_miss():
    capability = EnvCapability(policy(), env={"RILL_TEST_PORT": "8080"})
    assert capability.get("RILL_TEST_PORT") == "8080"
    try:
        capability.get("RILL_TEST_MISSING")
    except HostError as exc:
        assert exc.code == "E-HOST-ENV-MISSING", exc.code
        assert "RILL_TEST_MISSING" in str(exc), str(exc)
        return
    raise AssertionError("缺失环境变量不应成功")


def case_default_policy_is_read_only():
    default = default_shell_policy()
    assert default.allows("fs", "read") is True
    assert default.allows("fs", "write") is False
    assert default.allows("env", "get") is True


def main():
    case_read_text()
    case_read_missing()
    case_read_binary_is_bytes()
    case_write_denied()
    case_write_allowed()
    case_write_missing_parent()
    case_env_hit_and_miss()
    case_default_policy_is_read_only()
    print("PASS phase10 fs/env: 读/写/拒绝/env 命中与缺失")


if __name__ == "__main__":
    main()
