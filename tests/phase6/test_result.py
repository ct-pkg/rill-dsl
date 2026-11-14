"""PH-6-T2：`{value, ok}` 成败通道与默认错误。

用法：python3 tests/phase6/test_result.py（退出 0 = 通过）。
断言只碰结果模型，不执行语句、不读 AST。
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from rill import result


def main():
    empty_ok = result.ExecOutcome.success("")
    assert empty_ok.ok is True
    assert empty_ok.value == ""
    assert result.triggers_ok(empty_ok) is True, "[ok] 只看 ok，不看 value 真值"
    assert result.triggers_error(empty_ok) is False

    zero_ok = result.ExecOutcome.success(0)
    assert result.triggers_ok(zero_ok) is True

    failed = result.ExecOutcome.failure()
    assert failed.ok is False
    assert failed.error == "RILL DSL ERROR"
    assert failed.value is None
    assert result.triggers_error(failed) is True
    assert result.triggers_ok(failed) is False
    assert result.dollar(failed) == "RILL DSL ERROR"

    custom = result.ExecOutcome.failure("boom")
    assert result.dollar(custom) == "boom"

    assert result.dollar(empty_ok) == ""
    assert result.dollar(result.ExecOutcome.success("x")) == "x"

    with_meta = result.ExecOutcome.success("x", host_meta={"pid": 1}, exit_code=7)
    assert with_meta.host_meta == {"pid": 1}
    assert with_meta.exit_code == 7
    assert result.dollar(with_meta) == "x", "$ 不得混入 host_meta"
    assert result.ExecOutcome.success("x").exit_code is None
    assert result.ExecOutcome.failure("e").exit_code is None

    steps = [
        lambda: result.ExecOutcome.success("a"),
        lambda: result.ExecOutcome.failure("boom"),
        lambda: result.ExecOutcome.success("c"),
    ]
    trace = result.run_top_level(steps)
    assert len(trace) == 2, "顶层未处理失败必须中断后续语句"
    assert trace[0].value == "a"
    assert trace[1].error == "boom"

    handled = [
        lambda: result.ExecOutcome.success("a"),
        lambda: result.ExecOutcome.success("handled"),
        lambda: result.ExecOutcome.success("c"),
    ]
    assert len(result.run_top_level(handled)) == 3

    print("PASS result: ok 只看 ok、默认错误、$ 投影、exit_code 钩子、顶层中断")


if __name__ == "__main__":
    main()
