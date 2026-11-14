"""PH-8-T3：`break` 场域与 each+break 三组合。

用法：python3 tests/phase8/test_break.py（退出 0 = 通过）。
覆盖 E-5：顶层 / 管道 / 循环三场域；each 内 break、失败轮后 break、
裸词 break（A2 按字符串）；`->$var` 由场域外部捕捉。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from support import called, events, failure, objects, run, success

SEND = {"queue": [], "default": success(None)}


def case_top_level_break_stops_program():
    source = (
        '<send> "before" [to] user\n'
        'break "done"\n'
        '<send> "after" [to] user\n'
    )
    interp, out = run(source, {"send": SEND})
    assert out.ok is True and out.value == "done", out
    assert called(interp) == ["send"], "顶层 break 应中断整个 program"
    assert objects(interp, "send") == ["before"]


def case_top_level_bareword_break_is_string():
    interp, out = run("break done\n", {})
    assert out.ok is True and out.value == "done", "裸词应按 STRING：%r" % (out,)


def case_pipe_break_stops_pipe_only():
    """§4.6：`[error]` 内 break 只中断管道，后面的语句继续。"""
    source = (
        '<read> a.yml |> <write> b.yml [error] { break "halt" }\n'
        '<send> "after" [to] user\n'
    )
    interp, out = run(
        source,
        {
            "read": [success("V")],
            "write": [failure("boom")],
            "send": SEND,
        },
    )
    assert out.ok is True, out
    assert called(interp) == ["read", "write", "send"], "break 不应中断 program"
    assert objects(interp, "send") == ["after"]


def case_pipe_break_skips_downstream():
    source = (
        '<read> a.yml |> <write> b.yml [error] { break "halt" } '
        '|> <send> "last" [to] user\n'
    )
    interp, out = run(
        source,
        {
            "read": [success("V")],
            "write": [failure("boom")],
            "send": SEND,
        },
    )
    assert called(interp) == ["read", "write"], "break 之后的下游不得执行"
    assert out.ok is True and out.value == "halt", out


def case_each_break_ends_loop():
    source = (
        'each $x [in] $v {\n'
        '    <send> $x [to] user\n'
        '    break "stop" -> $err\n'
        '    <send> "never" [to] user\n'
        '}\n'
        '<send> $err [to] user\n'
        '<send> "after" [to] user\n'
    )
    interp, out = run(source, {"send": SEND}, {"v": ["a", "b"]})
    assert out.ok is True, out
    assert objects(interp, "send") == ["a", "stop", "after"], (
        "each 内 break 应结束循环、捕获变量可读、外层继续"
    )
    assert len(events(interp, "round")) == 1, "break 之后不再开新轮"


def case_each_break_after_failure():
    """某轮失败后在 `[error]` 内 break：循环结束，错误值被捕捉。"""
    source = (
        'each $x [in] $v {\n'
        '    <read> $x [error] { break "stop" -> $err }\n'
        '}\n'
        '<send> $err [to] user\n'
    )
    interp, out = run(
        source, {"read": [failure("boom")], "send": SEND}, {"v": ["a", "b"]}
    )
    assert out.ok is True, out
    assert called(interp) == ["read", "send"], "break 之后不得进入第二轮"
    assert objects(interp, "send") == ["stop"]
    seen = events(interp, "round")
    assert len(seen) == 1 and seen[0]["ok"] is False, seen


def case_each_bareword_break_is_string():
    """A2：`break done` 的裸词按 STRING 进入捕捉变量。"""
    source = (
        'each $x [in] $v {\n'
        '    break done -> $err\n'
        '}\n'
        '<send> $err [to] user\n'
    )
    interp, out = run(source, {"send": SEND}, {"v": ["a"]})
    assert out.ok is True, out
    assert objects(interp, "send") == ["done"], "裸词 break 的值应是字符串 done"


def case_if_body_break_leaves_if_domain():
    """普通块不吞 break：穿到最近的 program 场域。"""
    source = (
        'if $v {\n'
        '    <send> "in" [to] user\n'
        '    break "stop"\n'
        '}\n'
        '<send> "after" [to] user\n'
    )
    interp, out = run(source, {"send": SEND}, {"v": True})
    assert out.ok is True and out.value == "stop", out
    assert objects(interp, "send") == ["in"], "if 之后的语句不得执行"


def case_block_break_captured_by_outer_scope():
    """`[into]` 块内 break：管道场域结束，`->$var` 写回外层。"""
    source = (
        '<read> a.yml [into] { break "halt" -> $err } |> <send> "down" [to] user\n'
        '<send> $err [to] user\n'
    )
    interp, out = run(
        source, {"read": [success("V")], "send": SEND}
    )
    assert called(interp) == ["read", "send"], "管道下游不得执行"
    assert objects(interp, "send") == ["halt"], "break 值应写回外层变量"


def main():
    case_top_level_break_stops_program()
    case_top_level_bareword_break_is_string()
    case_pipe_break_stops_pipe_only()
    case_pipe_break_skips_downstream()
    case_each_break_ends_loop()
    case_each_break_after_failure()
    case_each_bareword_break_is_string()
    case_if_body_break_leaves_if_domain()
    case_block_break_captured_by_outer_scope()
    print("PASS phase8 break: 三场域、each+break 三组合、裸词捕捉")


if __name__ == "__main__":
    main()
