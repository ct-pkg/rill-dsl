"""RILL 0.1.x 函数调用（PH-9）。

函数名精确匹配；参数位 = 模板 ``$变量`` 去重后首次出现顺序，实参按位置
绑定；默认值只允许尾部（加载期已校验）。函数体最后一条语句的段输出即
返回值，空体返回 ``null``。

求值仍走 ``Interpreter._run_block`` / ``_apply_tail`` / ``_finish``，
不另立段语义。规范依据：``docs/RILL-0.1.0.md`` §4.18；规范缺口见
``docs/phases/PH-9/card.md`` §8。
"""

from . import loader, result
from .eval_simple import BreakSignal, EvalError, Scope


def eval_call(interp, statement, scope, dollar):
    """``@ "name" arg*``：先求函数结果，再按语句尾随块与管道收口。"""
    outcome = call_function(interp, statement, scope, dollar)
    outcome = interp._apply_tail(statement["tail"], scope, outcome)
    return interp._finish(statement, scope, outcome)


def call_function(interp, statement, scope, dollar):
    name = statement["name"]
    span = statement["span"]
    definition = (interp.functions or {}).get(name)
    if definition is None:
        raise EvalError(
            "E-RUN-FN-UNDECLARED",
            "未声明的函数 %r；只能调用 //fn{} 内定义的名字" % name,
            span["line"],
            span["col"],
        )

    names, defaults = loader.template_params(definition)
    args = [interp.eval_value(arg, scope, dollar) for arg in statement["args"]]
    if len(args) > len(names):
        raise EvalError(
            "E-RUN-FN-ARITY",
            "函数 %r 需要 %d 个实参，实际 %d 个" % (name, len(names), len(args)),
            span["line"],
            span["col"],
        )

    body_scope = Scope(scope)
    for index, param in enumerate(names):
        if index < len(args):
            body_scope.vars[param] = args[index]
        elif param in defaults:
            body_scope.vars[param] = interp.eval_value(defaults[param], scope, dollar)
        else:
            raise EvalError(
                "E-RUN-FN-ARITY",
                "函数 %r 需要 %d 个实参，实际 %d 个" % (name, len(names), len(args)),
                span["line"],
                span["col"],
            )

    body = definition["body"]["body"]
    if not body:
        outcome = result.ExecOutcome.success(None)
    else:
        try:
            outcome, _ = interp._run_block(
                definition["body"], body_scope, dollar, last_value=True
            )
        except BreakSignal as signal:
            if signal.target:
                scope.set(signal.target, signal.value)
            outcome = result.ExecOutcome.failure(signal.value)
        if outcome.ok:
            outcome = result.ExecOutcome.success(outcome.value)

    interp.trace.append(
        {
            "event": "fn",
            "name": name,
            "ok": outcome.ok,
            "value": outcome.value if outcome.ok else None,
            "error": outcome.error,
        }
    )
    return outcome
