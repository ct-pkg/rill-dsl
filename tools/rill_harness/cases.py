"""用例发现与形状校验。

约定见 testdata/0.1.0/README.md。本模块不执行被测命令，只回答两个问题：
  1. 有哪些用例；
  2. 用例声明本身是否合法。

一个用例 = 一个目录 + source.ri + case.json。
"""

import json
import os
import re

BUCKETS = ("positive", "negative", "pending", "host", "smoke")
KINDS = ("ast", "tokens", "error", "warning", "check", "run", "host-ast-equal", "pending")
PHASES = ("p0", "p1", "p2", "p3", "p4", "r1", "r2", "r3", "r4", "h1", "h2", "i1")
STAGES = ("tokenize", "parse", "load", "any")
COMMANDS = ("tokenize", "parse", "check")
BLOCKED_BY = ("A", "B")

# 桶决定用途，kind 必须落在桶允许的集合内；不靠文件名猜。
BUCKET_KINDS = {
    "positive": ("ast", "tokens", "warning", "check", "run"),
    "negative": ("error",),
    "pending": ("pending",),
    "host": ("host-ast-equal", "check", "run"),
    "smoke": ("ast", "host-ast-equal"),
}

COMMON_KEYS = ("kind", "phase", "note", "stub_only", "sut_env", "sut", "fakes", "expect")
EXPECT_KEYS = {
    "ast": ("profiles", "ast"),
    "tokens": ("tokens",),
    "error": ("stage", "command", "code", "line", "col", "message_contains"),
    "warning": ("command", "code", "line", "col", "message_contains"),
    "check": ("profiles", "warnings"),
    "run": ("profile", "ok", "value", "error", "host_meta"),
    "host-ast-equal": ("profiles",),
    "pending": ("blocked_by", "reason", "unblocks_to", "profiles"),
}
PROFILE_NAMES = ("shell", "agent")
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

CASE_FILE = "case.json"
SOURCE_FILE = "source.ri"


class Case(object):
    def __init__(self, rel, bucket, doc, dir_path, source_path, case_path):
        self.rel = rel
        self.bucket = bucket
        self.dir_path = dir_path
        self.source_path = source_path
        self.case_path = case_path
        self.kind = doc["kind"]
        self.phase = doc["phase"]
        self.note = doc.get("note", "")
        self.stub_only = bool(doc.get("stub_only", False))
        self.sut_env = dict(doc.get("sut_env", {}))
        self.sut = doc.get("sut")
        self.fakes = doc.get("fakes", "")
        self.expect = doc["expect"]

    @property
    def name(self):
        return self.rel.rsplit("/", 1)[-1]

    @property
    def inline_expect(self):
        if self.kind == "ast":
            return self.expect.get("ast")
        if self.kind == "tokens":
            return self.expect.get("tokens")
        return None

    @property
    def has_inline_expect(self):
        return self.inline_expect is not None

    def profiles(self):
        return list(self.expect.get("profiles") or ["shell"])

    def golden_path(self, root):
        family = {"ast": "ast", "tokens": "tokens"}[self.kind]
        return os.path.join(root, "expected", family, self.rel + ".json")

    def __repr__(self):
        return "Case(%s)" % self.rel


def _is_str(value):
    return isinstance(value, str) and value.strip() != ""


def _check_keys(obj, allowed, where, errors):
    for key in sorted(obj):
        if key not in allowed:
            errors.append("%s: 未知字段 %r（允许：%s）" % (where, key, ", ".join(allowed)))


def _validate_profiles(value, where, errors, minimum=2):
    if not isinstance(value, list) or len(value) < minimum:
        errors.append("%s.profiles: 必须是至少 %d 个 profile 的数组" % (where, minimum))
        return
    for item in value:
        if item not in PROFILE_NAMES:
            errors.append("%s.profiles: 未知 profile %r" % (where, item))


def _validate_expect(case, where, errors):
    kind = case.kind
    expect = case.expect
    if not isinstance(expect, dict):
        errors.append("%s.expect: 必须是对象" % where)
        return
    _check_keys(expect, EXPECT_KEYS[kind], where + ".expect", errors)

    if kind == "ast":
        if "profiles" in expect:
            _validate_profiles(expect["profiles"], where + ".expect", errors, minimum=1)
        elif "ast" not in expect and not case.stub_only:
            # 允许 DRAFT：golden 尚未产出；由 runner 标 DRAFT，不算用例错误。
            pass
    elif kind == "tokens":
        pass
    elif kind == "error":
        stage = expect.get("stage", "any")
        if stage not in STAGES:
            errors.append("%s.expect.stage: 必须是 %s" % (where, " / ".join(STAGES)))
        command = expect.get("command", "check")
        if command not in COMMANDS:
            errors.append("%s.expect.command: 必须是 %s" % (where, " / ".join(COMMANDS)))
        for key in ("code", "message_contains"):
            if key in expect and not isinstance(expect[key], str):
                errors.append("%s.expect.%s: 必须是字符串" % (where, key))
        for key in ("line", "col"):
            if key in expect and not isinstance(expect[key], int):
                errors.append("%s.expect.%s: 必须是整数" % (where, key))
    elif kind == "warning":
        command = expect.get("command", "check")
        if command != "check":
            errors.append("%s.expect.command: warning 只支持 check" % where)
        if not _is_str(expect.get("code")):
            errors.append("%s.expect.code: warning 必须写明警告码，如 W-01" % where)
        if "message_contains" in expect and not isinstance(expect["message_contains"], str):
            errors.append("%s.expect.message_contains: 必须是字符串" % where)
        for key in ("line", "col"):
            if key in expect and not isinstance(expect[key], int):
                errors.append("%s.expect.%s: 必须是整数" % (where, key))
    elif kind == "check":
        if "profiles" in expect:
            _validate_profiles(expect["profiles"], where + ".expect", errors, minimum=1)
        warnings = expect.get("warnings")
        if warnings is not None and (
            not isinstance(warnings, list)
            or not all(isinstance(item, str) for item in warnings)
        ):
            errors.append("%s.expect.warnings: 必须是警告码字符串数组" % where)
    elif kind == "run":
        if expect.get("profile") not in PROFILE_NAMES:
            errors.append("%s.expect.profile: 必须是 shell 或 agent" % where)
        if "ok" not in expect or not isinstance(expect["ok"], bool):
            errors.append("%s.expect.ok: 必须是布尔值" % where)
        if "host_meta" in expect and not isinstance(expect["host_meta"], dict):
            errors.append("%s.expect.host_meta: 必须是对象" % where)
    elif kind == "host-ast-equal":
        _validate_profiles(expect.get("profiles"), where + ".expect", errors)
    elif kind == "pending":
        if expect.get("blocked_by") not in BLOCKED_BY:
            errors.append("%s.expect.blocked_by: 必须是 A 或 B" % where)
        if not _is_str(expect.get("reason")):
            errors.append("%s.expect.reason: 必须写明阻塞原因" % where)
        if "unblocks_to" in expect and expect["unblocks_to"] not in KINDS:
            errors.append("%s.expect.unblocks_to: 未知 kind %r" % (where, expect["unblocks_to"]))
        if "profiles" in expect:
            _validate_profiles(expect["profiles"], where + ".expect", errors)


def _load_one(root, bucket, dir_path, errors):
    rel = os.path.relpath(dir_path, root).replace(os.sep, "/")
    where = rel + "/" + CASE_FILE
    source_path = os.path.join(dir_path, SOURCE_FILE)
    case_path = os.path.join(dir_path, CASE_FILE)

    for part in rel.split("/")[1:]:
        if not NAME_RE.match(part):
            errors.append("%s: 目录名必须匹配 %s" % (rel, NAME_RE.pattern))

    if not os.path.isfile(source_path):
        errors.append("%s: 缺少 %s" % (rel, SOURCE_FILE))
        return None
    try:
        with open(source_path, encoding="utf-8") as fh:
            source = fh.read()
    except OSError as exc:
        errors.append("%s: 无法读取 %s（%s）" % (rel, SOURCE_FILE, exc))
        return None
    if not source.strip():
        errors.append("%s: %s 为空" % (rel, SOURCE_FILE))

    try:
        with open(case_path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        errors.append("%s: 无法解析（%s）" % (where, exc))
        return None

    if isinstance(doc, dict) and doc.get("retired") is True:
        # 已转正/退役的用例保留目录作为痕迹，不参与发现、统计与执行。
        return None

    if not isinstance(doc, dict):
        errors.append("%s: 顶层必须是对象" % where)
        return None
    _check_keys(doc, COMMON_KEYS, where, errors)

    if doc.get("kind") not in KINDS:
        errors.append("%s.kind: 必须是 %s" % (where, " / ".join(KINDS)))
        return None
    if doc.get("phase") not in PHASES:
        errors.append("%s.phase: 必须是 %s" % (where, " / ".join(PHASES)))
        return None
    if doc["kind"] not in BUCKET_KINDS[bucket]:
        errors.append(
            "%s.kind: %s/ 桶只允许 %s" % (where, bucket, " / ".join(BUCKET_KINDS[bucket]))
        )
        return None
    if not isinstance(doc.get("expect"), dict):
        errors.append("%s.expect: 必填对象" % where)
        return None
    if bucket == "smoke" and not doc.get("stub_only"):
        errors.append("%s.stub_only: smoke/ 用例必须显式标记 true（占位链路自证）" % where)
    if bucket != "smoke" and doc.get("stub_only"):
        errors.append("%s.stub_only: 只允许出现在 smoke/ 桶" % where)
    if "sut_env" in doc:
        if not isinstance(doc["sut_env"], dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in doc["sut_env"].items()
        ):
            errors.append("%s.sut_env: 必须是字符串到字符串的对象" % where)
    if "sut" in doc:
        if bucket != "smoke":
            errors.append("%s.sut: 只允许 smoke/ 用例覆盖被测命令" % where)
        value = doc["sut"]
        if isinstance(value, str):
            if not value.strip():
                errors.append("%s.sut: 不能为空字符串" % where)
        elif not (isinstance(value, list) and value and all(_is_str(v) for v in value)):
            errors.append("%s.sut: 必须是非空字符串或非空字符串数组" % where)
    if "fakes" in doc and not _is_str(doc["fakes"]):
        errors.append("%s.fakes: 必须是相对路径字符串" % where)

    case = Case(rel, bucket, doc, dir_path, source_path, case_path)
    _validate_expect(case, where, errors)
    return case


def discover(root):
    """返回 (cases, errors)。errors 非空时调用方必须拒绝开跑。"""
    cases = []
    errors = []
    if not os.path.isdir(root):
        return [], ["%s: 测试根目录不存在" % root]

    for bucket in BUCKETS:
        bucket_dir = os.path.join(root, bucket)
        if not os.path.isdir(bucket_dir):
            continue
        for dir_path, dir_names, file_names in os.walk(bucket_dir):
            dir_names[:] = sorted(d for d in dir_names if not d.startswith("_"))
            if CASE_FILE in file_names:
                case = _load_one(root, bucket, dir_path, errors)
                if case is not None:
                    cases.append(case)
            elif SOURCE_FILE in file_names:
                rel = os.path.relpath(dir_path, root).replace(os.sep, "/")
                errors.append("%s: 有 %s 但缺少 %s" % (rel, SOURCE_FILE, CASE_FILE))

    cases.sort(key=lambda c: c.rel)
    return cases, errors


def find_case(cases, needle):
    exact = [c for c in cases if c.rel == needle]
    if exact:
        return exact[0]
    suffix = [c for c in cases if c.rel.endswith("/" + needle) or c.name == needle]
    if len(suffix) == 1:
        return suffix[0]
    if len(suffix) > 1:
        raise KeyError("用例名 %r 不唯一：%s" % (needle, ", ".join(c.rel for c in suffix)))
    raise KeyError("找不到用例 %r" % needle)


def bucket_counts(cases):
    counts = {}
    for case in cases:
        counts[case.bucket] = counts.get(case.bucket, 0) + 1
    return counts


def kind_counts(cases):
    counts = {}
    for case in cases:
        counts[case.kind] = counts.get(case.kind, 0) + 1
    return counts
