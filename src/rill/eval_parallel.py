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
from .eval_simple import BreakSignal, EvalError, Scope


def eval_parallel(interp, statement, scope, dollar):
    """执行全部分支，返回 ``{value: 结果数组, ok}`；``[results]`` 在 T2 落地。"""
    if statement["results"] is not None:
        span = statement["results"]["span"]
        raise EvalError(
            "E-RUN-UNSUPPORTED",
            "parallel [results] 不在 PH-9-T1 的执行范围（T2）",
            span["line"],
            span["col"],
        )

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
    return interp._finish(statement, scope, base)


def _run_branch(interp, branch, scope, dollar):
    """分支场域：新子作用域；未处理 break 收口为本分支失败。"""
    branch_scope = Scope(scope)
    try:
        return interp.eval_statement_in_domain(branch, branch_scope, dollar)
    except BreakSignal as signal:
        if signal.target:
            scope.set(signal.target, signal.value)
        return result.ExecOutcome.failure(signal.value)
