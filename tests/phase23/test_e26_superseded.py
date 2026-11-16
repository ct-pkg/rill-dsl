"""PH-23-T6：D-024 §判决 6 取代 PH-22 E-26。

E-26 的旧口径是“类型前缀不进签名，file:x 与 text:x 同形并报 E-03”。
D-024 改为字面原文比较：两者是不同形状、可共存；跨前缀调用报 E-04；
引号透明，file:x 与 "file:x" 仍同形。

plain python 脚本与 pytest 均可运行。
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "phase22"))

from support import LoadError, load


def _expect(source, code, line, col):
    try:
        load(source)
    except LoadError as exc:
        assert exc.code == code, (exc.code, exc.message)
        assert (exc.line, exc.col) == (line, col), (exc.line, exc.col, exc.message)
        return exc
    raise AssertionError("应报 %s：%r" % (code, source))


def test_prefixes_are_distinct_and_coexist():
    source = (
        "//fn{\n"
        "@ <send> file:x { <send> file:x }\n"
        "@ <send> text:x { <send> text:x }\n"
        "}\n"
        '@ <send> "file:x"\n'
        '@ <send> "text:x"\n'
    )
    load(source)


def test_cross_prefix_call_is_undeclared():
    source = (
        "//fn{\n"
        "@ <send> file:x { <send> file:x }\n"
        "}\n"
        '@ <send> "text:x"\n'
    )
    _expect(source, "E-04", 4, 1)


def test_quotes_are_transparent_in_const_slot():
    source = (
        "//fn{\n"
        "@ <send> file:x { <send> file:x }\n"
        '@ <send> "file:x" { <send> file:x }\n'
        "}\n"
    )
    _expect(source, "E-03", 3, 1)


TESTS = [value for key, value in sorted(globals().items()) if key.startswith("test_")]


def main():
    for test in TESTS:
        test()
    print("PASS phase23 e26 superseded: %d 项" % len(TESTS))


if __name__ == "__main__":
    main()
