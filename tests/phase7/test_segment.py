"""PH-7-T3：4 种段输出与 `|>` 下游只收 value。

用法：python3 tests/phase7/test_segment.py（退出 0 = 通过）。
golden 在 testdata/0.1.0/expected/run/，轨迹只取段输出与 into 投影。
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from support import ROOT, called, failure, parse_source, registry, success

from rill.eval_simple import Interpreter

GOLDEN = os.path.join(ROOT, "testdata", "0.1.0", "expected", "run")


def load_golden(name):
    with open(os.path.join(GOLDEN, name), encoding="utf-8") as handle:
        return json.load(handle)


def run(source, script):
    interp = Interpreter(registry(script))
    return interp, interp.eval_program(parse_source(source))


def assert_outcome(out, expected):
    assert out.ok is expected["ok"], "ok：期望 %r，实际 %r" % (expected["ok"], out.ok)
    if "value" in expected:
        assert out.value == expected["value"], "value：期望 %r，实际 %r" % (
            expected["value"],
            out.value,
        )
    if "error" in expected:
        assert out.error == expected["error"], "error：期望 %r，实际 %r" % (
            expected["error"],
            out.error,
        )


def case_segment_outputs():
    cases = [
        (
            "success-plain.json",
            "<read> a.yml\n",
            {"read": [success("V")]},
        ),
        (
            "success-ok.json",
            "<read> a.yml [ok] { <send> $ [to] user }\n",
            {"read": [success("V")], "send": [success(None)]},
        ),
        (
            "failure-plain.json",
            "<read> a.yml\n",
            {"read": [failure("boom")]},
        ),
        (
            "failure-error.json",
            "<read> a.yml [error] { <send> $ [to] user }\n",
            {"read": [failure("boom")], "send": [success(None)]},
        ),
    ]
    for name, source, script in cases:
        golden = load_golden(name)
        _, out = run(source, script)
        assert_outcome(out, golden["run"])


def case_into_order_golden():
    golden = load_golden("into-order.json")
    _, out = run(
        "<read> a.yml [into] { <send> $ [to] user } [into] { <write> b.yml }\n",
        {
            "read": [success("host: a\n")],
            "send": [success(None)],
            "write": [success(None)],
        },
    )
    assert_outcome(out, golden["run"])


def case_pipe_passes_value_only():
    interp, out = run(
        "<read> a.yml |> <write> b.yml\n",
        {"read": [success("V")], "write": [success(None)]},
    )
    assert out.ok is True and out.value is None
    assert called(interp) == ["read", "write"]
    assert interp.log[1]["input"] == "V", "下游收到上一段的 value"
    assert not hasattr(interp.log[1]["input"], "ok"), "ok 不向下游传"


def case_pipe_after_ok_block():
    interp, out = run(
        "<read> a.yml [ok] { <send> $ [to] user } |> <write> b.yml\n",
        {
            "read": [success("V")],
            "send": {"queue": [success(None)], "default": success(None)},
            "write": [success(None)],
        },
    )
    assert out.ok is True
    assert interp.log[2]["verb"] == "write"
    assert interp.log[2]["input"] == "V", "[ok] 的段输出才是下游输入"


def case_pipe_after_handled_error():
    interp, out = run(
        "<read> a.yml [error] { <send> $ [to] user } |> <write> b.yml\n",
        {
            "read": [failure("boom")],
            "send": {"queue": [success(None)], "default": success(None)},
            "write": [success(None)],
        },
    )
    assert out.ok is True
    assert interp.log[2]["verb"] == "write"
    assert interp.log[2]["input"] == "boom", "[error] 处理后下游收到 $ 的 value"


def case_pipe_unhandled_failure_stops():
    interp, out = run(
        "<read> a.yml |> <write> b.yml\n",
        {"read": [failure("boom")], "write": [success(None)]},
    )
    assert out.ok is False and out.error == "RILL DSL ERROR"
    assert called(interp) == ["read"], "未处理失败必须中断管道"


def main():
    case_segment_outputs()
    case_into_order_golden()
    case_pipe_passes_value_only()
    case_pipe_after_ok_block()
    case_pipe_after_handled_error()
    case_pipe_unhandled_failure_stops()
    print("PASS phase7 segment: 4 种段输出、into 轨迹、管道只传 value")


if __name__ == "__main__":
    main()
