"""PH-9-T3：`//fn` 参数绑定、默认值与返回值。

用法：python3 tests/phase9/test_fn.py（退出 0 = 通过）。
覆盖 E-3（同名参数去重）、E-4（默认值仅尾部）、E-6（最后一条语句段输出），
以及 `//fn {` 空格容忍与块内 `//` 不再触发 header 特例。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from support import (
    EvalError,
    LoadError,
    ParseError,
    objects,
    parse_source,
    run_loaded,
    success,
)

SEND = {"queue": [], "default": success(None)}
READ = {"queue": [], "default": success("A")}
PARSE = {"queue": [], "default": success("PARSED")}


def case_three_occurrences_one_argument():
    source = (
        "//fn{\n"
        '@ "f" $x <read> $x |> $x <parse> $x {\n'
        "    <send> $x [to] user\n"
        "}\n"
        "}\n"
        '@ "f" "a.yml"\n'
    )
    interp, out = run_loaded(source, {"send": SEND})
    assert out.ok is True, out
    assert objects(interp, "send") == ["a.yml"], "3 处 $x 应绑定同一个实参"


def case_default_tail_can_be_omitted():
    source = (
        "//fn{\n"
        '@ "load" $path <read> $path |> $fmt?yaml <parse> $fmt {\n'
        "    <read> $path |> <parse> $fmt\n"
        "}\n"
        "}\n"
        '@ "load" "a.yml"\n'
    )
    interp, out = run_loaded(
        source,
        {
            "read": {"queue": [], "default": success("A")},
            "parse": {"queue": [], "default": success("PARSED")},
        },
    )
    assert out.ok is True, out
    assert objects(interp, "parse") == ["yaml"], "省略的尾部参数应取默认值"


def case_default_tail_can_be_overridden():
    source = (
        "//fn{\n"
        '@ "load" $path <read> $path |> $fmt?yaml <parse> $fmt {\n'
        "    <read> $path |> <parse> $fmt\n"
        "}\n"
        "}\n"
        '@ "load" "a.yml" "json"\n'
    )
    interp, out = run_loaded(
        source,
        {
            "read": {"queue": [], "default": success("A")},
            "parse": {"queue": [], "default": success("PARSED")},
        },
    )
    assert out.ok is True, out
    assert objects(interp, "parse") == ["json"], "尾部默认值应可被实参覆盖"


def case_default_in_middle_is_rejected():
    source = (
        "//fn{\n"
        '@ "bad" $a?one <read> $a |> $b <parse> $b {\n'
        "    <read> $a\n"
        "}\n"
        "}\n"
        '@ "bad" "x"\n'
    )
    try:
        run_loaded(source, {"read": READ, "parse": PARSE})
    except LoadError as exc:
        assert exc.code == "E-LOAD-FN-DEFAULT-NOT-TAIL", exc.code
        return
    raise AssertionError("中间参数缺省应报错，不能静默按尾部默认值处理")


def case_return_is_last_segment():
    source = (
        "//fn{\n"
        '@ "last-word" $path <read> $path {\n'
        "    <read> $path\n"
        "    <parse> yaml\n"
        "}\n"
        "}\n"
        '@ "last-word" "a.yml" ->$ret\n'
        "<send> $ret [to] user\n"
    )
    interp, out = run_loaded(
        source,
        {
            "read": {"queue": [], "default": success("A")},
            "parse": {"queue": [], "default": success("PARSED")},
            "send": SEND,
        },
    )
    assert out.ok is True, out
    assert objects(interp, "send") == ["PARSED"], "返回值是最后一条语句的段输出"


def case_return_ignores_earlier_value():
    source = (
        "//fn{\n"
        '@ "read-then-send" $path <read> $path {\n'
        "    <read> $path\n"
        '    <send> "done" [to] user\n'
        "}\n"
        "}\n"
        '@ "read-then-send" "a.yml" ->$ret\n'
        "<send> $ret [to] user\n"
    )
    interp, out = run_loaded(
        source,
        {"read": READ, "send": SEND},
    )
    assert out.ok is True, out
    assert objects(interp, "send") == ["done", None], "不能把第一条语句的值当返回"


def case_empty_body_returns_null():
    source = (
        "//fn{\n"
        '@ "noop" $x <read> $x { }\n'
        "}\n"
        '@ "noop" "a.yml"\n'
    )
    interp, out = run_loaded(source, {"read": READ})
    assert out.ok is True, out
    assert out.value is None, out.value


def case_body_dollar_is_call_dollar():
    source = (
        "//fn{\n"
        '@ "selfie" $x <read> $x {\n'
        "    <send> $ [to] user\n"
        "}\n"
        "}\n"
        '@ "selfie" "a.yml"\n'
    )
    interp, out = run_loaded(source, {"read": READ, "send": SEND})
    assert out.ok is True, out
    assert objects(interp, "send") == [None], objects(interp, "send")


def case_body_break_becomes_call_failure():
    source = (
        "//fn{\n"
        '@ "stop" $x <read> $x {\n'
        '    break "F_STOP"\n'
        "}\n"
        "}\n"
        '@ "stop" "a.yml" [error] { <send> $ [to] user }\n'
    )
    interp, out = run_loaded(source, {"read": READ, "send": SEND})
    assert out.ok is True, "调用上的 [error] 应处理函数体 break：%r" % (out,)
    assert objects(interp, "send") == ["F_STOP"], objects(interp, "send")


def case_body_scope_does_not_leak():
    source = (
        "//fn{\n"
        '@ "leak" $x <read> $x {\n'
        '    <send> $x [to] user ->$tmp\n'
        "}\n"
        "}\n"
        '@ "leak" "a.yml"\n'
        "<send> $tmp [to] user\n"
    )
    try:
        run_loaded(source, {"read": READ, "send": SEND})
    except EvalError as exc:
        assert exc.code == "E-RUN-UNDEFINED", exc.code
        return
    raise AssertionError("函数体内新建的 $tmp 不应泄漏到调用方")


def case_body_reads_outer_variable():
    source = (
        "//fn{\n"
        '@ "outer" $x <read> $x {\n'
        "    <send> $cfg [to] user\n"
        "}\n"
        "}\n"
        '@ "outer" "a.yml"\n'
    )
    interp, out = run_loaded(source, {"read": READ, "send": SEND}, variables={"cfg": "OUTER"})
    assert out.ok is True, out
    assert objects(interp, "send") == ["OUTER"], objects(interp, "send")


def case_default_name_conflict_keeps_first():
    source = (
        "//fn{\n"
        '@ "dup" $a?one <read> $a |> $a?two <parse> $a {\n'
        "    <read> $a\n"
        "}\n"
        "}\n"
        '@ "dup"\n'
    )
    interp, out = run_loaded(source, {"read": READ})
    assert out.ok is True, out
    assert objects(interp, "read") == ["one"], "同名默认值冲突取首次出现"


def case_spaced_fn_header():
    source = (
        "//fn {\n"
        '@ "f" $x <read> $x {\n'
        "    <read> $x\n"
        "}\n"
        "}\n"
        '@ "f" "a.yml"\n'
    )
    interp, out = run_loaded(source, {"read": READ})
    assert out.ok is True, out
    assert out.value == "A", out.value


def case_comment_inside_fn_block():
    source = (
        "//fn{\n"
        '@ "f" $x <read> $x {\n'
        "// fn { 这一行在函数体内是注释\n"
        "// map { 这一行同样只是注释\n"
        "    <read> $x\n"
        "}\n"
        "}\n"
        '@ "f" "a.yml"\n'
    )
    interp, out = run_loaded(source, {"read": READ})
    assert out.ok is True, "//fn 块内的 // 不应再触发 header 特例：%r" % (out,)
    assert out.value == "A", out.value


def case_nested_fn_definition_is_rejected():
    source = (
        "//fn{\n"
        '@ "outer" $x <read> $x {\n'
        "//fn{\n"
        '@ "inner" $y <read> $y {\n'
        "    <read> $y\n"
        "}\n"
        "}\n"
        "}\n"
    )
    try:
        parse_source(source)
    except ParseError as exc:
        assert exc.code == "E-PARSE-FN-DEF-BODY", exc.code
        return
    raise AssertionError("嵌套 //fn 不能成为新的区块头")


def main():
    case_three_occurrences_one_argument()
    case_default_tail_can_be_omitted()
    case_default_tail_can_be_overridden()
    case_default_in_middle_is_rejected()
    case_return_is_last_segment()
    case_return_ignores_earlier_value()
    case_empty_body_returns_null()
    case_body_dollar_is_call_dollar()
    case_body_break_becomes_call_failure()
    case_body_scope_does_not_leak()
    case_body_reads_outer_variable()
    case_default_name_conflict_keeps_first()
    case_spaced_fn_header()
    case_comment_inside_fn_block()
    case_nested_fn_definition_is_rejected()
    print("PASS phase9 fn: 去重参数、尾部默认值、返回值、//fn 边界")


if __name__ == "__main__":
    main()
