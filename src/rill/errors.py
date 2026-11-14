"""词法诊断。

``stage`` 固定为 ``tokenize``，与 harness 的 STAGES 对齐。
``E-01`` / ``E-02`` 来自规范 §4.20；其余为词法层实现错误码，见
``docs/planning/rill-0.1.0-lexer.md``。
"""


class LexError(Exception):
    def __init__(self, code, message, line, col):
        Exception.__init__(self, message)
        self.code = code
        self.message = message
        self.line = line
        self.col = col

    @property
    def stage(self):
        return "tokenize"

    def as_dict(self):
        return {
            "stage": self.stage,
            "code": self.code,
            "line": self.line,
            "col": self.col,
            "message": self.message,
        }
