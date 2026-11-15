"""词法与语法诊断。

``stage`` 与 harness 的 STAGES 对齐：词法为 ``tokenize``，语法为 ``parse``，加载期为 ``load``。
``E-01`` / ``E-02`` / ``E-07`` 来自规范 §4.20；``E-03``…``E-06`` 见 PH-22 卡；
``E-PARSE-*`` 是 PH-3 冻结的实现错误码，见 ``docs/phases/PH-3/card.md`` §7；
``E-LOAD-*`` 见 ``docs/phases/PH-4/card.md`` §8。

``hint`` 只在错误确实带迁移/候选提示时出现；旧错误不带该键，信封保持不变。
"""


class _Diag(Exception):
    stage = ""

    def __init__(self, code, message, line, col, hint=None):
        Exception.__init__(self, message)
        self.code = code
        self.message = message
        self.line = line
        self.col = col
        self.hint = hint

    def as_dict(self):
        payload = {
            "stage": self.stage,
            "code": self.code,
            "line": self.line,
            "col": self.col,
            "message": self.message,
        }
        if self.hint:
            payload["hint"] = self.hint
        return payload


class LexError(_Diag):
    stage = "tokenize"


class ParseError(_Diag):
    stage = "parse"


class LoadError(_Diag):
    """加载期诊断；``E-LOAD-*`` 见 ``docs/phases/PH-4/card.md`` §8。"""

    stage = "load"
