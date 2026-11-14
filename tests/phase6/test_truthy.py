"""PH-6-T3：truthy/falsy 集合与 `$` 基准。

用法：python3 tests/phase6/test_truthy.py（退出 0 = 通过）。
只断言值模型与 `$` 投影，不执行语句。
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from rill import result, value


def main():
    falsy = [None, False, 0, 0.0, "", [], {}]
    for item in falsy:
        assert value.truthy(item) is False, "%r 应为 falsy" % (item,)

    truthy = [
        "0",
        "false",
        [0],
        {"a": 1},
        1,
        -1,
        True,
        value.Bytes(b""),
        value.Opaque("h"),
    ]
    for item in truthy:
        assert value.truthy(item) is True, "%r 应为 truthy" % (item,)

    ok = result.ExecOutcome.success("x")
    assert result.dollar(ok) == "x"
    assert result.dollar(result.ExecOutcome.failure("e")) == "e"
    assert result.dollar(result.ExecOutcome.failure()) == "RILL DSL ERROR"

    with_meta = result.ExecOutcome.success("x", host_meta={"pid": 1})
    assert result.dollar(with_meta) == "x", "$ 不得混入 host_meta"

    obj = {"a": 1, "b": {"c": 2}}
    assert result.field(obj, "a") == 1
    assert result.field(obj, "b") == {"c": 2}

    try:
        result.field(obj, "missing")
    except KeyError:
        pass
    else:
        raise AssertionError("缺失字段必须抛 KeyError，不静默返回 null")

    try:
        result.field("not-an-object", "a")
    except TypeError:
        pass
    else:
        raise AssertionError("非对象读字段必须抛 TypeError")

    print("PASS truthy: 6 个 falsy、9 个真值、$ 基准与 .字段")


if __name__ == "__main__":
    main()
