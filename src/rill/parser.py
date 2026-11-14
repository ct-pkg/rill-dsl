"""RILL 0.1.x 语法分析器（PH-3）。

只把 token 流归约为 AST：不建 map/fn 表用于加载期校验、不求值、不 import 宿主。
规范依据：``docs/RILL-0.1.0.md`` §三、§4.5、§4.17；规范缺口见
``docs/phases/PH-3/card.md`` §8。

PH-3-T2 范围：``program``、``header``（``//map``）、``block``、
``simple_stmt`` 的 ``verb_call`` 核心（可选主语、动词、宾语）与映射展开。
状语、介宾、赋值、管道、``@`` 调用、控制流与尾随块在 T3/T4 加入。
"""

from . import ast
from .errors import ParseError
from .tokens import Token

# 宾语/值可用的单词类 token；`MAP_REF` 先展开为 STRING 再参与相邻折叠。
_WORD_KINDS = ("BARE", "NUMBER", "STRING", "VARIABLE", "DOLLAR", "FIELD", "MAP_REF")
_STOP_KINDS = (
    "LPAREN",
    "LBRACKET",
    "LBRACE",
    "RBRACE",
    "ARROW",
    "PIPE",
    "NEWLINE",
    "EOF",
)


def _raw_len(token):
    """token 在源码里的原始宽度；用于判断两个单词是否相邻（无空格）。"""
    length = len(token.text)
    if token.kind == "MAP_REF":
        return length + 2
    if token.kind in ("VARIABLE", "FIELD"):
        return length + 1
    if token.kind == "DOLLAR":
        return 1
    return length


def _adjacent(prev, nxt):
    return (
        prev.line == nxt.line
        and nxt.col == prev.col + _raw_len(prev)
        and nxt.kind in _WORD_KINDS
    )


class Parser(object):
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0
        self.maps = {}

    # ---- token 游标 ----------------------------------------------------

    def _peek(self, offset=0):
        index = self.i + offset
        if index >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[index]

    def _at(self, *kinds):
        return self._peek().kind in kinds

    def _take(self):
        token = self._peek()
        if token.kind != "EOF":
            self.i += 1
        return token

    def _skip_newlines(self):
        while self._at("NEWLINE"):
            self.i += 1

    def _error(self, code, message, token=None):
        token = token or self._peek()
        raise ParseError(code, message, token.line, token.col)

    def _expect(self, kind, what, code="E-PARSE-UNEXPECTED"):
        if not self._at(kind):
            self._error(code, "期望 %s，实际 %r" % (what, self._peek().text))
        return self._take()

    # ---- program / header ---------------------------------------------

    def parse_program(self):
        self._skip_newlines()
        first = self._peek()
        span = {"line": first.line, "col": first.col}
        headers = []
        body = []
        while self._at("MAP_HEADER"):
            headers.append(self._parse_map_block())
            self._skip_newlines()
        if self._at("FN_HEADER"):
            self._error("E-PARSE-UNEXPECTED", "//fn{} 区块在 PH-3-T3 加入")
        while not self._at("EOF"):
            if self._at("NEWLINE"):
                self.i += 1
                continue
            if self._at("MAP_HEADER") or self._at("FN_HEADER"):
                self._error("E-PARSE-HEADER-ORDER", "header 只能出现在语句之前")
            body.append(self._parse_statement())
            self._skip_newlines()
        return ast.make("Program", span=span, headers=headers, body=body)

    def _parse_map_block(self):
        head = self._take()
        span = {"line": head.line, "col": head.col}
        entries = []
        while True:
            self._skip_newlines()
            if self._at("RBRACE"):
                self._take()
                return ast.make("MapBlock", span=span, entries=entries)
            if self._at("EOF"):
                self._error("E-PARSE-MISSING-BLOCK", "//map{} 缺 }", head)
            short = self._expect("MAP_SHORT", "map 短词")
            marker = self._expect("MAP_MARK", "map 标记符")
            long_word = self._expect("MAP_LONG", "map 长词")
            entries.append(
                ast.make(
                    "MapEntry",
                    span={"line": short.line, "col": short.col},
                    short=short.text,
                    marker=marker.text,
                    long=long_word.text,
                )
            )
            # 块内映射表：只用于本 phase 的展开；查重留 PH-4。
            self.maps.setdefault(short.text, (marker.text, long_word.text))

    # ---- 语句 ----------------------------------------------------------

    def _parse_statement(self):
        token = self._peek()
        if token.kind == "KEYWORD":
            self._error(
                "E-PARSE-UNEXPECTED",
                "关键字 %r 的语句在 PH-3-T4 加入" % token.text,
            )
        if token.kind == "AT":
            self._error("E-PARSE-UNEXPECTED", "@ 语句在 PH-3-T3 加入")
        if token.kind == "LBRACKET":
            self._error("E-PARSE-UNEXPECTED", "独立介宾块在 PH-3-T4 加入")
        return self._parse_simple_stmt()

    def _parse_simple_stmt(self):
        span = {"line": self._peek().line, "col": self._peek().col}
        call = self._parse_verb_call()
        tail = []
        if self._at("ARROW"):
            self._error("E-PARSE-UNEXPECTED", "-> 赋值在 PH-3-T3 加入")
        if self._at("LBRACKET"):
            self._error("E-PARSE-UNEXPECTED", "尾随块在 PH-3-T4 加入")
        if self._at("PIPE"):
            self._error("E-PARSE-UNEXPECTED", "管道在 PH-3-T3 加入")
        if not (self._at("NEWLINE") or self._at("EOF") or self._at("RBRACE")):
            self._error("E-PARSE-UNEXPECTED", "语句后出现意外 token %r" % self._peek().text)
        return ast.make("SimpleStmt", span=span, call=call, tail=tail, pipe=None)

    def _parse_verb_call(self):
        span = {"line": self._peek().line, "col": self._peek().col}
        subject = None
        if self._peek().kind in _WORD_KINDS and self._peek(1).kind == "VERB":
            subject = self._parse_word(bare_as_string=False)
        verb = self._expect("VERB", "动词 <name>")
        verb_name = verb.text
        mapped = self.maps.get(verb_name)
        if mapped and mapped[0] == "<":
            verb_name = mapped[1]
        if self._at(*_STOP_KINDS):
            self._error("E-PARSE-UNEXPECTED", "动词 %r 缺宾语" % verb_name)
        obj = self._parse_word(bare_as_string=False)
        return ast.make(
            "VerbCall",
            span=span,
            subject=subject,
            verb=verb_name,
            object=obj,
            post=[],
        )

    # ---- 单词与值 ------------------------------------------------------

    def _parse_word(self, bare_as_string):
        """读一个单词，并把无空格的相邻单词折叠：全静态则并为 STRING。"""
        parts = [self._word_node(self._take(), bare_as_string)]
        while _adjacent(self.tokens[self.i - 1], self._peek()):
            parts.append(self._word_node(self._take(), bare_as_string))
        if len(parts) == 1:
            return parts[0]
        if all(part["kind"] in ("String", "Bare") for part in parts):
            return ast.make(
                "String",
                span=parts[0]["span"],
                value="".join(
                    part["value"] if part["kind"] == "String" else part["text"]
                    for part in parts
                ),
            )
        return ast.make("Concat", span=parts[0]["span"], parts=parts)

    def _word_node(self, token, bare_as_string):
        span = {"line": token.line, "col": token.col}
        if token.kind == "STRING":
            return ast.make("String", span=span, value=token.text)
        if token.kind == "NUMBER":
            return ast.make("Number", span=span, value=int(token.text))
        if token.kind == "VARIABLE":
            return ast.make("Variable", span=span, name=token.text)
        if token.kind == "DOLLAR":
            return ast.make("Self", span=span)
        if token.kind == "FIELD":
            return ast.make("Field", span=span, name=token.text)
        if token.kind == "MAP_REF":
            mapped = self.maps.get(token.text)
            if mapped and mapped[0] in ("'", "`"):
                return ast.make("String", span=span, value=mapped[1])
            return ast.make("String", span=span, value=token.text)
        if token.kind == "BARE":
            if bare_as_string:
                return ast.make("String", span=span, value=token.text)
            return ast.make("Bare", span=span, text=token.text)
        self._error("E-PARSE-UNEXPECTED", "这里不能出现 %r" % token.text, token)


def parse(tokens):
    return Parser(tokens).parse_program()
