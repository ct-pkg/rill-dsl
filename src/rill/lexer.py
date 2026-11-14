"""RILL 0.1.x 词法分析器。

只做 token 切分，不建 AST、不查注册表、不 import 任何宿主模块。
规范依据：``docs/RILL-0.1.0.md`` §3.1、§3.2、§4.16、§4.19、§4.20，
以及对 A2 / B1 两项裁定的落实。
"""

import re

from .errors import LexError
from .tokens import KEYWORDS, Token

_WS = " \t"
# 这些字符在任何位置都终止裸词；`>` 与 `|` 单独出现时报错。
_BARE_STOP = set("<>()[]{}|@?,\"'`$")
_BARE_ESCAPABLE = set("[]()<>{}$\\")
_SHORT_EXTRA = set("_-")
_NUMBER_RE = re.compile(r"-?[0-9]+")


def _is_short_char(ch):
    return ch.isalnum() and ch.isascii() or ch in _SHORT_EXTRA


def _is_ident_start(ch):
    return ch == "_" or (ch.isascii() and ch.isalpha())


def _is_ident_char(ch):
    return ch == "_" or (ch.isascii() and ch.isalnum())


class Lexer(object):
    def __init__(self, source):
        self.src = source.replace("\r\n", "\n").replace("\r", "\n")
        self.n = len(self.src)
        self.i = 0
        self.line = 1
        self.col = 1
        self.prev_char = ""
        self.tokens = []
        self.map_mode = False
        self.map_pos = None

    # ---- 游标 ----------------------------------------------------------

    def _peek(self, offset=0):
        index = self.i + offset
        return self.src[index] if index < self.n else ""

    def _advance(self, count=1):
        for _ in range(count):
            if self.i >= self.n:
                return
            ch = self.src[self.i]
            self.i += 1
            self.prev_char = ch
            if ch == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1

    def _emit(self, kind, text, line=None, col=None):
        self.tokens.append(
            Token(kind, text, self.line if line is None else line, self.col if col is None else col)
        )

    def _error(self, code, message, line=None, col=None):
        raise LexError(
            code,
            message,
            self.line if line is None else line,
            self.col if col is None else col,
        )

    def _wordish_prev(self):
        ch = self.prev_char
        return bool(ch) and (ch.isalnum() or ch in "_-.:'\"`")

    # ---- 入口 ----------------------------------------------------------

    def run(self):
        while self.i < self.n:
            if self.map_mode:
                self._lex_map_line()
            else:
                self._lex_normal()
        if self.map_mode:
            self._error(
                "E-LEX-MAP-UNCLOSED",
                "//map 区块未闭合：缺少 }",
                line=self.map_pos[0],
                col=self.map_pos[1],
            )
        self._emit("EOF", "")
        return self.tokens

    # ---- 普通模式 ------------------------------------------------------

    def _lex_normal(self):
        ch = self._peek()

        if ch in _WS:
            self._advance()
            return
        if ch == "\n":
            line, col = self.line, self.col
            self._advance()
            self._emit("NEWLINE", "\n", line=line, col=col)
            return
        if ch == "/" and self._peek(1) == "/":
            self._lex_comment_or_header()
            return
        if ch in "()[]{}":
            kinds = {
                "(": "LPAREN",
                ")": "RPAREN",
                "[": "LBRACKET",
                "]": "RBRACKET",
                "{": "LBRACE",
                "}": "RBRACE",
            }
            self._emit(kinds[ch], ch)
            self._advance()
            return
        if ch == "<":
            self._lex_verb()
            return
        if ch == ">":
            self._error("E-LEX-GT", "孤立的 >：动词必须写成 <name>")
        if ch == "-" and self._peek(1) == ">":
            self._emit("ARROW", "->")
            self._advance(2)
            return
        if ch == "|":
            if self._peek(1) == ">":
                self._emit("PIPE", "|>")
                self._advance(2)
                return
            self._error("E-LEX-PIPE", "孤立的 |：管道符号必须是 |>")
        if ch == "@":
            self._emit("AT", "@")
            self._advance()
            return
        if ch == "?":
            self._emit("QUESTION", "?")
            self._advance()
            return
        if ch == ",":
            self._emit("COMMA", ",")
            self._advance()
            return
        if ch == "$":
            self._lex_dollar()
            return
        if ch in ("'", '"'):
            self._lex_string(ch)
            return
        if ch == "`":
            self._lex_map_ref()
            return
        if ch == "." and _is_ident_start(self._peek(1)) and not self._wordish_prev():
            self._lex_field()
            return
        if not self._wordish_prev():
            end = self._match_number()
            if end is not None:
                line, col = self.line, self.col
                text = self.src[self.i : end]
                self._advance(end - self.i)
                self._emit("NUMBER", text, line=line, col=col)
                return
        self._lex_bare()

    # ---- 单词类 --------------------------------------------------------

    def _lex_bare(self):
        line, col = self.line, self.col
        start = self.i
        while self.i < self.n:
            ch = self._peek()
            if ch in _WS or ch == "\n":
                break
            if ch in _BARE_STOP:
                break
            if ch == "-" and self._peek(1) == ">":
                break
            if ch == "\\":
                nxt = self._peek(1)
                if nxt not in _BARE_ESCAPABLE:
                    self._error(
                        "E-LEX-BARE-ESCAPE",
                        r"非法转义：裸词只允许 \[ \] \( \) \< \> \{ \} \$ \\",
                    )
                self._advance(2)
                continue
            self._advance()
        if self.i == start:
            self._error("E-LEX-CHAR", "无法识别的字符 %r" % self._peek())
        text = self.src[start : self.i]
        kind = "KEYWORD" if text in KEYWORDS else "BARE"
        self._emit(kind, text, line=line, col=col)

    def _match_number(self):
        match = _NUMBER_RE.match(self.src, self.i)
        if not match:
            return None
        end = match.end()
        nxt = self.src[end] if end < self.n else ""
        # 数字后面紧跟词字符时，整体按裸词处理（如 42abc、1.5、prod-db:5432）。
        if nxt and (nxt.isalnum() or nxt in "_.:-" or nxt == "\\"):
            return None
        return end

    def _lex_dollar(self):
        line, col = self.line, self.col
        self._advance()
        start = self.i
        while self.i < self.n and _is_ident_char(self._peek()):
            self._advance()
        if self.i == start:
            self._emit("DOLLAR", "$", line=line, col=col)
        else:
            self._emit("VARIABLE", self.src[start : self.i], line=line, col=col)

    def _lex_field(self):
        line, col = self.line, self.col
        self._advance()
        start = self.i
        while self.i < self.n and _is_ident_char(self._peek()):
            self._advance()
        self._emit("FIELD", self.src[start : self.i], line=line, col=col)

    def _lex_string(self, quote):
        line, col = self.line, self.col
        self._advance()
        buf = []
        while True:
            if self.i >= self.n or self._peek() == "\n":
                self._error(
                    "E-LEX-QUOTE",
                    "字符串未闭合：行尾前缺少结束引号",
                    line=line,
                    col=col,
                )
            ch = self._peek()
            if ch == quote:
                self._advance()
                break
            if quote == '"' and ch == "\\":
                nxt = self._peek(1)
                if nxt not in ('"', "\\"):
                    self._error(
                        "E-LEX-ESCAPE",
                        r"非法转义：双引号内只允许 \" 与 \\",
                    )
                buf.append(nxt)
                self._advance(2)
                continue
            buf.append(ch)
            self._advance()
        self._emit("STRING", "".join(buf), line=line, col=col)

    def _lex_verb(self):
        line, col = self.line, self.col
        self._advance()
        start = self.i
        while self.i < self.n and self._peek() not in ">\n":
            self._advance()
        if self.i >= self.n or self._peek() == "\n":
            self._error(
                "E-02",
                "动词未闭合；映射定义必须在 `//map{}` 块内",
                line=line,
                col=col,
            )
        if self.i == start:
            self._error("E-LEX-VERB", "动词名为空：<> 内至少要有一个字符", line=line, col=col)
        text = self.src[start : self.i]
        self._advance()
        self._emit("VERB", text, line=line, col=col)

    def _lex_map_ref(self):
        line, col = self.line, self.col
        self._advance()
        start = self.i
        while self.i < self.n and self._peek() not in "`\n":
            self._advance()
        if self.i >= self.n or self._peek() == "\n":
            self._error("E-LEX-MAP-REF", "反引号引用未闭合", line=line, col=col)
        text = self.src[start : self.i]
        self._advance()
        self._emit("MAP_REF", text, line=line, col=col)

    # ---- // 注释与区块头 -----------------------------------------------

    def _lex_comment_or_header(self):
        line, col = self.line, self.col
        probe = self.i + 2
        word = ""
        for candidate in ("map", "fn"):
            end = probe
            while end < self.n and self.src[end] in _WS:
                end += 1
            if self.src.startswith(candidate, end):
                after = end + len(candidate)
                while after < self.n and self.src[after] in _WS:
                    after += 1
                if after < self.n and self.src[after] == "{":
                    word = candidate
                    brace = after
                    break
        if word:
            self._emit(
                "MAP_HEADER" if word == "map" else "FN_HEADER",
                "//" + word,
                line=line,
                col=col,
            )
            self._advance(brace + 1 - self.i)
            if word == "map":
                self.map_mode = True
                self.map_pos = (line, col)
            return
        # 行注释：吃掉到行尾，不含换行。
        while self.i < self.n and self._peek() != "\n":
            self._advance()

    # ---- map 行模式 ----------------------------------------------------

    def _lex_map_line(self):
        while self._peek() and self._peek() in _WS:
            self._advance()

        if self.i >= self.n:
            self._error(
                "E-LEX-MAP-UNCLOSED",
                "//map 区块未闭合：缺少 }",
                line=self.map_pos[0],
                col=self.map_pos[1],
            )
        if self._peek() == "\n":
            line, col = self.line, self.col
            self._advance()
            self._emit("NEWLINE", "\n", line=line, col=col)
            return
        if self._peek() == "}":
            self._emit("RBRACE", "}")
            self._advance()
            self.map_mode = False
            self.map_pos = None
            return

        short_line, short_col = self.line, self.col
        start = self.i
        while self.i < self.n and _is_short_char(self._peek()):
            self._advance()
        if self.i == start:
            self._error(
                "E-LEX-MAP-ENTRY",
                "map 行缺少短词：短词只允许字母、数字、- 和 _",
                line=short_line,
                col=short_col,
            )
        short = self.src[start : self.i]
        mark_line, mark_col = self.line, self.col
        marker = self._peek()
        if marker == "" or marker == "\n":
            self._error(
                "E-01",
                "map_entry 标记符非法",
                line=mark_line,
                col=mark_col,
            )
        if marker not in ("'", "`", "<"):
            self._error(
                "E-01",
                "map_entry 标记符非法：只允许 ' / ` / <",
                line=mark_line,
                col=mark_col,
            )
        # 标记符只占一个字符；其后到行尾是长词，不启动任何扫描。
        self._emit("MAP_SHORT", short, line=short_line, col=short_col)
        self._emit("MAP_MARK", marker, line=mark_line, col=mark_col)
        self._advance()
        long_line, long_col = self.line, self.col
        long_start = self.i
        while self.i < self.n and self._peek() != "\n":
            self._advance()
        self._emit("MAP_LONG", self.src[long_start : self.i], line=long_line, col=long_col)
        if self.i >= self.n:
            self._error(
                "E-LEX-MAP-UNCLOSED",
                "//map 区块未闭合：缺少 }",
                line=self.map_pos[0],
                col=self.map_pos[1],
            )
        newline_line, newline_col = self.line, self.col
        self._advance()
        self._emit("NEWLINE", "\n", line=newline_line, col=newline_col)


def tokenize(source):
    return Lexer(source).run()
