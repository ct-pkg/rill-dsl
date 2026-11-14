"""PH-6-T5：`expr` / `simple_stmt` 两条管道的值传播与 each 轮归约。

用法：python3 tests/phase6/test_pipe.py（退出 0 = 通过）。
断言只碰值传播模型，不执行 AST、不调度尾随块。
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from rill import pipe, result


def recorder(log, name, outcome):
    def call(value):
        log.append((name, value))
        return outcome

    return call


def downstream(log):
    def call(value):
        log.append(("downstream", value))
        return result.ExecOutcome.success("never")

    return call


def main():
    log = []
    expr_hops = [
        pipe.ExprPipeHop(recorder(log, "a", result.ExecOutcome.success("a"))),
        pipe.ExprPipeHop(recorder(log, "b", result.ExecOutcome.success("b"))),
    ]
    out = pipe.run_expr_pipe("start", expr_hops)
    assert out.ok is True and out.value == "b"
    assert [name for name, _ in log] == ["a", "b"]
    assert log[0][1] == "start"
    assert log[1][1] == "a", "管道只传 value，上一跳的 value 才是下一跳输入"

    log = []
    expr_fail = [
        pipe.ExprPipeHop(recorder(log, "fail", result.ExecOutcome.failure("boom"))),
        pipe.ExprPipeHop(downstream(log)),
    ]
    out = pipe.run_expr_pipe("start", expr_fail)
    assert out.ok is False and out.error == "boom"
    assert log == [("fail", "start")], "未处理失败必须短路，后续跳不得执行"

    try:
        pipe.run_expr_pipe(
            "s", [pipe.StmtPipeHop(lambda value: result.ExecOutcome.success(value))]
        )
    except TypeError:
        pass
    else:
        raise AssertionError("expr 管道不允许带尾随块的 stmt hop")

    log = []
    stmt_hops = [
        pipe.StmtPipeHop(
            lambda value: result.ExecOutcome.failure("boom"),
            tail=lambda outcome: result.ExecOutcome.success("handled"),
        ),
        pipe.StmtPipeHop(recorder(log, "next", result.ExecOutcome.success("done"))),
    ]
    out = pipe.run_stmt_pipe("start", stmt_hops)
    assert out.ok is True and out.value == "done"
    assert log == [("next", "handled")], "尾随块消费 ok 后，下一跳拿到处理结果"

    log = []
    stmt_fail = [
        pipe.StmtPipeHop(lambda value: result.ExecOutcome.failure("boom")),
        pipe.StmtPipeHop(downstream(log)),
    ]
    out = pipe.run_stmt_pipe("start", stmt_fail)
    assert out.ok is False and out.error == "boom"
    assert log == []

    assert pipe.each_source("xs") == ["xs"], "裸词归一成 STRING 后作为单元素数组"
    assert pipe.each_source([1, 2]) == [1, 2]
    assert pipe.each_source(3) == [3]
    assert pipe.each_source({"a": 1}) == [{"a": 1}]
    try:
        pipe.each_source(None)
    except ValueError:
        pass
    else:
        raise AssertionError("each [in] null 必须报错")

    rounds = pipe.reduce_rounds(
        [
            result.ExecOutcome.success("a"),
            result.ExecOutcome.failure("boom"),
            result.ExecOutcome.success("c"),
        ]
    )
    assert rounds.values == ["a", None, "c"], "失败轮记 null，循环继续"
    assert rounds.ok is False and rounds.error == "boom"

    handled = pipe.reduce_rounds(
        [result.ExecOutcome.success("a"), result.ExecOutcome.success("handled")]
    )
    assert handled.ok is True and handled.error is None

    log = []
    each_fail = [
        pipe.StmtPipeHop(lambda value: pipe.each_outcome(rounds)),
        pipe.StmtPipeHop(downstream(log)),
    ]
    out = pipe.run_stmt_pipe("start", each_fail)
    assert out.ok is False and out.error == "boom"
    assert log == [], "each 级未处理失败必须短路"

    log = []
    each_handled = [
        pipe.StmtPipeHop(
            lambda value: pipe.each_outcome(rounds),
            tail=lambda outcome: result.ExecOutcome.success("recovered"),
        ),
        pipe.StmtPipeHop(recorder(log, "next", result.ExecOutcome.success("done"))),
    ]
    out = pipe.run_stmt_pipe("start", each_handled)
    assert out.ok is True and out.value == "done"
    assert log == [("next", "recovered")]

    print("PASS pipe: expr/stmt 分流、只传 value、失败短路、each 失败轮与恢复")


if __name__ == "__main__":
    main()
