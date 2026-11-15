#!/usr/bin/env python3
"""Python 参考实现 vs CT 实现的逐层对拍入口。

  python3 tools/diff/diff.py --layer token          # PH-13 验收口径
  python3 tools/diff/diff.py --layer ast            # PH-14 预演（忽略 span）
  python3 tools/diff/diff.py --layer error          # PH-15 加载期（check）
  python3 tools/diff/diff.py --layer eval           # PH-16 运行期（run，10 例）
  python3 tools/diff/diff.py --layer all --bucket negative

两侧都是 ``testdata/0.1.0`` 的 SUT 协议（命令 + 退出码 + stdout JSON）：
Python 侧读 ``testdata/0.1.0/sut.json``，CT 侧读 ``tools/diff/sut.ct.json``。
用例发现规则与 harness 相同：``positive/**/source.rill`` + ``negative/**/source.rill``。

比较项（逐层取最小可比较面）：
  token 层：成功比完整 ``{"tokens":[...]}`` 信封；诊断比 ``stage/code/line/col`` 与退出码。
  ast 层：成功比忽略 ``span`` 后的 AST；诊断比 ``stage/code/line/col`` 与退出码。
  error 层：用 ``check`` 跑 ``negative/**``；诊断比 ``stage/code/line/col`` 与退出码。
            加载期负例（``negative/load/**``）由此进入对拍；正例不在本层语料内。

退出码：0 差异为 0；1 存在差异；2 用法或清单错误。
"""

import argparse
import json
import os
import subprocess
import sys

SPAN_KEYS = ("span",)


def repo_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_sut(path, root):
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        raise SystemExit("diff.py: 无法读取 %s（%s）" % (path, exc))
    command = doc.get("command")
    if not isinstance(command, list) or not command:
        raise SystemExit("diff.py: %s.command 必须是非空数组" % path)
    env = {}
    for key, value in (doc.get("env") or {}).items():
        if not isinstance(value, str):
            raise SystemExit("diff.py: %s.env.%s 必须是字符串" % (path, key))
        env[key] = value if os.path.isabs(value) else os.path.join(root, value)
    return {
        "command": command,
        "env": env,
        "timeout": doc.get("timeout_seconds", 15),
        "path": path,
    }


def discover_sources(root):
    """返回 (正例, 负例) 两组仓库相对路径，组内按路径排序。"""
    fixtures = os.path.join(root, "testdata", "0.1.0")
    found = []
    for bucket in ("positive", "negative"):
        base = os.path.join(fixtures, bucket)
        for dirpath, _dirnames, filenames in os.walk(base):
            if "source.rill" in filenames:
                rel = os.path.relpath(os.path.join(dirpath, "source.rill"), fixtures)
                found.append(rel.replace(os.sep, "/"))
    found.sort()
    positive = [p for p in found if p.startswith("positive/")]
    negative = [p for p in found if p.startswith("negative/")]
    return positive, negative


def run(sut, root, args):
    env = dict(os.environ)
    env.update(sut["env"])
    try:
        proc = subprocess.run(
            sut["command"] + list(args),
            cwd=root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=sut["timeout"],
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, None, "无法启动 %s：%s" % (" ".join(sut["command"]), exc)
    try:
        payload = json.loads(proc.stdout) if proc.stdout.strip() else None
    except ValueError as exc:
        return proc.returncode, None, "stdout 不是 JSON：%s" % exc
    if not isinstance(payload, dict):
        return proc.returncode, None, "stdout 顶层不是对象"
    return proc.returncode, payload, ""


def canonical(node):
    if isinstance(node, dict):
        return {key: canonical(value) for key, value in node.items() if key not in SPAN_KEYS}
    if isinstance(node, list):
        return [canonical(item) for item in node]
    return node


def compare_ok(layer, py_payload, ct_payload):
    if layer == "token":
        if "tokens" not in py_payload:
            return "Python 输出缺少 tokens 字段"
        if "tokens" not in ct_payload:
            return "CT 输出缺少 tokens 字段"
        return "" if py_payload == ct_payload else "tokens 信封不一致"
    if layer == "error":
        if "warnings" not in py_payload:
            return "Python 输出缺少 warnings 字段"
        if "warnings" not in ct_payload:
            return "CT 输出缺少 warnings 字段"
        return "" if py_payload == ct_payload else "warnings 信封不一致"
    if layer == "eval":
        for key in ("ok", "value", "error", "host_meta"):
            if key not in py_payload:
                return "Python 输出缺少 %s 字段" % key
            if key not in ct_payload:
                return "CT 输出缺少 %s 字段" % key
            if canonical(py_payload[key]) != canonical(ct_payload[key]):
                return "%s 不一致：py=%r ct=%r" % (
                    key,
                    py_payload[key],
                    ct_payload[key],
                )
        return ""
    if "ast" not in py_payload:
        return "Python 输出缺少 ast 字段"
    if "ast" not in ct_payload:
        return "CT 输出缺少 ast 字段"
    return "" if canonical(py_payload["ast"]) == canonical(ct_payload["ast"]) else "AST 不一致"


def compare_error(py_payload, ct_payload):
    py_err = py_payload.get("error")
    ct_err = ct_payload.get("error")
    if not isinstance(py_err, dict) or not isinstance(ct_err, dict):
        return "退出码 2 但缺少 error 对象"
    if set(py_err) != set(ct_err):
        return "error 字段集不一致：py=%s ct=%s" % (sorted(py_err), sorted(ct_err))
    fields = [key for key in ("stage", "code", "line", "col") if py_err.get(key) != ct_err.get(key)]
    if fields:
        return "error 字段不一致：%s（py=%s ct=%s）" % (
            ",".join(fields),
            {key: py_err.get(key) for key in fields},
            {key: ct_err.get(key) for key in fields},
        )
    return ""


def case_opts(root, source):
    """读 case.json 的 profile 与 fakes；缺省与 harness 一致。"""
    fakes = "fakes/tools.json"
    profile = "shell"
    path = os.path.join(root, source, "case.json")
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        fakes = doc.get("fakes") or fakes
        profile = (doc.get("expect") or {}).get("profile") or profile
    except (OSError, ValueError):
        pass
    return profile, os.path.join("testdata", "0.1.0", fakes)


def args_for(layer, root, source):
    if layer == "token":
        return ["tokenize", source]
    if layer == "error":
        return ["check", source, "--profile", "shell"]
    if layer == "eval":
        profile, fakes = case_opts(root, os.path.dirname(source))
        return ["run", source, "--profile", profile, "--fakes", fakes]
    return ["parse", "--dump-ast", source, "--profile", "shell"]


def compare_source(layer, py_sut, ct_sut, root, source):
    args = args_for(layer, root, os.path.join("testdata", "0.1.0", source))
    py_rc, py_payload, py_err = run(py_sut, root, args)
    ct_rc, ct_payload, ct_err = run(ct_sut, root, args)
    if py_err or ct_err:
        return "执行失败：py=%s ct=%s" % (py_err or "ok", ct_err or "ok"), ""
    if py_rc != ct_rc:
        return "退出码不一致：py=%s ct=%s" % (py_rc, ct_rc), ""
    if layer == "eval":
        if py_rc not in (0, 1):
            return "eval 层只比 0/1，实际退出码 %s" % py_rc, ""
        return compare_ok(layer, py_payload, ct_payload), "ok"
    if py_rc == 0:
        return compare_ok(layer, py_payload, ct_payload), "ok"
    if py_rc == 2:
        return compare_error(py_payload, ct_payload), "diagnostic"
    return "非约定退出码 %s（仅 0/2 可比）" % py_rc, ""


def main(argv):
    parser = argparse.ArgumentParser(description="Python 参考实现 vs CT 实现逐层对拍")
    parser.add_argument("--layer", choices=("token", "ast", "error", "eval", "all"), default="token")
    parser.add_argument("--bucket", choices=("positive", "negative", "all"), default="all")
    parser.add_argument("--python-sut", default="")
    parser.add_argument("--ct-sut", default="")
    parser.add_argument("--verbose", action="store_true", help="逐用例打印 PASS")
    opts = parser.parse_args(argv)

    root = repo_root()
    py_path = opts.python_sut or os.path.join(root, "testdata", "0.1.0", "sut.json")
    ct_path = opts.ct_sut or os.path.join(root, "tools", "diff", "sut.ct.json")
    py_sut = load_sut(py_path, root)
    ct_sut = load_sut(ct_path, root)

    positive, negative = discover_sources(root)
    sources = positive + negative
    if opts.bucket == "positive":
        sources = positive
    elif opts.bucket == "negative":
        sources = negative

    layers = ("token", "ast") if opts.layer == "all" else (opts.layer,)
    total_diffs = 0
    for layer in layers:
        if layer == "error":
            if opts.bucket == "positive":
                print("diff.py: --layer error 只对拍负例（negative/**）", file=sys.stderr)
                return 2
            layer_sources = negative
        elif layer == "eval":
            prefixes = (
                "positive/run/segment/",
                "positive/run/into/",
                "positive/run/pipe/",
                "positive/run/call/",
                "positive/run/control/",
                "positive/run/parallel/",
            )
            layer_sources = [s for s in positive if s.startswith(prefixes)]
        else:
            layer_sources = sources
        print("== layer=%s" % layer)
        print("   python: %s" % " ".join(py_sut["command"]))
        print("   ct    : %s" % " ".join(ct_sut["command"]))
        diffs = 0
        ok_compared = 0
        err_compared = 0
        for source in layer_sources:
            problem, status = compare_source(layer, py_sut, ct_sut, root, source)
            if problem:
                diffs += 1
                print("   DIFF %s: %s" % (source, problem))
                continue
            if status == "diagnostic":
                err_compared += 1
            else:
                ok_compared += 1
            if opts.verbose:
                print("   PASS %s" % source)
        total_diffs += diffs
        print(
            "   sources=%d ok=%d diagnostics=%d diffs=%d"
            % (len(layer_sources), ok_compared, err_compared, diffs)
        )
        print("   RESULT: %s" % ("PASS" if diffs == 0 else "FAIL"))
    print("== total diffs: %d" % total_diffs)
    return 1 if total_diffs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
