"""PH-23-T1：常量位按 AST 字面原文比较，定义侧形状键带 ``shape_version``。

覆盖 E-1 / E-2 / E-3 / E-5 / E-8 / E-17。plain python 脚本与 pytest 均可运行。
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "tests", "phase22"))

from support import parse_source  # noqa: E402

from rill import shape  # noqa: E402


def _first_def(text):
    for header in parse_source(text)["headers"]:
        if header["kind"] == "FnBlock":
            return header["defs"][0]
    raise AssertionError("没有 //fn{} 定义")


def _shape(text):
    return _first_def(text)["shape"]


def _call_shape(text):
    for node in parse_source(text)["body"]:
        if node.get("kind") == "CallStmt":
            return shape.shape_of(node["call"], template=False)
    raise AssertionError("没有调用")


def test_type_prefix_is_part_of_const_value():
    left = _shape("//fn{\n@ <send> file:x { <send> file:x }\n}\n")
    right = _shape("//fn{\n@ <send> text:x { <send> text:x }\n}\n")
    assert left != right, "file:x 与 text:x 同形"
    assert left["object"] == {"role": "const", "value": "file:x"}
    assert right["object"] == {"role": "const", "value": "text:x"}


def test_type_prefix_is_not_dropped_against_bare_value():
    prefixed = _shape("//fn{\n@ <send> file:x { <send> file:x }\n}\n")
    plain = _shape("//fn{\n@ <send> x { <send> x }\n}\n")
    assert prefixed != plain, "前缀被剥离后与裸值同形"


def test_quotes_do_not_change_shape():
    as_bare = _shape("//fn{\n@ <send> file:x { <send> file:x }\n}\n")
    as_string = _shape('//fn{\n@ <send> "file:x" { <send> "file:x" }\n}\n')
    assert as_bare == as_string

    single = _shape("//fn{\n@ <send> 'ok' { <send> 'ok' }\n}\n")
    double = _shape('//fn{\n@ <send> "ok" { <send> "ok" }\n}\n')
    bare = _shape("//fn{\n@ <send> ok { <send> ok }\n}\n")
    assert single == double == bare


def test_number_uses_its_canonical_string():
    number = _shape("//fn{\n@ <send> 42 { <send> 42 }\n}\n")
    assert number["object"] == {"role": "const", "value": "42"}


def test_shape_version_is_first_and_definition_only():
    definition = _shape("//fn{\n@ <read> $p { <read> $p }\n}\n")
    assert shape.SHAPE_VERSION == 2
    keys = list(definition)
    assert keys[0] == "shape_version"
    assert definition["shape_version"] == 2
    assert keys.count("shape_version") == 1


def test_call_shape_never_carries_shape_version():
    call = _call_shape('@ <read> "a.yml"\n')
    assert "shape_version" not in call
    assert list(call) == ["verb", "subject", "object", "preps", "adverbs"]


def test_obsolete_p025_comment_is_gone():
    path = os.path.join(ROOT, "src", "rill", "shape.py")
    with open(path, encoding="utf-8") as handle:
        assert "P-025 未裁定前" not in handle.read()


TESTS = [value for key, value in sorted(globals().items()) if key.startswith("test_")]


def main():
    for test in TESTS:
        test()
    print("PASS phase23 shape literal: %d 项" % len(TESTS))


if __name__ == "__main__":
    main()
