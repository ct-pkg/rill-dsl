"""RILL 0.1.x 成败通道（PH-6）。

``ExecOutcome`` 是 ``{value, ok}`` 的运行时承载：
- ``ok`` 是独立通道，``[ok]`` 只看它，不看 ``value`` 的真值；
- 失败且没有错误串时用规范默认串 ``RILL DSL ERROR``（§4.10）；
- ``$`` 投影是 ``value`` 或错误串，``host_meta`` 不属于 ``$``（§4.8）；
- ``exit_code`` 只是钩子，不在本 phase 映射数字（PH-11）。

顶层轨迹 ``run_top_level`` 只模拟“未处理失败中断后续语句”，不做 AST 求值。
"""

DEFAULT_ERROR = "RILL DSL ERROR"


class ExecOutcome(object):
    __slots__ = ("value", "ok", "error", "host_meta", "exit_code")

    def __init__(self, value=None, ok=True, error=None, host_meta=None, exit_code=None):
        self.value = value
        self.ok = bool(ok)
        self.error = error
        self.host_meta = host_meta
        self.exit_code = exit_code

    @classmethod
    def success(cls, value=None, host_meta=None, exit_code=None):
        return cls(value=value, ok=True, error=None, host_meta=host_meta, exit_code=exit_code)

    @classmethod
    def failure(cls, error=None, host_meta=None, exit_code=None):
        return cls(
            value=None,
            ok=False,
            error=DEFAULT_ERROR if error is None else error,
            host_meta=host_meta,
            exit_code=exit_code,
        )

    def __repr__(self):
        return "ExecOutcome(ok=%r, value=%r, error=%r)" % (
            self.ok,
            self.value,
            self.error,
        )


def triggers_ok(outcome):
    """§4.10：``[ok]`` 的条件是 ``ok == true``，与 value 真值无关。"""
    return outcome.ok is True


def triggers_error(outcome):
    return not triggers_ok(outcome)


def dollar(outcome):
    """§4.8/§4.10：``$`` 是 value；失败时是错误串，不含 host_meta。"""
    if triggers_ok(outcome):
        return outcome.value
    return outcome.error


def field(value, name):
    """``.字段`` 只读对象现有键；缺失键抛 KeyError，不静默返回 null。"""
    if not isinstance(value, dict):
        raise TypeError("只能读取对象字段，实际 %r" % type(value))
    return value[name]


def run_top_level(steps):
    """按顺序执行步骤模型；未处理失败立即中断，返回已执行的结果。"""
    trace = []
    for step in steps:
        outcome = step()
        trace.append(outcome)
        if triggers_error(outcome):
            break
    return trace
