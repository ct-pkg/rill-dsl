"""词法与语法诊断。

``stage`` 与 harness 的 STAGES 对齐：词法为 ``tokenize``，语法为 ``parse``，加载期为 ``load``。
``E-01`` / ``E-02`` 来自规范 §4.20；``E-PARSE-*`` 是 PH-3 冻结的实现错误码，
见 ``docs/phases/PH-3/card.md`` §7；``E-LOAD-*`` 见 ``docs/phases/PH-4/card.md`` §8。
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


class ParseError(Exception):
    def __init__(self, code, message, line, col):
        Exception.__init__(self, message)
        self.code = code
        self.message = message
        self.line = line
        self.col = col

    @property
    def stage(self):
        return "parse"

    def as_dict(self):
        return {
            "stage": self.stage,
            "code": self.code,
            "line": self.line,
            "col": self.col,
            "message": self.message,
        }


class LoadError(Exception):
    """加载期诊断；``E-LOAD-*`` 见 ``docs/phases/PH-4/card.md`` §8。"""

    def __init__(self, code, message, line, col):
        Exception.__init__(self, message)
        self.code = code
        self.message = message
        self.line = line
        self.col = col

    @property
    def stage(self):
        return "load"

    def as_dict(self):
        return {
            "stage": self.stage,
            "code": self.code,
            "line": self.line,
            "col": self.col,
            "message": self.message,
        }
