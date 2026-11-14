"""PH-6-T1：值类型与 Bytes/Opaque 的独立断言。

用法：python3 tests/phase6/test_value.py（退出 0 = 通过）。
不依赖 harness，也不启动 CLI；T1 的交付物只有 value.py，验收只能在这一层做。
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from rill import value


def main():
    kinds = [
        ("x", "string"),
        ("", "string"),
        (1, "number"),
        (1.5, "number"),
        (True, "bool"),
        (False, "bool"),
        (None, "null"),
        ([], "array"),
        ([1], "array"),
        ({}, "object"),
        ({"a": 1}, "object"),
    ]
    for item, want in kinds:
        got = value.kind(item)
        assert got == want, "kind(%r) = %r，期望 %r" % (item, got, want)

    assert value.is_value("x")
    assert value.is_value(0)
    assert value.is_value(None)
    assert not value.is_value(b"raw"), "裸 bytes 不得直接成为 Value，必须包 Bytes"
    assert not value.is_value(object()), "任意 Python 对象不得直接成为 Value"

    raw = value.Bytes(b"\x00\xff")
    assert value.kind(raw) == "bytes"
    assert raw.data == b"\x00\xff"
    assert raw == value.Bytes(b"\x00\xff")
    assert hash(raw) == hash(value.Bytes(b"\x00\xff"))
    try:
        raw.data = b"x"
    except AttributeError:
        pass
    else:
        raise AssertionError("Bytes.data 必须只读")

    handle = value.Opaque("host-handle-1", tag="stream")
    assert value.kind(handle) == "opaque"
    assert handle.handle == "host-handle-1"
    assert handle.tag == "stream"
    assert value.passthrough(handle) is handle
    assert value.passthrough(raw) is raw
    assert value.passthrough("plain") == "plain"

    assert value.truthy(raw) is True
    assert value.truthy(value.Bytes(b"")) is True
    assert value.truthy(handle) is True

    print("PASS value: 11 种值形态、Bytes/Opaque 只读与透传、真值判定")


if __name__ == "__main__":
    main()
