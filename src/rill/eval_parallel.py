"""RILL 0.1.x 并行分支（PH-9）。

逻辑并行、顺序可观察：分支按源序逐条执行，各自新建子作用域；结果数组
按源序汇集，长度 = 分支数。分支内 ``$`` 是进入分支的当前 ``$``，不是
最终数组，避免执行中成环。

段语义只有一份：分支是 ``simple_stmt``，交给
``Interpreter.eval_statement_in_domain``，不另立求值路径。
规范依据：``docs/RILL-0.1.0.md`` §4.14；规范缺口见
``docs/phases/PH-9/card.md`` §8。
"""

from . import result
from .eval_simple import BreakSignal, Scope


def eval_parallel(interp, statement, scope, dollar):
    """执行全部分支；``[results]`` 永远触发，且只改变值不携带状态字段。"""
    values = []
    first_error = None
    for index, branch in enumerate(statement["branches"]):
        outcome = _run_branch(interp, branch, scope, dollar)
        interp.trace.append(
            {
                "event": "branch",
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

    if statement["results"] is not None:
        block_outcome, block_dollar = _run_results(
            interp, statement["results"], scope, values
        )
        interp.trace.append(
            {
                "event": "results",
                "ok": block_outcome.ok,
                "value": block_dollar if block_outcome.ok else None,
                "error": block_outcome.error,
            }
        )
        if not block_outcome.ok:
            return block_outcome
        base = result.ExecOutcome(
            value=block_dollar, ok=base.ok, error=base.error
        )

    return interp._finish(statement, scope, base)


def _run_branch(interp, branch, scope, dollar):
    """分支场域：新子作用域；未处理 break 收口为本分支失败。"""
    branch_scope = Scope(scope)
    try:
        return interp.eval_statement_in_domain(branch, branch_scope, dollar)
    except BreakSignal as signal:
        if signal.target:
            scope.set(signal.target, signal.value)
        return result.ExecOutcome.failure(result.break_error(signal.value))


def _run_results(interp, block, scope, values):
    """``[results]`` 块：``$`` = 结果数组；块内 break 收口为块失败。"""
    try:
        return interp._run_block(block, scope, values)
    except BreakSignal as signal:
        if signal.target:
            scope.set(signal.target, signal.value)
        return result.ExecOutcome.failure(result.break_error(signal.value)), values
