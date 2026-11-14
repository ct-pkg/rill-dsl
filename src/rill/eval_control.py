"""RILL 0.1.x 控制流（PH-8）。

硬约束：段语义只有一份。``expr`` 位的管道被折成 ``SimpleStmt`` 链后交给
``Interpreter.eval_simple``，不另建求值路径；``if`` 分支复用同一份
``_run_block``。``each`` / ``break`` 场域分别在 T2 / T3 补。

规范依据：``docs/RILL-0.1.0.md`` §4.6、§4.12、§4.13、§4.15；
规范缺口见 ``docs/phases/PH-8/card.md`` §8。
"""

from . import ast, result
from .eval_simple import BreakSignal, Scope
from .value import truthy


def pipe_as_statement(node):
    """把 expr 位的 ``|>`` 折成语句位管道，段语义交给 ``eval_simple``。"""
    stages = node["stages"]
    rest = None
    for stage in reversed(stages[1:]):
        rest = ast.make(
            "SimpleStmt", span=stage["span"], call=stage, tail=[], pipe=rest
        )
    return ast.make(
        "SimpleStmt", span=stages[0]["span"], call=stages[0], tail=[], pipe=rest
    )


def eval_expr_outcome(interp, node, scope, dollar):
    """§4.12：条件就是 expr（值 / 动词调用 / 管道），统一归约成 {value, ok}。"""
    kind = node["kind"]
    if kind == "VerbCall":
        return interp._call(node, scope, dollar)
    if kind == "Pipe":
        return interp.eval_simple(pipe_as_statement(node), scope, dollar)
    return result.ExecOutcome.success(interp.eval_value(node, scope, dollar))


def eval_if(interp, statement, scope, dollar):
    """§4.12：纯条件判断，不挂尾随块，不参与管道。"""
    for branch in statement["branches"]:
        condition = eval_expr_outcome(interp, branch["condition"], scope, dollar)
        if not condition.ok:
            return condition
        if truthy(condition.value):
            outcome, _ = interp._run_block(branch["body"], scope, dollar)
            return outcome
    if statement["else_body"] is not None:
        outcome, _ = interp._run_block(statement["else_body"], scope, dollar)
        return outcome
    return result.ExecOutcome.success(dollar)


def eval_each(interp, statement, scope, dollar):
    """§4.13：null → error 且 0 轮；数组遍历；其他非数组单元素一次。

    每轮新建作用域，``$变量`` 与 ``$`` 都是当前项；轮内失败（未处理）占
    ``null`` 并继续，处理过的失败取处理后 value。each 级 ``[ok]/[error]``
    复用 ``_apply_tail``。
    """
    source = eval_expr_outcome(interp, statement["source"], scope, dollar)
    if not source.ok:
        return interp._apply_tail(statement["tail"], scope, source)
    items = source.value
    if items is None:
        return interp._apply_tail(
            statement["tail"], scope, result.ExecOutcome.failure()
        )
    if not isinstance(items, list):
        items = [items]

    values = []
    first_error = None
    for index, item in enumerate(items):
        round_scope = Scope(scope)
        round_scope.set(statement["var"], item)
        try:
            outcome, _ = interp._run_block(
                statement["body"], round_scope, item, last_value=True
            )
        except BreakSignal as signal:
            # §4.13「[error] 内显式 break 整个 each」：循环在这里截住 break。
            if signal.target:
                scope.set(signal.target, signal.value)
            interp.trace.append(
                {
                    "event": "round",
                    "index": index,
                    "ok": False,
                    "value": None,
                    "error": signal.value,
                    "break": True,
                }
            )
            values.append(None)
            break
        interp.trace.append(
            {
                "event": "round",
                "index": index,
                "ok": outcome.ok,
                "value": outcome.value if outcome.ok else None,
                "error": outcome.error,
            }
        )
        values.append(outcome.value if outcome.ok else None)
        if not outcome.ok and first_error is None:
            first_error = outcome.error

    if first_error is None:
        base = result.ExecOutcome.success(values)
    else:
        base = result.ExecOutcome(value=values, ok=False, error=first_error)
    return interp._apply_tail(statement["tail"], scope, base)
