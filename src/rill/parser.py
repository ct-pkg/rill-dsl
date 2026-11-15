"""RILL 0.1.x 语法分析器（PH-3）。

只把 token 流归约为 AST：不建 map/fn 表用于加载期校验、不求值、不 import 宿主。
规范依据：``docs/RILL-0.1.0.md`` §三、§4.5、§4.17；规范缺口见
``docs/phases/PH-3/card.md`` §8。

PH-3-T2 范围：``program``、``header``（``//map``）、``block``、
``simple_stmt`` 的 ``verb_call`` 核心（可选主语、动词、宾语）与映射展开。
PH-3-T3 加入状语、介宾、``->`` 赋值、管道、``@`` 调用与 ``//fn`` 模板；
控制流与尾随块在 T4。
"""

from . import ast, shape
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

# §4.5 的介词表；方括号里出现表外名称按 §七 在解析期拒绝。
_PREPS = ("to", "with", "from", "in", "on", "into", "ok", "error")


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
        self.warnings = []
        # §4.18：`$变量?默认值` 只允许出现在 //fn{} 的模板里。
        self.template_mode = False

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

    def _error(self, code, message, token=None, hint=None):
        token = token or self._peek()
        raise ParseError(code, message, token.line, token.col, hint=hint)

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
            if token.text == "if":
                return self._parse_if()
            if token.text == "each":
                return self._parse_each()
            if token.text == "parallel":
                return self._parse_parallel()
            if token.text == "break":
                return self._parse_break()
            self._error(
                "E-PARSE-UNEXPECTED", "关键字 %r 不能出现在语句起始位" % token.text
            )
        if token.kind == "AT":
            return self._parse_call_stmt()
        if token.kind == "LBRACKET":
            return self._parse_prep_block_stmt()
        return self._parse_simple_stmt()

    def _parse_simple_stmt(self):
        span = {"line": self._peek().line, "col": self._peek().col}
        call = self._parse_verb_call()
        tail = self._parse_statement_tail()
        pipe = self._parse_pipe(lambda: self._parse_simple_stmt())
        return ast.make("SimpleStmt", span=span, call=call, tail=tail, pipe=pipe)

    def _parse_statement_tail(self, allow_assign=True):
        tail = []
        counts = {"ok": 0, "error": 0}
        while True:
            if allow_assign and self._at("ARROW"):
                tail.append(self._parse_assign())
                continue
            if self._is_trailing_block():
                tail.append(self._parse_trailing_block(counts))
                continue
            break
        if self._at("LBRACKET"):
            self._reject_results()
            self._error(
                "E-PARSE-UNEXPECTED", "方括号后必须跟块或介宾宾语：%r" % self._peek().text
            )
        if not (self._at("NEWLINE") or self._at("EOF") or self._at("RBRACE")):
            if not self._at("PIPE"):
                self._error(
                    "E-PARSE-UNEXPECTED", "语句后出现意外 token %r" % self._peek().text
                )
        return tail

    def _reject_results(self):
        """§4.5/§4.14：``[results]`` 只有 parallel 尾随块一个合法位置。

        所有方括号入口共用这一条判据；出现在其他位置一律报错，不落进
        通用介词表被静默吃掉。
        """
        if self._at("LBRACKET") and self._peek(1).text == "results":
            self._error(
                "E-PARSE-RESULTS-CONTEXT",
                "[results] 只允许出现在 parallel 块级",
                self._peek(),
            )

    def _parse_trailing_block(self, counts):
        self._reject_results()
        bracket = self._take()
        prep = self._take()
        if prep.text not in ("ok", "error", "into"):
            self._error(
                "E-PARSE-UNKNOWN-PREP",
                "尾随块只允许 [ok] / [error] / [into]，实际 [%s]" % prep.text,
                bracket,
            )
        if not self._at("RBRACKET"):
            self._error("E-PARSE-UNEXPECTED", "尾随块头缺 ]", bracket)
        self._take()
        if prep.text in ("ok", "error"):
            counts[prep.text] += 1
            if counts[prep.text] > 1:
                self._error(
                    "E-PARSE-DUP-OK" if prep.text == "ok" else "E-PARSE-DUP-ERROR",
                    "[%s] 每条语句最多一次" % prep.text,
                    bracket,
                )
        body = self._parse_block("[%s] 尾随块" % prep.text)
        kind = {"ok": "OkBlock", "error": "ErrorBlock", "into": "IntoBlock"}[prep.text]
        return ast.make(kind, span={"line": bracket.line, "col": bracket.col}, body=body)

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

    def _parse_prep_block_stmt(self):
        self._reject_results()
        bracket = self._take()
        prep = self._take()
        if not self._at("RBRACKET"):
            self._error("E-PARSE-UNEXPECTED", "独立介宾块头缺 ]", bracket)
        self._take()
        if prep.text not in ("into", "ok", "error"):
            self._error(
                "E-PARSE-UNKNOWN-PREP",
                "独立介宾块只允许 [into] / [ok] / [error]，实际 [%s]" % prep.text,
                bracket,
            )
        if self._at("VARIABLE"):
            subject = self._parse_word(bare_as_string=False)
        elif self._at("VERB") or self._peek(1).kind == "VERB":
            subject = self._parse_verb_call()
        else:
            self._error(
                "E-PARSE-UNEXPECTED", "独立介宾块需要 $变量 或 verb_call 作宾语"
            )
        body = self._parse_block("[%s] 独立形式" % prep.text)
        return ast.make(
            "PrepBlockStmt",
            span={"line": bracket.line, "col": bracket.col},
            prep=prep.text,
            subject=subject,
            block=body,
        )

    def _parse_if(self):
        keyword = self._take()
        span = {"line": keyword.line, "col": keyword.col}
        branches = []
        condition = self._parse_expr()
        body = self._parse_block("if 体")
        branches.append(
            ast.make("IfBranch", span=span, condition=condition, body=body)
        )
        else_body = None
        while self._at("KEYWORD") and self._peek().text == "else-if":
            self._take()
            branch_span = {"line": self._peek().line, "col": self._peek().col}
            condition = self._parse_expr()
            body = self._parse_block("else-if 体")
            branches.append(
                ast.make(
                    "IfBranch", span=branch_span, condition=condition, body=body
                )
            )
        if self._at("KEYWORD") and self._peek().text == "else":
            self._take()
            else_body = self._parse_block("else 体")
        return ast.make(
            "IfStmt", span=span, branches=branches, else_body=else_body
        )

    def _parse_each(self):
        keyword = self._take()
        span = {"line": keyword.line, "col": keyword.col}
        var = self._expect("VARIABLE", "each 后的 $变量")
        if not self._at("LBRACKET"):
            self._error("E-PARSE-UNEXPECTED", "each 缺 [in]")
        self._take()
        prep = self._take()
        if prep.text != "in":
            self._error("E-PARSE-UNKNOWN-PREP", "each 头只接受 [in]，实际 [%s]" % prep.text, prep)
        self._expect("RBRACKET", "[in] 的 ]")
        source_start = self.i
        source = self._parse_expr()
        self._warn_bareword_source(source_start)
        body = self._parse_block("each 体")
        tail = self._parse_statement_tail(allow_assign=False)
        return ast.make(
            "EachStmt", span=span, var=var.text, source=source, body=body, tail=tail
        )

    def _warn_bareword_source(self, index):
        """§4.20 W-01：``each`` 的 ``[in]`` 右值以单个裸词开头时提示。

        PH-4 采用裁定 (a)：在归约成 ``STRING`` 之前记录来源；``parse`` 的信封
        不变，只有 ``check`` 消费。多段裸词（如 ``xs.yml``）不提示，因为提示
        文案要求“若意图是变量请写 ``$xs``”，对拼接串没有意义。
        """
        token = self.tokens[index]
        if token.kind != "BARE":
            return
        nxt = self.tokens[index + 1] if index + 1 < len(self.tokens) else self.tokens[-1]
        if nxt.kind == "VERB" or _adjacent(token, nxt):
            return
        self.warnings.append(
            {
                "code": "W-01",
                "line": token.line,
                "col": token.col,
                "message": "裸词 `%s` 按字符串处理，若意图是变量请写 `$%s`"
                % (token.text, token.text),
            }
        )

    def _parse_parallel(self):
        keyword = self._take()
        span = {"line": keyword.line, "col": keyword.col}
        self._expect("LBRACE", "parallel 的 {")
        branches = []
        while True:
            self._skip_newlines()
            if self._at("RBRACE"):
                self._take()
                break
            if self._at("EOF"):
                self._error("E-PARSE-MISSING-BLOCK", "parallel 缺 }", keyword)
            if not (
                self._peek().kind in ("BARE", "STRING", "VARIABLE", "DOLLAR", "FIELD", "MAP_REF")
                or self._at("VERB")
            ):
                self._error(
                    "E-PARSE-UNEXPECTED", "parallel 分支只能是 simple_stmt"
                )
            branches.append(self._parse_simple_stmt())
        results = None
        if (
            self._at("LBRACKET")
            and self._peek(1).text == "results"
            and self._peek(2).kind == "RBRACKET"
        ):
            self._take()
            self._take()
            self._take()
            results = self._parse_block("parallel [results]")
        pipe = self._parse_pipe(lambda: self._parse_simple_stmt())
        return ast.make(
            "ParallelStmt", span=span, branches=branches, results=results, pipe=pipe
        )

    def _parse_break(self):
        keyword = self._take()
        span = {"line": keyword.line, "col": keyword.col}
        value = None
        if self._at("VERB"):
            self._error(
                "E-PARSE-BREAK-VALUE", "break 的值只能是 value，不能是动词调用"
            )
        if not (self._at("NEWLINE", "EOF", "RBRACE", "ARROW")):
            if self._peek().kind in _WORD_KINDS:
                value = self._parse_word(bare_as_string=True)
            else:
                self._error("E-PARSE-UNEXPECTED", "break 后出现意外 token")
        target = None
        if self._at("ARROW"):
            self._take()
            target = self._expect("VARIABLE", "break -> 后的 $变量").text
        return ast.make("BreakStmt", span=span, value=value, target=target)

    def _parse_expr(self):
        starts_verb = self._at("VERB") or (
            self._peek().kind in _WORD_KINDS and self._peek(1).kind == "VERB"
        )
        if not starts_verb:
            return self._parse_word(bare_as_string=True)
        stages = [self._parse_verb_call()]
        while self._at("PIPE"):
            self._take()
            self._skip_newlines()
            stages.append(self._parse_verb_call())
        if len(stages) == 1:
            return stages[0]
        return ast.make("Pipe", span=stages[0]["span"], stages=stages)

    def _parse_call_stmt(self):
        at = self._take()
        span = {"line": at.line, "col": at.col}
        if self._at("STRING"):
            self._error(
                "E-07",
                "@ 后不再写函数名；请直接写 verb_call（如 @ <read> \"a.yml\"）",
                self._peek(),
                hint="旧形态 @ \"name\" 已移除；删除字符串名字，形状相同的定义会按形状匹配",
            )
        if not (
            self._at("VERB")
            or (self._peek().kind in _WORD_KINDS and self._peek(1).kind == "VERB")
        ):
            self._error("E-PARSE-UNEXPECTED", "@ 后必须是函数调用 verb_call")
        call = self._parse_verb_call()
        tail = self._parse_statement_tail()
        pipe = self._parse_pipe(lambda: self._parse_simple_stmt())
        return ast.make("CallStmt", span=span, call=call, tail=tail, pipe=pipe)

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
        if self._at("STRING"):
            self._error(
                "E-07",
                "@ 后不再写函数名；请直接写 verb_call（如 @ $path <read> $path）",
                self._peek(),
                hint="旧形态 @ \"name\" 已移除；签名由模板形状导出",
            )
        self.template_mode = True
        try:
            if not (self._at("VERB") or self._peek(1).kind == "VERB" or self._default_subject_ahead()):
                self._error("E-PARSE-UNEXPECTED", "函数定义缺模板")
            template = [self._parse_verb_call()]
            while self._at("PIPE"):
                self._take()
                self._skip_newlines()
                template.append(self._parse_verb_call())
        finally:
            self.template_mode = False
        definition_shape = shape.shape_of(template[0], template=True)
        body = self._parse_block("函数体")
        return ast.make(
            "FnDef",
            span=span,
            shape=definition_shape,
            template=template,
            body=body,
        )

    def _default_subject_ahead(self):
        """模板主语写成 ``$变量?默认值`` 时，``?`` 挡住了 ``<动词>`` 的探测。"""
        return (
            self._peek().kind == "VARIABLE"
            and self._peek(1).kind == "QUESTION"
        )

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
        if self._peek().kind in _WORD_KINDS and (
            self._peek(1).kind == "VERB"
            or (self.template_mode and self._default_subject_ahead())
        ):
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
        self._reject_results()
        bracket = self._take()
        prep = self._take()
        if prep.text not in _PREPS:
            self._error(
                "E-PARSE-UNKNOWN-PREP",
                "未知介词 [%s]；§4.5 只接受 %s" % (prep.text, "/".join(_PREPS)),
                prep,
            )
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
        first = self._take()
        if self.template_mode and first.kind == "VARIABLE" and self._at("QUESTION"):
            self._take()
            if self._at("NEWLINE", "EOF", "RBRACE", "PIPE"):
                self._error(
                    "E-PARSE-FN-DEFAULT",
                    "默认值缺失：$%s? 后必须有 value" % first.text,
                )
            default = self._parse_word(bare_as_string=True)
            return ast.make(
                "Default",
                span={"line": first.line, "col": first.col},
                name=first.text,
                value=default,
            )
        parts = [self._word_node(first, bare_as_string)]
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


def parse_with_warnings(tokens):
    """返回 ``(AST, warnings)``；警告来自解析期，不改 AST。"""
    parser = Parser(tokens)
    tree = parser.parse_program()
    return tree, parser.warnings


def parse(tokens):
    return parse_with_warnings(tokens)[0]
