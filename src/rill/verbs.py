"""RILL 0.1.x fake VerbRegistry（PH-6）。

只按脚本返回可编程结果，不接真实工具、文件系统或网络：
每个动词一条结果队列，调用时取队首；队列耗尽取 default；没有 default
则返回失败。未注册动词直接抛 KeyError，让接线错误早暴露。

脚本项可以是 ``ExecOutcome``，也可以是 ``{"ok", "value", "error"}`` 形状。
"""

from . import result


def _coerce(name, spec):
    if isinstance(spec, result.ExecOutcome):
        return spec
    if isinstance(spec, dict):
        if spec.get("ok", True):
            return result.ExecOutcome.success(
                spec.get("value"),
                host_meta=spec.get("host_meta"),
                exit_code=spec.get("exit_code"),
            )
        return result.ExecOutcome.failure(
            spec.get("error"),
            host_meta=spec.get("host_meta"),
            exit_code=spec.get("exit_code"),
        )
    raise TypeError("fake 动词 %r 的结果脚本不是 ExecOutcome/dict：%r" % (name, spec))


class FakeVerbRegistry(object):
    def __init__(self):
        self._queues = {}
        self._defaults = {}

    def register(self, name, results, default=None):
        self._queues[name] = list(results)
        self._defaults[name] = default

    def call(self, name, arg=None):
        """``arg`` 只为将来对齐调用形状；fake 不解释它。"""
        if name not in self._queues:
            raise KeyError("fake 动词 %r 未注册" % name)
        queue = self._queues[name]
        if queue:
            return _coerce(name, queue.pop(0))
        default = self._defaults[name]
        if default is None:
            return result.ExecOutcome.failure(
                "fake 动词 %r 无排队结果且无 default" % name
            )
        return _coerce(name, default)
