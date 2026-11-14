"""RILL 0.1.x 单语句执行（PH-7）。

PH-7-T1 只落 trailing ``[into]``：按 AST 书写顺序执行，块内 ``$`` 是进入
into 的对象，某个 ``[into]`` 失败即段失败；未写 ``[error]`` 时按 §4.10
默认 ``break "RILL DSL ERROR"``，后续 ``[into]`` 不执行。

``[ok]/[error]``、段输出四态、``|>` 下游、独立 ``[into]`` 与 ``->$x``
顺序分别在 T2–T5 补齐；规范缺口见 ``docs/phases/PH-7/card.md`` §8。
"""

from . import result

DEFAULT_ERROR = result.DEFAULT_ERROR


class EvalError(Exception):
    """运行期错误；``code`` 供 CLI 输出诊断，不冒充规范错误码表。"""

    def __init__(self, code, message, line=0, col=0):
        Exception.__init__(self, message)
        self.code = code
        self.message = message
        self.line = line
        self.col = col

    def as_dict(self):
        return {
            "stage": "run",
            "code": self.code,
            "line": self.line,
            "col": self.col,
            "message": self.message,
        }


class BreakSignal(Exception):
    def __init__(self, value, target):
        Exception.__init__(self, "break")
        self.value = value
        self.target = target


class Scope(object):
    """块级变量作用域；子块新建变量不外泄，外层已有变量直接读写。"""

    def __init__(self, parent=None):
        self.parent = parent
        self.vars = {}

    def get(self, name):
        scope = self
        while scope is not None:
            if name in scope.vars:
                return scope.vars[name]
            scope = scope.parent
        raise EvalError("E-RUN-UNDEFINED", "变量 $%s 未定义" % name)

    def set(self, name, value):
        scope = self
        while scope is not None:
            if name in scope.vars:
                scope.vars[name] = value
                return
            scope = scope.parent
        self.vars[name] = value


class Interpreter(object):
    """按 AST 执行语句；``verbs`` 只需提供 ``call(name, arg) -> ExecOutcome``。"""

    def __init__(self, verbs, trace=None, functions=None):
        self.verbs = verbs
        self.trace = trace if trace is not None else []
        self.functions = functions
        self.log = []

    # ---- 程序 / 语句 ---------------------------------------------------

    def eval_program(self, program, variables=None, input_value=None):
        scope = Scope()
        if variables:
            scope.vars.update(variables)
        last = input_value
        meta = None
        try:
            for statement in program["body"]:
                outcome = self.eval_statement_in_domain(statement, scope, input_value)
                self._trace_segment(outcome)
                if not outcome.ok:
                    return outcome
                last = outcome.value
                meta = outcome.host_meta
        except BreakSignal as signal:
            if signal.target:
                scope.set(signal.target, signal.value)
            return result.ExecOutcome.success(signal.value)
        return result.ExecOutcome.success(last, host_meta=meta)

    def eval_statement(self, statement, scope, dollar):
        kind = statement["kind"]
        if kind == "SimpleStmt":
            return self.eval_simple(statement, scope, dollar)
        if kind == "PrepBlockStmt":
            return self.eval_prep_block(statement, scope, dollar)
        if kind == "BreakStmt":
            raise BreakSignal(self._break_value(statement["value"], scope, dollar), statement["target"])
        if kind == "IfStmt":
            # 控制流只有一份实现；管道与块语义仍回落到本模块。
            from . import eval_control

            return eval_control.eval_if(self, statement, scope, dollar)
        if kind == "EachStmt":
            from . import eval_control

            return eval_control.eval_each(self, statement, scope, dollar)
        if kind == "ParallelStmt":
            from . import eval_parallel

            return eval_parallel.eval_parallel(self, statement, scope, dollar)
        if kind == "CallStmt":
            from . import eval_fn

            return eval_fn.eval_call(self, statement, scope, dollar)
        raise EvalError(
            "E-RUN-UNSUPPORTED",
            "%s 不在 PH-9 的执行范围" % kind,
            statement["span"]["line"],
            statement["span"]["col"],
        )

    def eval_statement_in_domain(self, statement, scope, dollar):
        """§4.15：带 ``|>`` 的语句自成一个管道场域，break 止于管道。"""
        if statement["kind"] in ("SimpleStmt", "CallStmt", "ParallelStmt") and (
            statement["pipe"] is not None
        ):
            try:
                return self.eval_statement(statement, scope, dollar)
            except BreakSignal as signal:
                if signal.target:
                    scope.set(signal.target, signal.value)
                return result.ExecOutcome.success(signal.value)
        return self.eval_statement(statement, scope, dollar)

    # ---- simple_stmt ---------------------------------------------------

    def eval_simple(self, statement, scope, dollar):
        outcome = self._call(statement["call"], scope, dollar)
        outcome = self._apply_tail(statement["tail"], scope, outcome)
        return self._finish(statement, scope, outcome)

    def _apply_tail(self, tail, scope, outcome):
        """§4.11 段尾处理；``each`` 复用同一份，不另写 [ok]/[error] 路径。"""
        cur = result.dollar(outcome)
        failure = None if outcome.ok else outcome
        ok_block = None
        error_block = None

        for item in tail:
            kind = item["kind"]
            if kind == "Assign":
                if failure is not None:
                    continue
                scope.set(item["target"], cur)
                self.trace.append(
                    {"event": "assign", "target": item["target"], "value": cur}
                )
                continue
            if kind == "IntoBlock":
                if failure is not None:
                    continue
                block_outcome, block_dollar = self._run_block(
                    item["body"], scope, cur
                )
                self.trace.append(
                    {
                        "event": "into",
                        "ok": block_outcome.ok,
                        "value": block_dollar if block_outcome.ok else None,
                        "error": block_outcome.error,
                    }
                )
                if not block_outcome.ok:
                    failure = block_outcome
                    continue
                cur = block_dollar
                continue
            if kind == "OkBlock":
                ok_block = item
                continue
            if kind == "ErrorBlock":
                error_block = item
                continue
            raise EvalError(
                "E-RUN-UNSUPPORTED",
                "尾随块 %s 尚未实现" % kind,
                item["span"]["line"],
                item["span"]["col"],
            )

        if failure is None:
            if ok_block is not None:
                block_outcome, block_dollar = self._run_block(
                    ok_block["body"], scope, outcome.value
                )
                self.trace.append(
                    {
                        "event": "ok",
                        "triggered": True,
                        "value": block_dollar if block_outcome.ok else None,
                    }
                )
                if not block_outcome.ok:
                    return self._unhandled(block_outcome)
                cur = block_dollar
            if error_block is not None:
                self.trace.append(
                    {"event": "error", "triggered": False, "value": None}
                )
            # PH-10：段尾只改写 value/ok，不清空宿主元数据（如进程 code/stderr）。
            return result.ExecOutcome.success(cur, host_meta=outcome.host_meta)

        if ok_block is not None:
            self.trace.append({"event": "ok", "triggered": False, "value": None})
        error_string = failure.error or DEFAULT_ERROR
        if error_block is not None:
            block_outcome, block_dollar = self._run_block(
                error_block["body"], scope, error_string
            )
            self.trace.append(
                {
                    "event": "error",
                    "triggered": True,
                    "value": block_dollar if block_outcome.ok else None,
                }
            )
            if not block_outcome.ok:
                return self._unhandled(block_outcome)
            return result.ExecOutcome.success(
                block_dollar, host_meta=block_outcome.host_meta or failure.host_meta
            )
        return self._unhandled(failure)

    def _finish(self, statement, scope, outcome):
        """§4.6：段尾 ok 为真才把 value 交给 ``|>`` 下游；失败中断管道。"""
        if statement["pipe"] is None or not outcome.ok:
            return outcome
        return self.eval_simple(statement["pipe"], scope, outcome.value)

    def eval_prep_block(self, statement, scope, dollar):
        """独立形式 ``[into] $cfg { ... }`` / ``[into] <call> { ... }``。"""
        prep = statement["prep"]
        span = statement["span"]
        if prep != "into":
            raise EvalError(
                "E-RUN-UNSUPPORTED",
                "独立 [%s] 没有前置 {value, ok}，语义未定义（PH-7 卡 §8 #5）；"
                "请改用挂在产生 $ 的语句后的尾随块" % prep,
                span["line"],
                span["col"],
            )
        subject = statement["subject"]
        if subject["kind"] == "Variable":
            cur = scope.get(subject["name"])
        elif subject["kind"] == "VerbCall":
            outcome = self._call(subject, scope, dollar)
            if not outcome.ok:
                return self._unhandled(outcome)
            cur = outcome.value
        else:
            cur = self.eval_value(subject, scope, dollar)

        block_outcome, block_dollar = self._run_block(
            statement["block"], scope, cur
        )
        self.trace.append(
            {
                "event": "into",
                "ok": block_outcome.ok,
                "value": block_dollar if block_outcome.ok else None,
                "error": block_outcome.error,
            }
        )
        if not block_outcome.ok:
            return self._unhandled(block_outcome)
        if subject["kind"] == "Variable":
            scope.set(subject["name"], block_dollar)
        return result.ExecOutcome.success(block_dollar)

    def _run_block(self, block, scope, dollar, last_value=False):
        """块输出默认是块最终 ``$``；``each`` 的轮需要最后一条语句的段输出。"""
        block_scope = Scope(scope)
        outcome = result.ExecOutcome.success(dollar)
        for statement in block["body"]:
            outcome = self.eval_statement_in_domain(statement, block_scope, dollar)
            self._trace_segment(outcome)
            if not outcome.ok:
                return outcome, dollar
        if last_value:
            return outcome, dollar
        return result.ExecOutcome.success(dollar), dollar

    def _unhandled(self, outcome):
        """§4.10：未写 ``[error]`` 时失败默认 break 规范串。

        ``host_meta`` 继续透传，让进程 code/stderr 在顶层仍可观察；``$`` 不受影响。
        """
        return result.ExecOutcome.failure(
            DEFAULT_ERROR, host_meta=getattr(outcome, "host_meta", None)
        )

    # ---- 调用 ----------------------------------------------------------

    def _call(self, call, scope, dollar):
        subject = (
            self.eval_value(call["subject"], scope, dollar)
            if call["subject"] is not None
            else None
        )
        obj = self.eval_value(call["object"], scope, dollar)
        post = [self.eval_value(item, scope, dollar) for item in call["post"]]
        entry = {
            "verb": call["verb"],
            "subject": subject,
            "object": obj,
            "post": post,
            "input": dollar,
        }
        try:
            outcome = self.verbs.call(call["verb"], entry)
        except KeyError as exc:
            span = call["span"]
            raise EvalError(
                "E-RUN-VERB-UNREGISTERED", str(exc), span["line"], span["col"]
            )
        entry["ok"] = outcome.ok
        entry["value"] = outcome.value
        entry["error"] = outcome.error
        self.log.append(entry)
        self.trace.append(
            {
                "event": "call",
                "verb": call["verb"],
                "ok": outcome.ok,
                "value": outcome.value,
                "error": outcome.error,
            }
        )
        return outcome

    # ---- 值 ------------------------------------------------------------

    def eval_value(self, node, scope, dollar):
        kind = node["kind"]
        if kind == "String" or kind == "Number":
            return node["value"]
        if kind == "Bare":
            return node["text"]
        if kind == "Variable":
            return scope.get(node["name"])
        if kind == "Self":
            return dollar
        if kind == "Field":
            return result.field(dollar, node["name"])
        if kind == "Concat":
            parts = [self.eval_value(part, scope, dollar) for part in node["parts"]]
            if not all(isinstance(part, str) for part in parts):
                raise EvalError("E-RUN-CONCAT", "拼接只能用于字符串")
            return "".join(parts)
        if kind == "Adverb":
            return {
                "adverb": [self.eval_value(item, scope, dollar) for item in node["items"]]
            }
        if kind == "PrepPhrase":
            return {
                "prep": node["prep"],
                "object": self.eval_value(node["object"], scope, dollar),
            }
        raise EvalError("E-RUN-UNSUPPORTED", "值节点 %s 尚未实现" % kind)

    def _break_value(self, node, scope, dollar):
        if node is None:
            return None
        return self.eval_value(node, scope, dollar)

    def _trace_segment(self, outcome):
        self.trace.append(
            {
                "event": "segment",
                "ok": outcome.ok,
                "value": outcome.value,
                "error": outcome.error,
            }
        )
