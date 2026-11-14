"""PH-7-T1：`[into]` 按书写顺序执行，失败后后续 `[into]` 不执行。

用法：python3 tests/phase7/test_into.py（退出 0 = 通过）。
本文件只覆盖 trailing `[into]`；独立形式与 `->$x` 顺序在 test_forms.py。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from support import called, events, failure, parse_source, registry, success

from rill.eval_simple import Interpreter


def case_order():
    tree = parse_source(
        "<read> a.yml [into] { <send> $ [to] user } [into] { <write> b.yml }\n"
    )
    verbs = registry(
        {
            "read": [success({"k": "v"})],
            "send": [success(None)],
            "write": [success(None)],
        }
    )
    interp = Interpreter(verbs)
    out = interp.eval_program(tree)

    assert out.ok is True
    assert out.value == {"k": "v"}
    assert called(interp) == ["read", "send", "write"], "into 必须按书写顺序执行"
    assert interp.log[1]["object"] == {"k": "v"}, "块内 $ 应是进入 into 的对象"
    into_values = [entry["value"] for entry in events(interp, "into")]
    assert into_values == [{"k": "v"}, {"k": "v"}], "后续 into 看到前一个结果"


def case_failure_stops_later_into():
    tree = parse_source(
        "<read> a.yml [into] { <send> \"one\" [to] user }"
        " [into] { <read> boom } [into] { <write> b.yml }\n"
    )
    verbs = registry(
        {
            "read": [success("A"), failure("E_INTO")],
            "send": [success(None)],
            "write": [success(None)],
        }
    )
    interp = Interpreter(verbs)
    out = interp.eval_program(tree)

    assert out.ok is False
    assert out.error == "RILL DSL ERROR", "未写 [error] 时默认 break 用规范串"
    assert called(interp) == ["read", "send", "read"], "第三个 into 不得执行"
    flags = [entry["ok"] for entry in events(interp, "into")]
    assert flags == [True, False], "失败 into 之后不再追加 into 事件"


def main():
    case_order()
    case_failure_stops_later_into()
    print("PASS phase7 into: 顺序、块内 $、失败短路")


if __name__ == "__main__":
    main()
