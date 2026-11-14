"""PH-6-T4：fake VerbRegistry 的队列与默认结果。

用法：python3 tests/phase6/test_verbs.py（退出 0 = 通过）。
只验证“只返回可编程结果”，不接真实工具、文件系统或网络。
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from rill import result, verbs


def main():
    registry = verbs.FakeVerbRegistry()
    registry.register(
        "read",
        [result.ExecOutcome.success("a"), result.ExecOutcome.failure("boom")],
        default=result.ExecOutcome.success("default"),
    )
    assert registry.call("read").value == "a"
    first = registry.call("read")
    assert first.ok is False and first.error == "boom"
    assert registry.call("read").value == "default", "队列耗尽必须取 default"
    assert registry.call("read").value == "default"

    registry.register(
        "send",
        [{"ok": True, "value": "sent"}, {"ok": False, "error": "down"}],
        default={"ok": True, "value": "fallback"},
    )
    assert registry.call("send").value == "sent"
    assert registry.call("send").error == "down"
    assert registry.call("send").value == "fallback"

    registry.register("empty", [], default=None)
    missing = registry.call("empty")
    assert missing.ok is False
    assert "无排队结果" in missing.error

    try:
        registry.call("fly")
    except KeyError:
        pass
    else:
        raise AssertionError("未注册动词必须抛 KeyError，不能静默成功")

    assert registry.call("read", arg="ignored").ok is True

    print("PASS verbs: 队列顺序、default、空队列失败、未注册 KeyError")


if __name__ == "__main__":
    main()
