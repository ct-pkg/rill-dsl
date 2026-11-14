"""RILL 0.1.x 语法分析器（PH-3）。

只把 token 流归约为 AST：不建 map/fn 表用于加载期校验、不求值、不 import 宿主。
规范依据：``docs/RILL-0.1.0.md`` §三、§4.5、§4.17；规范缺口见
``docs/phases/PH-3/card.md`` §8。

PH-3-T2 范围：``program``、``header``（``//map``）、``block``、
``simple_stmt`` 的 ``verb_call`` 核心（可选主语、动词、宾语）与映射展开。
PH-3-T3 加入状语、介宾、``->`` 赋值、管道、``@`` 调用与 ``//fn`` 模板；
控制流与尾随块在 T4。
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
        while self._at("MAP_HEADER", "FN_HEADER"):
            if self._at("MAP_HEADER"):
                headers.append(self._parse_map_block())
            else:
                headers.append(self._parse_fn_block())
            self._skip_newlines()
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
            return self._parse_call_stmt()
        if token.kind == "LBRACKET":
            self._error("E-PARSE-UNEXPECTED", "独立介宾块在 PH-3-T4 加入")
        return self._parse_simple_stmt()

    def _parse_simple_stmt(self):
        span = {"line": self._peek().line, "col": self._peek().col}
        call = self._parse_verb_call()
        tail = []
        if self._at("ARROW"):
            tail.append(self._parse_assign())
        if self._at("LBRACKET"):
            self._error("E-PARSE-UNEXPECTED", "尾随块在 PH-3-T4 加入")
        if not (self._at("NEWLINE") or self._at("EOF") or self._at("RBRACE")):
            if not self._at("PIPE"):
                self._error(
                    "E-PARSE-UNEXPECTED", "语句后出现意外 token %r" % self._peek().text
                )
        pipe = self._parse_pipe(lambda: self._parse_simple_stmt())
        return ast.make("SimpleStmt", span=span, call=call, tail=tail, pipe=pipe)

    def _parse_assign(self):
        arrow = self._take()
        target = self._expect("VARIABLE", "-> 后的 $变量")
        return ast.make(
            "Assign",
            span={"line": arrow.line, "col": arrow.col},
            target=target.text,
        )

    def _parse_pipe(self, parse_next):
        if not self._at("PIPE"):
            return None
        self._take()
        self._skip_newlines()
        return parse_next()

    def _parse_call_stmt(self):
        at = self._take()
        span = {"line": at.line, "col": at.col}
        name = self._expect("STRING", "函数名（@ 后必须是字符串）")
        if self._at("VERB") or (
            self._peek().kind in _WORD_KINDS and self._peek(1).kind == "VERB"
        ):
            self._error(
                "E-PARSE-FN-DEF-BODY",
                "函数定义只能在 //fn{} 区块内",
                at,
            )
        args = []
        while self._peek().kind in _WORD_KINDS:
            args.append(self._parse_word(bare_as_string=True))
        tail = []
        if self._at("ARROW"):
            tail.append(self._parse_assign())
        if self._at("LBRACKET"):
            self._error("E-PARSE-UNEXPECTED", "尾随块在 PH-3-T4 加入")
        pipe = self._parse_pipe(lambda: self._parse_simple_stmt())
        return ast.make("CallStmt", span=span, name=name.text, args=args, tail=tail, pipe=pipe)

    def _parse_fn_block(self):
        head = self._take()
        span = {"line": head.line, "col": head.col}
        defs = []
        while True:
            self._skip_newlines()
            if self._at("RBRACE"):
                self._take()
                return ast.make("FnBlock", span=span, defs=defs)
            if self._at("EOF"):
                self._error("E-PARSE-MISSING-BLOCK", "//fn{} 缺 }", head)
            defs.append(self._parse_fn_def())

    def _parse_fn_def(self):
        at = self._take()
        span = {"line": at.line, "col": at.col}
        name = self._expect("STRING", "函数名（@ 后必须是字符串）")
        if not (self._at("VERB") or self._peek(1).kind == "VERB"):
            self._error("E-PARSE-UNEXPECTED", "函数定义缺模板")
        template = [self._parse_verb_call()]
        while self._at("PIPE"):
            self._take()
            self._skip_newlines()
            template.append(self._parse_verb_call())
        body = self._parse_block("函数体")
        return ast.make("FnDef", span=span, name=name.text, template=template, body=body)

    def _parse_block(self, what):
        if not self._at("LBRACE"):
            self._error("E-PARSE-MISSING-BLOCK", "%s 缺 { 块" % what)
        brace = self._take()
        body = []
        while True:
            self._skip_newlines()
            if self._at("RBRACE"):
                self._take()
                return ast.make(
                    "Block", span={"line": brace.line, "col": brace.col}, body=body
                )
            if self._at("EOF"):
                self._error("E-PARSE-MISSING-BLOCK", "%s 缺 }" % what, brace)
            body.append(self._parse_statement())

    def _is_trailing_block(self):
        return (
            self._at("LBRACKET")
            and self._peek(1).kind in ("BARE", "KEYWORD")
            and self._peek(2).kind == "RBRACKET"
            and self._peek(3).kind == "LBRACE"
        )

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
        if self._at(*_STOP_KINDS) or self._at("LPAREN", "LBRACKET"):
            self._error("E-PARSE-UNEXPECTED", "动词 %r 缺宾语" % verb_name)
        obj = self._parse_word(bare_as_string=False)
        post = []
        while True:
            if self._at("LPAREN"):
                post.append(self._parse_adverb())
                continue
            if self._at("LBRACKET") and not self._is_trailing_block():
                post.append(self._parse_prep_phrase())
                continue
            break
        return ast.make(
            "VerbCall",
            span=span,
            subject=subject,
            verb=verb_name,
            object=obj,
            post=post,
        )

    def _parse_adverb(self):
        paren = self._take()
        items = []
        while not self._at("RPAREN"):
            if self._at("EOF", "NEWLINE"):
                self._error("E-PARSE-UNEXPECTED", "状语缺 )", paren)
            items.append(self._parse_word(bare_as_string=False))
            if self._at("COMMA"):
                self._take()
                continue
            if not self._at("RPAREN"):
                self._error("E-PARSE-UNEXPECTED", "状语项之间必须是逗号")
        self._take()
        return ast.make(
            "Adverb", span={"line": paren.line, "col": paren.col}, items=items
        )

    def _parse_prep_phrase(self):
        bracket = self._take()
        prep = self._take()
        if not self._at("RBRACKET"):
            self._error("E-PARSE-UNKNOWN-PREP", "介宾标记必须是 [名称]", bracket)
        self._take()
        obj = self._parse_word(bare_as_string=False)
        return ast.make(
            "PrepPhrase",
            span={"line": bracket.line, "col": bracket.col},
            prep=prep.text,
            object=obj,
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
