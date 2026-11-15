"""PH-22-T3：形状表与加载期错误。

覆盖 E-4 / E-5 / E-6 / E-7 / E-8 / E-9 / E-10 / E-12 / E-15 / E-26。
plain python 脚本与 pytest 均可运行。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from support import LoadError, load


def _expect(source, code, line, col):
    try:
        load(source)
    except LoadError as exc:
        assert exc.code == code, (exc.code, exc.message)
        assert (exc.line, exc.col) == (line, col), (exc.line, exc.col, exc.message)
        return exc
    raise AssertionError("应报 %s：%r" % (code, source))


def test_duplicate_shape_differs_only_by_param_name():
    source = (
        "//fn{\n"
        "@ <send> $a [to] user { <send> $a [to] user }\n"
        "@ <send> $b [to] user { <send> $b [to] user }\n"
        "}\n"
    )
    exc = _expect(source, "E-03", 3, 1)
    assert "第 2 行" in exc.hint


def test_duplicate_shape_differs_only_by_default():
    source = (
        "//fn{\n"
        "@ <send> $a [to] user { <send> $a [to] user }\n"
        "@ <send> $b?world [to] user { <send> $b [to] user }\n"
        "}\n"
    )
    _expect(source, "E-03", 3, 1)


def test_duplicate_shape_differs_only_by_adverb_value():
    source = (
        "//fn{\n"
        "@ <send> $a (with:smile) { <send> $a }\n"
        "@ <send> $b (with:loud) { <send> $b }\n"
        "}\n"
    )
    _expect(source, "E-03", 3, 1)


def test_type_prefix_does_not_change_shape():
    source = (
        "//fn{\n"
        "@ <send> file:x { <send> file:x }\n"
        "@ <send> text:x { <send> text:x }\n"
        "}\n"
    )
    _expect(source, "E-03", 3, 1)


def test_ambiguous_across_blocks():
    source = (
        "//fn{\n@ <send> $a [to] user { <send> $a [to] user }\n}\n"
        "//fn{\n@ <send> $b [to] user { <send> $b [to] user }\n}\n"
        '@ <send> "hi" [to] user\n'
    )
    exc = _expect(source, "E-05", 7, 1)
    assert "2" in exc.hint and "5" in exc.hint


def test_undeclared_shape_has_no_name():
    exc = _expect('@ <send> "hi" [to] user\n', "E-04", 1, 1)
    assert "同名" not in exc.message
    assert "未声明的函数形状" in exc.message
    assert exc.hint


def test_undeclared_lists_same_verb_shapes():
    source = (
        "//fn{\n@ <send> $a [to] user { <send> $a [to] user }\n}\n"
        '@ <send> "hi" [with] user\n'
    )
    exc = _expect(source, "E-04", 4, 1)
    assert "[to]" in exc.hint and "[with]" in exc.message


def test_arity_missing_required_tail_position():
    source = (
        "//fn{\n@ <send> $msg [to] $who { <send> $msg [to] $who }\n}\n"
        '@ <send> "hi"\n'
    )
    _expect(source, "E-LOAD-FN-ARITY", 4, 1)


def test_arity_middle_skip():
    source = (
        "//fn{\n"
        "@ <send> $m [to] $a [with] $b { <send> $m [to] $a [with] $b }\n"
        "}\n"
        '@ <send> "hi" [with] "w"\n'
    )
    _expect(source, "E-LOAD-FN-ARITY", 4, 1)


def test_tail_default_can_be_omitted():
    source = (
        "//fn{\n@ <send> $msg [to] $who?user { <send> $msg [to] $who }\n}\n"
        '@ <send> "hi"\n'
    )
    tables = load(source)
    assert len(tables.functions) == 1


def test_default_not_tail_is_rejected():
    source = (
        "//fn{\n@ <read> $a?one |> <parse> $b { <read> $a }\n}\n"
        '@ <read> "x"\n'
    )
    _expect(source, "E-LOAD-FN-DEFAULT-NOT-TAIL", 2, 1)


def test_adverb_order_is_ignored():
    source = (
        "//fn{\n@ <send> $m (a, b) { <send> $m }\n}\n"
        '@ <send> "hi" (b, a)\n'
    )
    load(source)


def test_adverb_extra_name_is_undeclared():
    source = (
        "//fn{\n@ <send> $m (a, b) { <send> $m }\n}\n"
        '@ <send> "hi" (a, b, c)\n'
    )
    _expect(source, "E-04", 4, 1)


def test_prep_order_matters():
    source = (
        "//fn{\n@ <send> $m [to] $a [with] $b { <send> $m [to] $a [with] $b }\n}\n"
        '@ <send> "hi" [with] "w" [to] "t"\n'
    )
    _expect(source, "E-04", 4, 1)


def test_trailing_block_is_not_in_signature():
    source = (
        "//fn{\n@ <send> $m [to] user { <send> $m [to] user }\n}\n"
        '@ <send> "hi" [to] user [ok] { break "x" }\n'
    )
    load(source)


def test_direct_verb_call_is_not_a_function_call():
    source = (
        "//fn{\n@ <send> $m [to] user { <send> $m [to] user }\n}\n"
        '<send> "hi" [to] user\n'
    )
    load(source)
    _expect('@ <send> "hi" [to] user\n', "E-04", 1, 1)


def test_two_distinct_shapes_coexist():
    source = (
        "//fn{\n"
        "@ <read> $p { <read> $p }\n"
        "@ <send> $m [to] user { <send> $m [to] user }\n"
        "}\n"
        '@ <read> "a.yml"\n'
        '@ <send> "hi" [to] user\n'
    )
    tables = load(source)
    assert len(tables.functions) == 2


TESTS = [value for key, value in sorted(globals().items()) if key.startswith("test_")]


def main():
    for test in TESTS:
        test()
    print("PASS phase22 load: %d 项" % len(TESTS))


if __name__ == "__main__":
    main()
