"""PH-8-T2：`each` 三种输入、每轮作用域与成败、each 级 `[ok]/[error]`。

用法：python3 tests/phase8/test_each.py（退出 0 = 通过）。
覆盖 E-3（null 0 轮 / 空数组 0 轮 / 非数组 1 轮）与 E-4
（失败轮占 null 且继续、each 级触发与 `$`）。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from support import EvalError, called, events, failure, objects, run, success

SEND = {"queue": [], "default": success(None)}
EACH_SEND = 'each $x [in] $v {\n    <send> $x [to] user\n}\n'


def rounds(interp):
    return events(interp, "round")


def case_three_input_shapes():
    interp, out = run(EACH_SEND, {"send": SEND}, {"v": None})
    assert out.ok is False, "null 源应走 error：%r" % (out,)
    assert out.error == "RILL DSL ERROR"
    assert rounds(interp) == [], "null 源不应有轮次"
    assert called(interp) == []

    interp, out = run(EACH_SEND, {"send": SEND}, {"v": []})
    assert out.ok is True and out.value == [], "空数组应 0 轮：%r" % (out,)
    assert rounds(interp) == []
    assert called(interp) == []

    interp, out = run(EACH_SEND, {"send": SEND}, {"v": "solo"})
    assert out.ok is True and out.value == ["solo"], "非数组应单元素一次：%r" % (out,)
    assert len(rounds(interp)) == 1
    assert objects(interp, "send") == ["solo"]


def case_bareword_source_is_string():
    """A2：`each $f [in] xs` 的裸词按 STRING，单元素数组。"""
    interp, out = run(
        'each $f [in] xs {\n    <send> $f [to] user\n}\n', {"send": SEND}
    )
    assert out.ok is True and out.value == ["xs"], out
    assert objects(interp, "send") == ["xs"]


def case_round_dollar_and_var_are_item():
    source = (
        'each $x [in] $v {\n'
        '    <send> $ [to] user\n'
        '    <send> $x [to] user\n'
        '}\n'
    )
    interp, out = run(source, {"send": SEND}, {"v": ["a", "b"]})
    assert out.ok is True and out.value == ["a", "b"], out
    assert objects(interp, "send") == ["a", "a", "b", "b"], (
        "每轮 `$` 与 `$x` 都必须是当前项，不能是整个数组"
    )


def case_round_scope_is_fresh():
    source = (
        'each $x [in] $v {\n'
        '    <send> $x [to] user ->$last\n'
        '}\n'
        '<send> $last [to] user\n'
    )
    try:
        run(source, {"send": SEND}, {"v": ["a"]})
    except EvalError as exc:
        assert exc.code == "E-RUN-UNDEFINED", exc.code
        return
    raise AssertionError("每轮新建的 $last 不应泄漏到块外")


def case_round_failure_continues_with_null():
    source = 'each $x [in] $v {\n    <read> $x\n}\n'
    interp, out = run(
        source,
        {"read": [success("A"), failure("boom"), success("C")]},
        {"v": ["a", "b", "c"]},
    )
    seen = rounds(interp)
    assert [item["ok"] for item in seen] == [True, False, True], seen
    assert [item["value"] for item in seen] == ["A", None, "C"], (
        "失败轮占 null，后续轮继续：%r" % (seen,)
    )
    assert called(interp) == ["read", "read", "read"], "失败不得中断循环"
    assert out.ok is False and out.error == "RILL DSL ERROR"


def case_handled_round_takes_handled_value():
    source = (
        'each $x [in] $v {\n'
        '    <read> $x [error] { <send> $ [to] user }\n'
        '}\n'
    )
    interp, out = run(source, {"read": [failure("boom")], "send": SEND}, {"v": ["a"]})
    seen = rounds(interp)
    assert len(seen) == 1 and seen[0]["ok"] is True, seen
    assert seen[0]["value"] == "boom", "处理后元素应是 [error] 块的最终 `$`"
    assert out.ok is True and out.value == ["boom"], out
    assert objects(interp, "send") == ["boom"]


def case_each_level_ok_array():
    source = (
        'each $x [in] $v {\n'
        '    <read> $x\n'
        '} [ok] {\n'
        '    <send> $ [to] user\n'
        '}\n'
    )
    interp, out = run(
        source,
        {"read": [success("A"), success("B")], "send": SEND},
        {"v": ["a", "b"]},
    )
    assert out.ok is True and out.value == ["A", "B"], out
    assert objects(interp, "send") == [["A", "B"]], "each 级 [ok] 的 `$` 是结果数组"
    assert events(interp, "ok")[0]["triggered"] is True


def case_each_level_error_first_error():
    source = (
        'each $x [in] $v {\n'
        '    <read> $x\n'
        '} [error] {\n'
        '    <send> $ [to] user\n'
        '}\n'
    )
    interp, out = run(
        source, {"read": [failure("boom")], "send": SEND}, {"v": ["a"]}
    )
    assert out.ok is True and out.value == "RILL DSL ERROR", (
        "未处理轮的隐式 [error] 产生规范默认串：%r" % (out,)
    )
    assert objects(interp, "send") == ["RILL DSL ERROR"]
    assert events(interp, "error")[0]["triggered"] is True


def case_each_into_gets_result_array():
    source = (
        'each $x [in] $v {\n'
        '    <read> $x\n'
        '} [into] {\n'
        '    <send> $ [to] user\n'
        '}\n'
    )
    interp, out = run(source, {"read": [success("A")], "send": SEND}, {"v": ["a"]})
    assert out.ok is True and out.value == ["A"], out
    assert objects(interp, "send") == [["A"]]


def case_pipe_source_reuses_segments():
    source = (
        'each $x [in] <search> *.yml |> <parse> yaml {\n'
        '    <send> $x [to] user\n'
        '}\n'
    )
    interp, out = run(
        source,
        {
            "search": [success("names")],
            "parse": [success(["x", "y"])],
            "send": SEND,
        },
    )
    assert out.ok is True and out.value == ["x", "y"], out
    assert called(interp) == ["search", "parse", "send", "send"]
    assert interp.log[1]["input"] == "names", "expr 位管道下游收到上一段 value"
    assert objects(interp, "send") == ["x", "y"]


def main():
    case_three_input_shapes()
    case_bareword_source_is_string()
    case_round_dollar_and_var_are_item()
    case_round_scope_is_fresh()
    case_round_failure_continues_with_null()
    case_handled_round_takes_handled_value()
    case_each_level_ok_array()
    case_each_level_error_first_error()
    case_each_into_gets_result_array()
    case_pipe_source_reuses_segments()
    print("PASS phase8 each: 三形态、每轮作用域、失败轮 null、each 级 ok/error")


if __name__ == "__main__":
    main()
