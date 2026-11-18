"""RILL 0.1.x 函数调用（PH-9 / PH-22）。

函数没有名字：调用按整句形状（``shape.py``）与函数表求精确相等，参数位
按位置绑定；同一参数在模板多处出现时，调用每个位都要写值且相等。默认值
只允许尾部（加载期已校验）。函数体最后一条语句的段输出即返回值，空体返
回 ``null``。

求值仍走 ``Interpreter._run_block`` / ``_apply_tail`` / ``_finish``，
不另立段语义。规范依据：``docs/RILL-0.1.0.md`` §4.18。
"""

from . import loader, result, shape
from .eval_simple import BreakSignal, EvalError, Scope


def eval_call(interp, statement, scope, dollar):
    """``@ verb_call``：先求函数结果，再按语句尾随块与管道收口。"""
    outcome = call_function(interp, statement, scope, dollar)
    outcome = interp._apply_tail(statement["tail"], scope, outcome)
    return interp._finish(statement, scope, outcome)


def call_function(interp, statement, scope, dollar):
    call = statement["call"]
    span = statement["span"]
    call_shape = shape.shape_of(call, template=False)
    exact, _arity = shape.find(interp.functions or [], call_shape)
    if not exact:
        raise EvalError(
            "E-RUN-FN-UNDECLARED",
            "未声明的函数形状：%s" % shape.describe(call_shape),
            span["line"],
            span["col"],
        )
    definition = exact[0]
    names, defaults = loader.template_params(definition)

    bindings = {}
    for name, node in shape.param_positions(definition, call):
        value = interp.eval_value(node, scope, dollar)
        if name in bindings:
            if bindings[name] != value:
                raise EvalError(
                    "E-06",
                    "参数 $%s 在模板多个位上的值不相等" % name,
                    span["line"],
                    span["col"],
                )
        else:
            bindings[name] = value

    body_scope = Scope(scope)
    for name in names:
        if name in bindings:
            body_scope.vars[name] = bindings[name]
        elif name in defaults:
            body_scope.vars[name] = interp.eval_value(defaults[name], scope, dollar)
        else:
            raise EvalError(
                "E-RUN-FN-ARITY",
                "函数形状 %s 缺少参数 $%s"
                % (shape.describe(definition["shape"]), name),
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
            outcome = result.ExecOutcome.failure(result.break_error(signal.value))
        if outcome.ok:
            outcome = result.ExecOutcome.success(outcome.value)

    interp.trace.append(
        {
            "event": "fn",
            "shape": call_shape,
            "ok": outcome.ok,
            "value": outcome.value if outcome.ok else None,
            "error": outcome.error,
        }
    )
    return outcome
