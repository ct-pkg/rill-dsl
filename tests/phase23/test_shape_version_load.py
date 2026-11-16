"""PH-23-T2：loader 收集 ``FnDef`` 时断言 ``shape_version``。

覆盖 E-6 / E-7。plain python 脚本与 pytest 均可运行。
"""

import copy
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "tests", "phase22"))

from support import LoadError, load, parse_source  # noqa: E402

from rill import loader, shape  # noqa: E402

SOURCE = "//fn{\n@ <read> $p { <read> $p }\n}\n"


def _v1_shape():
    return {
        "verb": "read",
        "subject": {"role": "none"},
        "object": {"role": "param"},
        "preps": [],
        "adverbs": [],
    }


def _expect_version_error(tree, definition):
    try:
        loader.check_program(tree)
    except LoadError as exc:
        assert exc.code == "E-LOAD-FN-SHAPE-VERSION", exc.code
        assert (exc.line, exc.col) == (
            definition["span"]["line"],
            definition["span"]["col"],
        ), (exc.line, exc.col, exc.message)
        return exc
    raise AssertionError("旧 shape_version 未被拒")


def test_current_version_is_accepted():
    tables = load(SOURCE)
    assert shape.SHAPE_VERSION == 2
    assert tables.functions[0]["shape"]["shape_version"] == 2


def test_missing_version_is_rejected():
    tree = parse_source(SOURCE)
    definition = tree["headers"][0]["defs"][0]
    definition["shape"] = _v1_shape()
    _expect_version_error(tree, definition)


def test_wrong_version_is_rejected():
    tree = parse_source(SOURCE)
    definition = tree["headers"][0]["defs"][0]
    shape_v1 = _v1_shape()
    shape_v1["shape_version"] = 1
    definition["shape"] = shape_v1
    _expect_version_error(tree, definition)


def test_injected_v1_shape_is_rejected_before_matching():
    tree = parse_source(
        "//fn{\n@ <read> $p { <read> $p }\n}\n//fn{\n@ <write> $p { <write> $p }\n}\n"
    )
    injected = tree["headers"][1]["defs"][0]
    injected["shape"] = copy.deepcopy(injected["shape"])
    del injected["shape"]["shape_version"]
    _expect_version_error(tree, injected)


def test_call_side_is_unaffected():
    tables = load(SOURCE + '@ <read> "a.yml"\n')
    assert len(tables.functions) == 1


TESTS = [value for key, value in sorted(globals().items()) if key.startswith("test_")]


def main():
    for test in TESTS:
        test()
    print("PASS phase23 shape version: %d 项" % len(TESTS))


if __name__ == "__main__":
    main()
