"""用例执行与比对。

结果状态只有五种，统计口径固定：
  PASS    期望满足
  FAIL    期望不满足（含 SUT 内部错误、输出不合协议）
  BLOCK   被测命令明确返回“未实现”（退出码 3）
  DRAFT   用例已声明，但 golden 尚未产出（仅 ast / tokens）
  PENDING 已登记的不确定项，默认不执行，单独统计

通过率只由 positive / negative / host 三个桶计算；smoke 是占位链路自证，单独报告；
pending 永远不进通过率。
"""

import json
import os
import shlex

from . import sut as sut_mod

PASS = "PASS"
FAIL = "FAIL"
BLOCK = "BLOCK"
DRAFT = "DRAFT"
PENDING = "PENDING"

SPAN_KEYS = ("span",)
STATUS_ORDER = (FAIL, BLOCK, DRAFT, PASS, PENDING)


class Outcome(object):
    def __init__(self, case, status, detail="", payload=None):
        self.case = case
        self.status = status
        self.detail = detail
        self.payload = payload

    def line(self):
        text = "%-7s %s (%s)" % (self.status, self.case.rel, self.case.kind)
        if self.detail:
            text += "  " + self.detail
        return text


def canonical(node):
    """AST golden 忽略 span；其余字段逐个比较。"""
    if isinstance(node, dict):
        return {
            key: canonical(value)
            for key, value in node.items()
            if key not in SPAN_KEYS
        }
    if isinstance(node, list):
        return [canonical(item) for item in node]
    return node


def first_diff(expected, actual, path="$"):
    if type(expected) is not type(actual):
        return "%s: 类型 %s ≠ %s" % (path, _short(expected), _short(actual))
    if isinstance(expected, dict):
        for key in sorted(set(expected) | set(actual)):
            if key not in expected:
                return "%s.%s: 多出字段" % (path, key)
            if key not in actual:
                return "%s.%s: 缺少字段" % (path, key)
            diff = first_diff(expected[key], actual[key], "%s.%s" % (path, key))
            if diff:
                return diff
        return ""
    if isinstance(expected, list):
        if len(expected) != len(actual):
            return "%s: 长度 %d ≠ %d" % (path, len(expected), len(actual))
        for index, (left, right) in enumerate(zip(expected, actual)):
            diff = first_diff(left, right, "%s[%d]" % (path, index))
            if diff:
                return diff
        return ""
    if expected != actual:
        return "%s: %s ≠ %s" % (path, _short(expected), _short(actual))
    return ""


def _short(value):
    text = repr(value)
    return text if len(text) <= 80 else text[:77] + "..."


def _is_subset(expected, actual):
    """host_meta 一类的“只校验声明到的键”。"""
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        for key, value in expected.items():
            if key not in actual or not _is_subset(value, actual[key]):
                return False
        return True
    if isinstance(expected, list):
        return (
            isinstance(actual, list)
            and len(expected) == len(actual)
            and all(_is_subset(a, b) for a, b in zip(expected, actual))
        )
    return expected == actual


class Runner(object):
    def __init__(self, sut, root, repo_root):
        self.sut = sut
        self.root = root
        self.repo_root = repo_root
        self._sut_cache = {}

    def sut_for(self, case):
        """smoke/ 用例可以显式指定占位命令；其余用例一律走默认被测命令。"""
        if not case.sut:
            return self.sut
        parts = shlex.split(case.sut) if isinstance(case.sut, str) else list(case.sut)
        key = tuple(parts)
        if key not in self._sut_cache:
            self._sut_cache[key] = sut_mod.Sut(parts, self.repo_root)
        return self._sut_cache[key]

    # ---- 路径 ----------------------------------------------------------

    def _repo_rel(self, path):
        return os.path.relpath(path, self.repo_root).replace(os.sep, "/")

    def _source_arg(self, case):
        return self._repo_rel(case.source_path)

    def _fakes_arg(self, case):
        path = case.fakes or "fakes/tools.json"
        return self._repo_rel(os.path.join(self.root, path))

    # ---- golden --------------------------------------------------------

    def _load_golden(self, case):
        path = case.golden_path(self.root)
        if not os.path.isfile(path):
            return None, "缺少 golden：%s" % self._repo_rel(path)
        try:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError) as exc:
            return None, "golden 无法解析：%s（%s）" % (self._repo_rel(path), exc)
        if not isinstance(doc, dict):
            return None, "golden 顶层必须是对象：%s" % self._repo_rel(path)
        if doc.get("case") != case.rel:
            return None, "golden 的 case 字段是 %r，应为 %r" % (doc.get("case"), case.rel)
        family = {"ast": "ast", "tokens": "tokens"}[case.kind]
        if family not in doc:
            return None, "golden 缺少 %r 字段：%s" % (family, self._repo_rel(path))
        return doc[family], ""

    # ---- 执行 ----------------------------------------------------------

    def run(self, case):
        if case.kind == "pending":
            reason = case.expect.get("reason", "")
            blocked = case.expect.get("blocked_by", "?")
            return Outcome(case, PENDING, "blocked_by=%s：%s" % (blocked, reason))

        expected = None
        if case.kind in ("ast", "tokens"):
            if case.has_inline_expect:
                expected = case.inline_expect
            else:
                expected, error = self._load_golden(case)
                if error:
                    return Outcome(case, DRAFT, error)

        if case.kind == "ast":
            return self._run_ast(case, expected)
        if case.kind == "tokens":
            return self._run_tokens(case, expected)
        if case.kind == "error":
            return self._run_error(case)
        if case.kind == "warning":
            return self._run_warning(case)
        if case.kind == "run":
            return self._run_run(case)
        if case.kind == "host-ast-equal":
            return self._run_host_ast(case)
        return Outcome(case, FAIL, "未知 kind：%r" % case.kind)

    def _blocked(self, case, result):
        message = result.message
        if len(message) > 160:
            message = message[:157] + "..."
        return Outcome(case, BLOCK, message or "被测命令返回未实现（退出码 3）")

    def _internal(self, case, result):
        message = result.message or "被测命令异常（退出码 %r）" % result.exit_code
        if len(message) > 200:
            message = message[:197] + "..."
        return Outcome(case, FAIL, "SUT 错误：%s" % message)

    def _run_ast(self, case, expected):
        profiles = case.profiles()
        actual = None
        for profile in profiles:
            result = self.sut_for(case).run(
                ["parse", "--dump-ast", self._source_arg(case), "--profile", profile],
                env=case.sut_env,
            )
            if result.status == "not_implemented":
                return self._blocked(case, result)
            if result.status != "ok":
                return self._internal(case, result)
            if "ast" not in result.payload:
                return Outcome(case, FAIL, "SUT 输出缺少 ast 字段")
            candidate = canonical(result.payload["ast"])
            if actual is None:
                actual = candidate
            elif candidate != actual:
                return Outcome(
                    case,
                    FAIL,
                    "profile %s 与其他 profile 的 AST 不一致" % profile,
                )
        diff = first_diff(canonical(expected), actual)
        if diff:
            return Outcome(case, FAIL, "AST 不符：%s" % diff, actual)
        return Outcome(case, PASS, "ast 与 golden 一致", actual)

    def _run_tokens(self, case, expected):
        result = self.sut_for(case).run(["tokenize", self._source_arg(case)], env=case.sut_env)
        if result.status == "not_implemented":
            return self._blocked(case, result)
        if result.status != "ok":
            return self._internal(case, result)
        if "tokens" not in result.payload:
            return Outcome(case, FAIL, "SUT 输出缺少 tokens 字段")
        actual = canonical(result.payload["tokens"])
        diff = first_diff(canonical(expected), actual)
        if diff:
            return Outcome(case, FAIL, "token 不符：%s" % diff, actual)
        return Outcome(case, PASS, "tokens 与 golden 一致", actual)

    def _run_error(self, case):
        command = case.expect.get("command", "check")
        source = self._source_arg(case)
        if command == "tokenize":
            args = ["tokenize", source]
        elif command == "parse":
            args = ["parse", "--dump-ast", source, "--profile", "shell"]
        else:
            args = ["check", source, "--profile", "shell"]
        result = self.sut_for(case).run(args, env=case.sut_env)
        if result.status == "not_implemented":
            return self._blocked(case, result)
        if result.status == "internal":
            return self._internal(case, result)
        if result.status == "ok":
            return Outcome(case, FAIL, "期望诊断，实际成功（退出码 0）")

        error = result.payload.get("error", {})
        wanted_stage = case.expect.get("stage", "any")
        if wanted_stage != "any" and error.get("stage") != wanted_stage:
            return Outcome(
                case, FAIL, "stage 不符：期望 %r，实际 %r" % (wanted_stage, error.get("stage"))
            )
        for key in ("code", "line", "col"):
            if key in case.expect and error.get(key) != case.expect[key]:
                return Outcome(
                    case,
                    FAIL,
                    "%s 不符：期望 %r，实际 %r" % (key, case.expect[key], error.get(key)),
                )
        needle = case.expect.get("message_contains")
        if needle and needle not in (error.get("message") or ""):
            return Outcome(case, FAIL, "错误信息不含 %r：%r" % (needle, error.get("message")))
        detail = "%s %s@%s:%s" % (
            error.get("stage", "?"),
            error.get("code", "-"),
            error.get("line", "?"),
            error.get("col", "?"),
        )
        return Outcome(case, PASS, detail, error)

    def _run_warning(self, case):
        result = self.sut_for(case).run(
            ["check", self._source_arg(case), "--profile", "shell"], env=case.sut_env
        )
        if result.status == "not_implemented":
            return self._blocked(case, result)
        if result.status == "diagnostic":
            error = result.payload.get("error", {})
            return Outcome(
                case,
                FAIL,
                "期望警告且 check 通过，实际报错 %s" % error.get("code", "?"),
            )
        if result.status != "ok":
            return self._internal(case, result)

        warnings = result.payload.get("warnings")
        if not isinstance(warnings, list):
            return Outcome(case, FAIL, "SUT 输出缺少 warnings 数组")
        code = case.expect["code"]
        matches = [
            item for item in warnings if isinstance(item, dict) and item.get("code") == code
        ]
        if not matches:
            actual = ", ".join(
                str(item.get("code")) for item in warnings if isinstance(item, dict)
            )
            return Outcome(case, FAIL, "未产生 %s；实际警告：%s" % (code, actual or "无"))

        for item in matches:
            for key in ("line", "col"):
                if key in case.expect and item.get(key) != case.expect[key]:
                    return Outcome(
                        case, FAIL, "%s 不符：期望 %r，实际 %r" % (key, case.expect[key], item.get(key))
                    )
            needle = case.expect.get("message_contains")
            if needle and needle not in (item.get("message") or ""):
                return Outcome(case, FAIL, "警告信息不含 %r：%r" % (needle, item.get("message")))
        return Outcome(case, PASS, "%s 已提示，check 退出 0" % code, matches[0])

    def _run_run(self, case):
        profile = case.expect["profile"]
        result = self.sut_for(case).run(
            [
                "run",
                self._source_arg(case),
                "--profile",
                profile,
                "--fakes",
                self._fakes_arg(case),
            ],
            env=case.sut_env,
        )
        if result.status == "not_implemented":
            return self._blocked(case, result)
        if result.status != "ok":
            return self._internal(case, result)
        payload = result.payload
        if payload.get("ok") != case.expect["ok"]:
            return Outcome(
                case, FAIL, "ok 不符：期望 %r，实际 %r" % (case.expect["ok"], payload.get("ok"))
            )
        for key in ("value", "error"):
            if key in case.expect:
                diff = first_diff(case.expect[key], payload.get(key), "$." + key)
                if diff:
                    return Outcome(case, FAIL, diff, payload)
        if "host_meta" in case.expect and not _is_subset(
            case.expect["host_meta"], payload.get("host_meta")
        ):
            return Outcome(
                case,
                FAIL,
                "host_meta 不符：期望包含 %r，实际 %r"
                % (case.expect["host_meta"], payload.get("host_meta")),
                payload,
            )
        return Outcome(case, PASS, "运行结果与声明一致", payload)

    def _run_host_ast(self, case):
        profiles = case.expect.get("profiles") or []
        seen = {}
        for profile in profiles:
            result = self.sut_for(case).run(
                ["parse", "--dump-ast", self._source_arg(case), "--profile", profile],
                env=case.sut_env,
            )
            if result.status == "not_implemented":
                return self._blocked(case, result)
            if result.status != "ok":
                return self._internal(case, result)
            if "ast" not in result.payload:
                return Outcome(case, FAIL, "profile %s 的输出缺少 ast 字段" % profile)
            seen[profile] = canonical(result.payload["ast"])
        if len(seen) < 2:
            return Outcome(case, FAIL, "host-ast-equal 至少需要两个 profile")
        baseline_name = profiles[0]
        baseline = seen[baseline_name]
        for profile in profiles[1:]:
            diff = first_diff(baseline, seen[profile])
            if diff:
                return Outcome(
                    case,
                    FAIL,
                    "%s 与 %s 的 AST 不一致：%s" % (baseline_name, profile, diff),
                )
        return Outcome(case, PASS, "AST 在 %s 下相等" % " / ".join(profiles), baseline)
