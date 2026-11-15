"""PH-22-T4：按形状绑定与重复参数冲突。

覆盖 E-11 / E-16。plain python 脚本与 pytest 均可运行。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from support import EvalError, objects, run_loaded, success


def test_repeated_param_equal_is_accepted():
    source = (
        "//fn{\n@ $who <send> $who { <send> $who }\n}\n"
        "@ a <send> a\n"
    )
    interp, out = run_loaded(source, {"send": {"queue": [], "default": success(None)}})
    assert out.ok is True, out
    assert objects(interp, "send") == ["a"]


def test_repeated_param_conflict_is_rejected():
    source = (
        "//fn{\n@ $who <send> $who { <send> $who }\n}\n"
        "@ a <send> b\n"
    )
    try:
        run_loaded(source, {"send": {"queue": [], "default": success(None)}})
    except EvalError as exc:
        assert exc.code == "E-06", exc.code
        return
    raise AssertionError("重复参数位值不等应报 E-06")


def test_tail_default_is_used_when_omitted():
    source = (
        "//fn{\n@ <send> $msg [to] $who?user { <send> $msg [to] $who }\n}\n"
        '@ <send> "hi"\n'
    )
    interp, out = run_loaded(source, {"send": {"queue": [], "default": success(None)}})
    assert out.ok is True, out
    assert objects(interp, "send") == ["hi"]


def test_optional_prep_can_be_given():
    source = (
        "//fn{\n@ <send> $msg [to] $who?user { <send> $msg [to] $who }\n}\n"
        '@ <send> "hi" [to] admin\n'
    )
    interp, out = run_loaded(source, {"send": {"queue": [], "default": success(None)}})
    assert out.ok is True, out
    assert objects(interp, "send") == ["hi"]
    assert interp.log[0]["post"][0]["object"] == "admin"


def test_trailing_block_on_call_is_applied():
    source = (
        "//fn{\n@ <send> $m { <send> $m }\n}\n"
        '@ <send> "hi" [ok] { break "caught" }\n'
    )
    interp, out = run_loaded(source, {"send": {"queue": [], "default": success(None)}})
    assert out.ok is True, out
    assert out.value == "caught"


def test_return_is_last_segment():
    source = (
        "//fn{\n@ <read> $p { <read> $p\n<parse> yaml }\n}\n"
        '@ <read> "a.yml"\n'
    )
    interp, out = run_loaded(
        source,
        {
            "read": {"queue": [], "default": success("A")},
            "parse": {"queue": [], "default": success("PARSED")},
        },
    )
    assert out.ok is True, out
    assert out.value == "PARSED"


def test_empty_body_returns_null():
    source = "//fn{\n@ <read> $p { }\n}\n" '@ <read> "a.yml"\n'
    interp, out = run_loaded(source, {"read": {"queue": [], "default": success("A")}})
    assert out.ok is True, out
    assert out.value is None


def test_subject_and_object_share_one_param():
    source = "//fn{\n@ $x <read> $x { <read> $x }\n}\n" "@ a <read> a\n"
    interp, out = run_loaded(source, {"read": {"queue": [], "default": success("R")}})
    assert out.ok is True, out
    assert objects(interp, "read") == ["a"]


def test_body_new_variable_does_not_leak():
    source = (
        "//fn{\n@ <read> $p { <read> $p ->$tmp }\n}\n"
        '@ <read> "a.yml"\n'
        '<send> $tmp [to] user\n'
    )
    try:
        run_loaded(
            source,
            {
                "read": {"queue": [], "default": success("A")},
                "send": {"queue": [], "default": success(None)},
            },
        )
    except EvalError as exc:
        assert exc.code == "E-RUN-UNDEFINED", exc.code
        return
    raise AssertionError("函数体内新建的变量不应泄漏")


TESTS = [value for key, value in sorted(globals().items()) if key.startswith("test_")]


def main():
    for test in TESTS:
        test()
    print("PASS phase22 eval: %d 项" % len(TESTS))


if __name__ == "__main__":
    main()
