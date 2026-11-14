"""PH-7-T2：`[ok]/[error]` 触发、`$` 取值与 `[into]` 失败后的用户 `[error]`。

用法：python3 tests/phase7/test_ok_error.py（退出 0 = 通过）。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from support import called, events, failure, parse_source, registry, success

from rill.eval_simple import Interpreter


def run(source, script, variables=None):
    interp = Interpreter(registry(script))
    return interp, interp.eval_program(parse_source(source), variables=variables)


def case_ok_block_sees_value():
    interp, out = run(
        "<read> a.yml [ok] { <send> $ [to] user }\n",
        {"read": [success("V")], "send": {"queue": [success(None)], "default": success(None)}},
    )
    assert out.ok is True and out.value == "V"
    assert interp.log[1]["object"] == "V", "[ok] 块内 $ 是段成功结果"
    triggered = events(interp, "ok")
    assert triggered == [{"event": "ok", "triggered": True, "value": "V"}]


def case_error_block_sees_error_string():
    interp, out = run(
        "<read> a.yml [error] { <send> $ [to] user }\n",
        {"read": [failure("boom")], "send": [success(None)]},
    )
    assert out.ok is True, "[error] 处理且未 break 后按 §4.6 继续"
    assert out.value == "boom"
    assert interp.log[1]["object"] == "boom", "[error] 块内 $ 是错误串"
    triggered = events(interp, "error")
    assert triggered == [{"event": "error", "triggered": True, "value": "boom"}]


def case_empty_success_still_triggers_ok():
    interp, out = run(
        "<read> a.yml [ok] { <send> $ [to] user }\n",
        {"read": [success("")], "send": [success(None)]},
    )
    assert out.ok is True and out.value == ""
    assert interp.log[1]["object"] == "", "[ok] 只看 ok，不按 value 真值"


def case_failure_without_error_defaults_to_break():
    interp, out = run(
        "<read> a.yml\n",
        {"read": [failure("boom")]},
    )
    assert out.ok is False
    assert out.value is None
    assert out.error == "RILL DSL ERROR"


def case_ok_does_not_fire_on_failure_and_error_not_on_success():
    interp, out = run(
        "<read> a.yml [ok] { <send> \"ok\" [to] user }\n",
        {"read": [failure("boom")], "send": [success(None)]},
    )
    assert out.ok is False and out.error == "RILL DSL ERROR"
    assert events(interp, "ok") == [{"event": "ok", "triggered": False, "value": None}]
    assert called(interp) == ["read"], "失败时 [ok] 块不得执行"

    interp, out = run(
        "<read> a.yml [error] { <send> \"err\" [to] user }\n",
        {"read": [success("V")], "send": {"queue": [success(None)], "default": success(None)}},
    )
    assert out.ok is True and out.value == "V"
    assert events(interp, "error") == [
        {"event": "error", "triggered": False, "value": None}
    ]
    assert called(interp) == ["read"], "成功时 [error] 块不得执行"


def case_into_runs_before_ok():
    interp, out = run(
        "<read> a.yml [into] { <send> \"into\" [to] user }"
        " [ok] { <send> $ [to] user }\n",
        {"read": [success("V")], "send": {"queue": [success(None)], "default": success(None)}},
    )
    assert out.ok is True and out.value == "V"
    assert called(interp) == ["read", "send", "send"], "[into] 必须先于 [ok]"
    assert interp.log[1]["object"] == "into"
    assert interp.log[2]["object"] == "V", "[ok] 的 $ 是最终 value，不是 into 块输出"


def case_into_failure_goes_to_user_error():
    interp, out = run(
        "<read> a.yml [into] { <read> boom } [error] { <send> $ [to] user }\n",
        {
            "read": [success("A"), failure("E_INTO")],
            "send": [success(None)],
        },
    )
    assert out.ok is True, "[into] 失败后用户 [error] 处理，段算 handled"
    assert out.value == "RILL DSL ERROR", "块内未处理失败按 §4.10 默认 break 规范串"
    assert called(interp) == ["read", "read", "send"], "失败 into 后不得继续后续块"
    assert interp.log[2]["object"] == "RILL DSL ERROR"


def main():
    case_ok_block_sees_value()
    case_error_block_sees_error_string()
    case_empty_success_still_triggers_ok()
    case_failure_without_error_defaults_to_break()
    case_ok_does_not_fire_on_failure_and_error_not_on_success()
    case_into_runs_before_ok()
    case_into_failure_goes_to_user_error()
    print("PASS phase7 ok/error: 触发条件、$ 取值、into 失败转用户 error")


if __name__ == "__main__":
    main()
