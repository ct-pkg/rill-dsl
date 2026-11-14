"""RILL 0.1.x 管道值传播与 each 轮归约（PH-6）。

只做值传播模型，不执行 AST、不调度尾随块：
- §4.6：管道只传 ``value``，不传 ``{value, ok}``；段尾 ``ok`` 假且没有
  ``[error]`` 处理，或 ``[error]`` 内 break，即中断管道；
- §4.10/§4.11：``expr`` 管道没有尾随块，失败只能短路；``simple_stmt``
  管道每跳可带 ``[ok]/[error]``，先消费 ``ok`` 再交给下一跳；
- §4.13：each 的失败轮记 ``null`` 并继续，each 级 ``[error]`` 取首个失败轮。

未定义项（首跳隐式输入、each 输出在 each 级处理后的去向）见
``docs/phases/PH-6/card.md`` §8，不在这里写死。
"""

from . import result


class ExprPipeHop(object):
    """``expr`` 管道的一跳：只有动词调用，不允许尾随块。"""

    allows_tail = False

    def __init__(self, call):
        self.call = call

    def run(self, value):
        return self.call(value)


class StmtPipeHop(object):
    """``simple_stmt`` 管道的一跳：可带尾随块，先消费 ``ok``。"""

    allows_tail = True

    def __init__(self, call, tail=None):
        self.call = call
        self.tail = tail

    def run(self, value):
        outcome = self.call(value)
        if self.tail is None:
            return outcome
        return self.tail(outcome)


def advance(previous_value, outcome):
    """§4.6：成功把 ``value`` 交给下一跳；未处理失败返回错误串并中断。"""
    if result.triggers_ok(outcome):
        return outcome.value, True
    return outcome.error, False


def run_pipe(start_value, hops):
    value = start_value
    for hop in hops:
        outcome = hop.run(value)
        value, keep_going = advance(value, outcome)
        if not keep_going:
            return outcome
    return result.ExecOutcome.success(value)


def run_expr_pipe(start_value, hops):
    for hop in hops:
        if not isinstance(hop, ExprPipeHop):
            raise TypeError("expr 管道只接受 ExprPipeHop（不允许尾随块）")
    return run_pipe(start_value, hops)


def run_stmt_pipe(start_value, hops):
    for hop in hops:
        if not isinstance(hop, StmtPipeHop):
            raise TypeError("simple_stmt 管道只接受 StmtPipeHop")
    return run_pipe(start_value, hops)


class EachResult(object):
    __slots__ = ("values", "ok", "error")

    def __init__(self, values, ok, error):
        self.values = values
        self.ok = ok
        self.error = error

    def __repr__(self):
        return "EachResult(ok=%r, values=%r, error=%r)" % (
            self.ok,
            self.values,
            self.error,
        )


def each_source(value):
    """§4.13：``[in]`` 为 null 报错；数组原样；其他值转单元素数组。

    裸词在 parser 已归一成 ``STRING``，因此这里看到的是单个字符串。
    """
    if value is None:
        raise ValueError("each 的 [in] 值不能是 null")
    if isinstance(value, list):
        return value
    return [value]


def reduce_rounds(rounds):
    """§4.13：未处理失败轮记 null 并继续；返回结果数组与首个失败。"""
    values = []
    first_error = None
    for outcome in rounds:
        if result.triggers_ok(outcome):
            values.append(outcome.value)
            continue
        values.append(None)
        if first_error is None:
            first_error = outcome.error
    return EachResult(values, first_error is None, first_error)


def each_outcome(each_result):
    """把 each 归约投影成 ``ExecOutcome``，供管道下一跳消费。"""
    if each_result.ok:
        return result.ExecOutcome.success(each_result.values)
    return result.ExecOutcome.failure(each_result.error)
