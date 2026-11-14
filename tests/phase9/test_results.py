"""PH-9-T2：`[results]` 的单判据、触发时机与块输出。

用法：python3 tests/phase9/test_results.py（退出 0 = 通过）。
覆盖 E-2：`[results]` 只允许出现在 parallel 尾随块位置；尾随块位、
普通介宾位、独立介宾位、parallel 分支四个位置统一报
`E-PARSE-RESULTS-CONTEXT`。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from support import ParseError, called, objects, parse_source, run, success, failure

SEND = {"queue": [], "default": success(None)}


def expect_results_context(source, line, col):
    try:
        parse_source(source)
    except ParseError as exc:
        assert exc.code == "E-PARSE-RESULTS-CONTEXT", exc.code
        assert (exc.line, exc.col) == (line, col), (exc.line, exc.col, exc.message)
        return
    raise AssertionError("应报 E-PARSE-RESULTS-CONTEXT：%r" % source)


def case_results_only_in_parallel_tail():
    cases = (
        (
            '<read> a.yml [results] { <send> "x" [to] user }\n',
            1,
            14,
        ),
        (
            '<read> a.yml [results] user\n',
            1,
            14,
        ),
        (
            '[results] $x { <send> "x" [to] user }\n',
            1,
            1,
        ),
        (
            'parallel {\n    <read> a.yml [results] { <send> "x" [to] user }\n}\n',
            2,
            17,
        ),
    )
    for source, line, col in cases:
        expect_results_context(source, line, col)


def case_results_block_gets_array_once():
    source = (
        "parallel {\n"
        "    <read> a.yml\n"
        "    <read> b.yml\n"
        "} [results] {\n"
        "    <send> $ [to] user\n"
        "}\n"
    )
    interp, out = run(
        source,
        {
            "read": {"queue": [success("A"), success("B")], "default": failure()},
            "send": SEND,
        },
    )
    assert out.ok is True, out
    assert objects(interp, "send") == [["A", "B"]], "`[results]` 的 `$` 是结果数组"
    assert out.value == ["A", "B"], "parallel 块输出 = [results] 的 `$`"
    events = [entry["event"] for entry in interp.trace]
    assert events.count("results") == 1, "`[results]` 只触发一次：%r" % (events,)
    assert called(interp) == ["read", "read", "send"], "全部完成后才触发"


def case_results_triggers_even_when_failed():
    source = (
        "parallel {\n"
        "    <read> a.yml\n"
        "} [results] {\n"
        "    <send> $ [to] user\n"
        "}\n"
    )
    interp, out = run(
        source,
        {
            "read": {"queue": [failure("E_A")], "default": failure()},
            "send": SEND,
        },
    )
    assert out.ok is False, "分支未处理失败仍让整体失败"
    assert out.error == "RILL DSL ERROR", out.error
    assert objects(interp, "send") == [[None]], "`[results]` 永远触发，失败位为 null"
    assert out.value == [None], out.value


def case_results_block_failure_overrides():
    source = (
        "parallel {\n"
        "    <read> a.yml\n"
        "} [results] {\n"
        '    <send> "x" [to] user [error] { break "R_FAIL" }\n'
        "}\n"
    )
    interp, out = run(
        source,
        {
            "read": {"queue": [success("A")], "default": failure()},
            "send": {"queue": [], "default": failure("E_SEND")},
        },
    )
    assert out.ok is False, out
    assert out.error == "R_FAIL", "`[results]` 块未处理 break 应成为整体错误：%r" % (out,)
    assert objects(interp, "send") == ["x"]


def main():
    case_results_only_in_parallel_tail()
    case_results_block_gets_array_once()
    case_results_triggers_even_when_failed()
    case_results_block_failure_overrides()
    print("PASS phase9 results: 单判据四位置、触发一次、数组 `$` 与失败状态")


if __name__ == "__main__":
    main()
