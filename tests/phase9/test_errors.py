"""PH-9-T4（PH-22 迁移）：函数加载期错误码（形状未声明、参数个数、轮廓）。

用法：python3 tests/phase9/test_errors.py（退出 0 = 通过）。
覆盖 E-5：未声明形状与参数个数不符都在加载期给出稳定错误码与位置；
函数不再有名字，按形状键精确匹配。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from support import LoadError, tables

FN_ONE = (
    "//fn{\n"
    "@ <read> $x {\n"
    "    <read> $x\n"
    "}\n"
    "}\n"
)
FN_TWO = (
    "//fn{\n"
    "@ <read> $x |> <parse> $y {\n"
    "    <read> $x\n"
    "}\n"
    "}\n"
)
FN_TWO_WITH_DEFAULT = (
    "//fn{\n"
    "@ <read> $x |> <parse> $y?yaml {\n"
    "    <read> $x\n"
    "}\n"
    "}\n"
)


def expect_load_error(source, code, line, col, contains):
    try:
        tables(source)
    except LoadError as exc:
        assert exc.code == code, exc.code
        assert (exc.line, exc.col) == (line, col), (exc.line, exc.col, exc.message)
        assert contains in exc.message, exc.message
        return
    raise AssertionError("应报 %s：%r" % (code, source))


def case_undeclared_shape():
    expect_load_error(
        '@ <read> "a.yml"\n', "E-04", 1, 1, "未声明的函数形状"
    )


def case_shape_is_exact_match():
    expect_load_error(
        FN_ONE + '@ <send> "a.yml"\n', "E-04", 6, 1, "未声明的函数形状"
    )
    expect_load_error(
        FN_ONE + '@ <read> "a.yml" [to] user\n', "E-04", 6, 1, "未声明的函数形状"
    )


def case_missing_required_position():
    expect_load_error(
        FN_TWO + '@ <send> $x [to] $y\n', "E-04", 6, 1, "未声明的函数形状"
    )


def case_tail_default_allows_fewer():
    load = tables(FN_TWO_WITH_DEFAULT + '@ <read> "a.yml"\n')
    assert len(load.functions) == 1


def main():
    case_undeclared_shape()
    case_shape_is_exact_match()
    case_missing_required_position()
    case_tail_default_allows_fewer()
    print("PASS phase9 errors: 未声明形状、精确形状、缺位、尾部默认值")


if __name__ == "__main__":
    main()
