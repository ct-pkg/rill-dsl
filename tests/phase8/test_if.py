"""PH-8-T1：`if` 条件求值与 truthy/falsy。

用法：python3 tests/phase8/test_if.py（退出 0 = 通过）。
覆盖 E-2：truthy/falsy 与 `[ok]` 的 `ok` 分离；条件四形态
（裸值 / 动词调用 / 带主语 / 管道）在运行期真的归约并求值。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from support import called, failure, objects, run, success

SEND = {"queue": [], "default": success(None)}

IF_ELSE = (
    'if $v {\n'
    '    <send> "T" [to] user\n'
    '} else {\n'
    '    <send> "F" [to] user\n'
    '}\n'
)


def branch_taken(source, script, variables=None):
    interp, out = run(source, script, variables=variables)
    assert out.ok is True, "if 语句后 program 应成功：%r" % (out,)
    seen = objects(interp, "send")
    assert len(seen) == 1, "只应执行一个分支：%r" % (seen,)
    return seen[0]


def case_truthy_falsy_table():
    falsy = [None, False, 0, "", [], {}]
    truthy = [True, 1, -1, "x", [0], {"k": None}]
    for item in falsy:
        assert branch_taken(IF_ELSE, {"send": SEND}, {"v": item}) == "F", (
            "%r 应为 falsy" % (item,)
        )
    for item in truthy:
        assert branch_taken(IF_ELSE, {"send": SEND}, {"v": item}) == "T", (
            "%r 应为 truthy" % (item,)
        )


def case_ok_and_truthy_are_separate():
    """空串是成功的 value，但不是 truthy：`[ok]` 触发，if 走 else。"""
    source = (
        '<read> a.yml [ok] { <send> "ok" [to] user }\n'
        'if <read> a.yml {\n'
        '    <send> "truthy" [to] user\n'
        '} else {\n'
        '    <send> "falsy" [to] user\n'
        '}\n'
    )
    interp, out = run(
        source,
        {
            "read": {"queue": [success(""), success("")], "default": success("")},
            "send": SEND,
        },
    )
    assert out.ok is True
    assert called(interp) == ["read", "send", "read", "send"]
    assert objects(interp, "send") == ["ok", "falsy"]


def case_verb_call_condition():
    assert branch_taken(
        'if <probe> x {\n    <send> "T" [to] user\n} else {\n    <send> "F" [to] user\n}\n',
        {"probe": [success(False)], "send": SEND},
    ) == "F"


def case_subject_condition_is_evaluated():
    """§4.12 示例：`if $cfg <contains> debug=true` 的主语在运行期求值。"""
    source = (
        'if $cfg <contains> debug=true {\n'
        '    <send> "on" [to] user\n'
        '} else {\n'
        '    <send> "off" [to] user\n'
        '}\n'
    )
    interp, out = run(
        source,
        {"contains": [success(True)], "send": SEND},
        variables={"cfg": {"debug": True}},
    )
    assert out.ok is True
    assert called(interp) == ["contains", "send"]
    assert interp.log[0]["subject"] == {"debug": True}, (
        "主语应是求值后的对象：%r" % (interp.log[0]["subject"],)
    )
    assert objects(interp, "send") == ["on"]


def case_else_if_chain():
    source = (
        'if $cfg <contains> debug=true {\n'
        '    <send> "on" [to] user\n'
        '} else-if $cfg <contains> release=true {\n'
        '    <send> "release" [to] user\n'
        '} else {\n'
        '    <send> "off" [to] user\n'
        '}\n'
    )
    interp, out = run(
        source,
        {"contains": [success(False), success(True)], "send": SEND},
        variables={"cfg": {"release": True}},
    )
    assert out.ok is True
    assert called(interp) == ["contains", "contains", "send"]
    assert objects(interp, "send") == ["release"]


def case_pipe_condition_reuses_segments():
    """expr 位管道必须复用段语义：下游收到上一段的 value。"""
    source = (
        'if <read> a.yml |> <parse> yaml {\n'
        '    <send> "yes" [to] user\n'
        '} else {\n'
        '    <send> "no" [to] user\n'
        '}\n'
    )
    interp, out = run(
        source,
        {
            "read": [success("raw")],
            "parse": [success({"format": "yaml"})],
            "send": SEND,
        },
    )
    assert out.ok is True
    assert called(interp) == ["read", "parse", "send"]
    assert interp.log[1]["input"] == "raw", (
        "下游应收到上一段 value：%r" % (interp.log[1]["input"],)
    )
    assert objects(interp, "send") == ["yes"]


def case_condition_failure_stops_if():
    """条件求值失败时 if 不执行任何分支，失败向上传播（缺口 §8 #5）。"""
    source = (
        'if <read> missing.yml {\n'
        '    <send> "T" [to] user\n'
        '} else {\n'
        '    <send> "F" [to] user\n'
        '}\n'
    )
    interp, out = run(source, {"read": [failure("boom")], "send": SEND})
    assert out.ok is False and out.error == "boom", out
    assert called(interp) == ["read"], "条件失败不应执行分支"


def case_falsy_body_uses_dollar():
    """if 体是独立块；顶层进入时 `$` 是 program 输入（null）。"""
    interp, out = run(
        'if $v {\n    <send> $ [to] user\n}\n',
        {"send": SEND},
        {"v": True},
    )
    assert out.ok is True
    assert objects(interp, "send") == [None]


def main():
    case_truthy_falsy_table()
    case_ok_and_truthy_are_separate()
    case_verb_call_condition()
    case_subject_condition_is_evaluated()
    case_else_if_chain()
    case_pipe_condition_reuses_segments()
    case_condition_failure_stops_if()
    case_falsy_body_uses_dollar()
    print("PASS phase8 if: truthy 表、[ok] 分离、主语条件、else-if、条件管道")


if __name__ == "__main__":
    main()
