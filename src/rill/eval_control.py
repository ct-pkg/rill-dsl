"""RILL 0.1.x 控制流（PH-8）。

硬约束：段语义只有一份。``expr`` 位的管道被折成 ``SimpleStmt`` 链后交给
``Interpreter.eval_simple``，不另建求值路径；``if`` 分支复用同一份
``_run_block``。``each`` / ``break`` 场域分别在 T2 / T3 补。

规范依据：``docs/RILL-0.1.0.md`` §4.6、§4.12、§4.13、§4.15；
规范缺口见 ``docs/phases/PH-8/card.md`` §8。
"""

from . import ast, result
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
