"""Token 定义与稳定序列化形式。

序列化形状固定为 ``{"kind", "text", "line", "col"}``：
  - ``kind``：见 KINDS；
  - ``text``：STRING 为解码后的值；VARIABLE / FIELD / VERB / MAP_REF 不含引导符号；
    MAP_HEADER / FN_HEADER 归一为 ``//map`` / ``//fn``；其余为原文片段；
  - ``line`` / ``col``：1 基，col 按 Unicode 码点计数。
"""

KINDS = (
    # 结构符号
    "LBRACE",
    "RBRACE",
    "LPAREN",
    "RPAREN",
    "LBRACKET",
    "RBRACKET",
    "ARROW",
    "PIPE",
    "AT",
    "QUESTION",
    "COMMA",
    # 词类
    "KEYWORD",
    "BARE",
    "NUMBER",
    "STRING",
    "VARIABLE",
    "DOLLAR",
    "FIELD",
    "VERB",
    "MAP_REF",
    # 区块头
    "MAP_HEADER",
    "FN_HEADER",
    # map 行模式
    "MAP_SHORT",
    "MAP_MARK",
    "MAP_LONG",
    # 边界
    "NEWLINE",
    "EOF",
)

KEYWORDS = ("if", "else", "else-if", "each", "parallel", "break")


class Token(object):
    __slots__ = ("kind", "text", "line", "col")

    def __init__(self, kind, text, line, col):
        if kind not in KINDS:
            raise ValueError("未知 token kind %r" % (kind,))
        self.kind = kind
        self.text = text
        self.line = line
        self.col = col

    def as_dict(self):
        return {
            "kind": self.kind,
            "text": self.text,
            "line": self.line,
            "col": self.col,
        }

    def __eq__(self, other):
        return isinstance(other, Token) and self.as_dict() == other.as_dict()

    def __repr__(self):
        return "Token(%s, %r, %d:%d)" % (self.kind, self.text, self.line, self.col)
