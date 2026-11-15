"""PH-22-T2：``@`` 后直接 verb_call，签名形状可机械比较。

覆盖 E-2 / E-3 / E-14 / E-27。plain python 脚本与 pytest 均可运行。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from support import ParseError, ast, canonical, parse_source, sexpr

# 旧形态在测试里动态拼出，避免 examples/testdata/tests 出现旧形态字面量（E-20）。
OLD = "@" + " " + chr(34)


def _first_def(node):
    for header in node["headers"]:
        if header["kind"] == "FnBlock":
            return header["defs"][0]
    raise AssertionError("没有 //fn{} 定义")


def _shape(text):
    return _first_def(parse_source(text))["shape"]


def test_parse_verb_call_without_name():
    tree = parse_source("//fn{\n@ <read> $path { <read> $path }\n}\n")
    definition = _first_def(tree)
    assert definition["shape"]["verb"] == "read"
    assert definition["shape"]["subject"] == {"role": "none"}
    assert definition["shape"]["object"] == {"role": "param"}
    assert definition["shape"]["preps"] == []
    assert definition["shape"]["adverbs"] == []


def test_parse_subject_and_prep_positions():
    shape = _shape("//fn{\n@ $who <send> $who [to] user { <send> $who [to] user }\n}\n")
    assert shape["subject"] == {"role": "param"}
    assert shape["object"] == {"role": "param"}
    assert shape["preps"] == [
        {"prep": "to", "object": {"role": "const", "value": "user"}}
    ]


def test_parse_adverb_names_and_default_param():
    shape = _shape(
        "//fn{\n@ <send> $msg (friendly, with:smile) [to] $to?user "
        "{ <send> $msg [to] $to }\n}\n"
    )
    assert shape["adverbs"] == ["friendly", "with"]
    assert shape["preps"] == [{"prep": "to", "object": {"role": "param"}}]


def test_pipe_tail_is_not_in_signature():
    definition = _first_def(
        parse_source("//fn{\n@ <read> $p |> <parse> yaml { <read> $p }\n}\n")
    )
    assert definition["shape"]["verb"] == "read"
    assert definition["shape"]["preps"] == []
    assert "yaml" not in sexpr(definition["shape"])
    assert len(definition["template"]) == 2


def test_const_forms_share_one_value():
    first = _shape("//fn{\n@ <send> 'ok' { <send> 'ok' }\n}\n")
    second = _shape('//fn{\n@ <send> "ok" { <send> "ok" }\n}\n')
    third = _shape("//fn{\n@ <send> ok { <send> ok }\n}\n")
    assert first == second == third


def test_fn_def_fields_are_whitelisted():
    assert ast.FIELDS["FnDef"] == ("shape", "template", "body")
    definition = _first_def(parse_source("//fn{\n@ <read> $p { <read> $p }\n}\n"))
    assert set(definition) == {"kind", "shape", "template", "body", "span"}
    assert set(definition["shape"]) == {
        "verb",
        "subject",
        "object",
        "preps",
        "adverbs",
    }
    assert "name" not in definition


def _expect_parse_error(source, code, line, col):
    try:
        parse_source(source)
    except ParseError as exc:
        assert exc.code == code, exc.code
        assert (exc.line, exc.col) == (line, col), (exc.line, exc.col)
        return exc
    raise AssertionError("应报 %s：%r" % (code, source))


def test_old_named_call_is_rejected():
    _expect_parse_error(OLD + 'name" "x"\n', "E-07", 1, 3)


def test_old_named_definition_is_rejected():
    exc = _expect_parse_error(
        "//fn{\n" + OLD + 'name" $x <read> $x { <read> $x }\n}\n', "E-07", 2, 3
    )
    assert exc.hint and "verb_call" in exc.message


def test_old_form_mixed_is_rejected():
    _expect_parse_error(
        "//fn{\n" + OLD + 'a" <read> $x { <read> $x }\n}\n' + OLD + 'a" "x"\n',
        "E-07",
        2,
        3,
    )


def test_old_named_call_without_args_is_rejected():
    _expect_parse_error(OLD + 'name"\n', "E-07", 1, 3)


TESTS = [value for key, value in sorted(globals().items()) if key.startswith("test_")]


def main():
    for test in TESTS:
        test()
    print("PASS phase22 parse: %d 项" % len(TESTS))


if __name__ == "__main__":
    main()
