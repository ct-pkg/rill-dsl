"""PH-7-T5：独立 `[into]` 三形式与 `->$x` 的 AST 顺序。

用法：python3 tests/phase7/test_forms.py（退出 0 = 通过）。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from support import called, events, parse_source, registry, success

from rill.eval_simple import EvalError, Interpreter


def run(source, script, variables=None):
    interp = Interpreter(registry(script))
    return interp, interp.eval_program(parse_source(source), variables=variables)


def case_independent_into_variable():
    interp, out = run(
        "[into] $cfg { <send> $ [to] user }\n<send> $cfg [to] user\n",
        {"send": {"queue": [], "default": success(None)}},
        variables={"cfg": {"a": 1}},
    )
    assert out.ok is True and out.value == {"a": 1}
    assert interp.log[0]["object"] == {"a": 1}, "独立 into 的 $ 是 $cfg 的值"
    assert interp.log[1]["object"] == {"a": 1}, "$cfg 在块外仍可见"


def case_independent_into_verb():
    interp, out = run(
        "[into] <read> a.yml { <send> $ [to] user }\n",
        {"read": [success("A")], "send": [success(None)]},
    )
    assert out.ok is True and out.value == "A"
    assert called(interp) == ["read", "send"]
    assert interp.log[1]["object"] == "A", "独立 into 的 $ 是动词调用结果"


def case_independent_ok_error_unsupported():
    for source in (
        "[ok] $cfg { <send> \"x\" [to] user }\n",
        "[error] $cfg { <send> \"x\" [to] user }\n",
    ):
        try:
            run(source, {"send": [success(None)]}, variables={"cfg": "v"})
        except EvalError as exc:
            assert exc.code == "E-RUN-UNSUPPORTED", exc.code
        else:
            raise AssertionError("独立 [ok]/[error] 语义未定义，必须显式报错")


def case_assign_before_into():
    interp, out = run(
        "<read> a.yml -> $x [into] { <send> $x [to] user }\n"
        "<send> $x [to] user\n",
        {"read": [success("A")], "send": {"queue": [], "default": success(None)}},
    )
    assert out.ok is True
    assert called(interp) == ["read", "send", "send"]
    assert interp.log[1]["object"] == "A", "-> 先于 into，块内能读到 $x"
    assert interp.log[2]["object"] == "A", "$x 在后续语句仍可见"


def case_assign_after_into_runs_later():
    try:
        run(
            "<read> a.yml [into] { <send> $x [to] user } -> $x\n",
            {"read": [success("A")], "send": [success(None)]},
        )
    except EvalError as exc:
        assert exc.code == "E-RUN-UNDEFINED", exc.code
    else:
        raise AssertionError("-> 写在 into 之后时，块执行时 $x 还不存在")


def case_assign_between_into_blocks():
    interp, out = run(
        "<read> a.yml [into] { <send> \"one\" [to] user }"
        " -> $x [into] { <send> $x [to] user }\n",
        {"read": [success("A")], "send": {"queue": [], "default": success(None)}},
    )
    assert out.ok is True
    assert called(interp) == ["read", "send", "send"]
    assert interp.log[2]["object"] == "A", "第二个 into 看到 assign 后的值"
    into_values = [entry["value"] for entry in events(interp, "into")]
    assert into_values == ["A", "A"]


def main():
    case_independent_into_variable()
    case_independent_into_verb()
    case_independent_ok_error_unsupported()
    case_assign_before_into()
    case_assign_after_into_runs_later()
    case_assign_between_into_blocks()
    print("PASS phase7 forms: 独立 into、assign 顺序、独立 ok/error 显式拒绝")


if __name__ == "__main__":
    main()
