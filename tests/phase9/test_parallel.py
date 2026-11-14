"""PH-9-T1：parallel 分支三态、源序汇集与分支场域。

用法：python3 tests/phase9/test_parallel.py（退出 0 = 通过）。
覆盖 E-1：成功 / 未处理失败 / 已处理失败三态逐位比对，以及分支内 `$`、
分支作用域、多分支失败取源序第一个错误串。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from support import EvalError, called, events, failure, objects, run, success

SEND = {"queue": [], "default": success(None)}


def branches(interp):
    return events(interp, "branch")


def case_three_state_array():
    source = (
        "parallel {\n"
        "    <read> a.yml\n"
        '    <read> b.yml [error] { break "B_FAIL" }\n'
        "    <read> c.yml\n"
        '    <read> d.yml [error] { <send> "d failed" [to] user }\n'
        "}\n"
    )
    script = {
        "read": {"queue": [
            success("A"),
            failure("E_B"),
            failure("E_C"),
            failure("E_D"),
        ], "default": failure("E_SCRIPT_EXHAUSTED")},
        "send": SEND,
    }
    interp, out = run(source, script)
    assert out.ok is False, out
    assert out.error == "B_FAIL", "应取源序第一个失败分支的错误串：%r" % (out,)
    assert out.value == ["A", None, None, "E_D"], out.value
    assert branches(interp) == [
        {"event": "branch", "index": 0, "ok": True, "value": "A", "error": None},
        {"event": "branch", "index": 1, "ok": False, "value": None, "error": "B_FAIL"},
        {
            "event": "branch",
            "index": 2,
            "ok": False,
            "value": None,
            "error": "RILL DSL ERROR",
        },
        {"event": "branch", "index": 3, "ok": True, "value": "E_D", "error": None},
    ], branches(interp)


def case_all_success_keeps_source_order():
    source = "parallel {\n    <read> a.yml\n    <read> b.yml\n    <read> c.yml\n}\n"
    interp, out = run(
        source,
        {"read": {"queue": [success("A"), success("B"), success("C")], "default": failure()}},
    )
    assert out.ok is True, out
    assert out.value == ["A", "B", "C"], out.value
    assert called(interp) == ["read", "read", "read"], "分支按源序执行"
    assert objects(interp, "read") == ["a.yml", "b.yml", "c.yml"]
    assert [item["index"] for item in branches(interp)] == [0, 1, 2]


def case_branch_dollar_is_not_results_array():
    interp, out = run("parallel {\n    <send> $ [to] user\n}\n", {"send": SEND})
    assert out.ok is True, out
    assert objects(interp, "send") == [None], "分支内 `$` 不是结果数组：%r" % (
        objects(interp, "send"),
    )
    assert out.value == [None], out.value


def case_branch_reads_outer_variable():
    source = (
        'parallel {\n'
        '    <send> $cfg [to] user\n'
        '}\n'
    )
    interp, out = run(source, {"send": SEND}, variables={"cfg": "outer"})
    assert out.ok is True, out
    assert objects(interp, "send") == ["outer"]


def case_branch_scope_does_not_leak():
    source = (
        'parallel {\n'
        '    <send> "x" [to] user ->$local\n'
        '}\n'
        '<send> $local [to] user\n'
    )
    try:
        run(source, {"send": SEND})
    except EvalError as exc:
        assert exc.code == "E-RUN-UNDEFINED", exc.code
        return
    raise AssertionError("分支内新建的 $local 不应泄漏到块外")


def case_empty_parallel():
    interp, out = run("parallel {}\n", {"send": SEND})
    assert out.ok is True, out
    assert out.value == [], out.value
    assert branches(interp) == []


def case_pipe_receives_array_after_success():
    source = "parallel {\n    <read> a.yml\n    <read> b.yml\n} |> <write> out.yml\n"
    interp, out = run(
        source,
        {
            "read": {"queue": [success("A"), success("B")], "default": failure()},
            "write": {"queue": [], "default": success(None)},
        },
    )
    assert out.ok is True, out
    write = [entry for entry in interp.log if entry["verb"] == "write"]
    assert len(write) == 1, interp.log
    assert write[0]["input"] == ["A", "B"], "管道应收到结果数组：%r" % (write[0],)


def case_pipe_skipped_after_failure():
    source = "parallel {\n    <read> a.yml\n} |> <write> out.yml\n"
    interp, out = run(
        source,
        {
            "read": {"queue": [failure("E_A")], "default": failure()},
            "write": {"queue": [], "default": success(None)},
        },
    )
    assert out.ok is False, out
    assert called(interp) == ["read"], "整体失败时管道下游不应执行"


def main():
    case_three_state_array()
    case_all_success_keeps_source_order()
    case_branch_dollar_is_not_results_array()
    case_branch_reads_outer_variable()
    case_branch_scope_does_not_leak()
    case_empty_parallel()
    case_pipe_receives_array_after_success()
    case_pipe_skipped_after_failure()
    print("PASS phase9 parallel: 分支三态、源序、分支 `$` 与作用域")


if __name__ == "__main__":
    main()
