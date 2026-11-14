"""PH-9-T4：函数调用错误码（未声明、名字精确匹配、参数个数）。

用法：python3 tests/phase9/test_errors.py（退出 0 = 通过）。
覆盖 E-5：未声明函数与错误实参个数都在加载期给出稳定错误码与位置；
名字按大小写/连字符精确匹配，不补默认值。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from support import LoadError, tables

FN_ONE = (
    "//fn{\n"
    '@ "one" $x <read> $x {\n'
    "    <read> $x\n"
    "}\n"
    "}\n"
)
FN_TWO = (
    "//fn{\n"
    '@ "two" $x <read> $x |> $y <parse> $y {\n'
    "    <read> $x\n"
    "}\n"
    "}\n"
)
FN_TWO_WITH_DEFAULT = (
    "//fn{\n"
    '@ "two" $x <read> $x |> $y?yaml <parse> $y {\n'
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


def case_undeclared_function():
    expect_load_error(
        '@ "nope" "a.yml"\n', "E-LOAD-FN-UNDECLARED", 1, 1, "nope"
    )


def case_name_is_exact_match():
    expect_load_error(
        FN_ONE + '@ "One" "a.yml"\n', "E-LOAD-FN-UNDECLARED", 6, 1, "One"
    )
    expect_load_error(
        FN_ONE + '@ "one " "a.yml"\n', "E-LOAD-FN-UNDECLARED", 6, 1, "one "
    )


def case_too_few_arguments():
    expect_load_error(
        FN_TWO + '@ "two" "a.yml"\n', "E-LOAD-FN-ARITY", 6, 1, "2"
    )


def case_too_many_arguments():
    expect_load_error(
        FN_TWO + '@ "two" "a.yml" "yaml" "extra"\n', "E-LOAD-FN-ARITY", 6, 1, "2"
    )


def case_tail_default_allows_fewer():
    load = tables(FN_TWO_WITH_DEFAULT + '@ "two" "a.yml"\n')
    assert "two" in load.functions


def main():
    case_undeclared_function()
    case_name_is_exact_match()
    case_too_few_arguments()
    case_too_many_arguments()
    case_tail_default_allows_fewer()
    print("PASS phase9 errors: 未声明、精确名字、少参/多参、尾部默认值")


if __name__ == "__main__":
    main()
