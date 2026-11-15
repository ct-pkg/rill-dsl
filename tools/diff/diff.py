#!/usr/bin/env python3
"""Python 参考实现 vs CT 实现的逐层对拍入口。

  python3 tools/diff/diff.py --layer token          # PH-13 验收口径
  python3 tools/diff/diff.py --layer ast            # PH-14 预演（忽略 span）
  python3 tools/diff/diff.py --layer error          # PH-15 加载期（check）
  python3 tools/diff/diff.py --layer eval           # PH-16 运行期（run，10 例）
  python3 tools/diff/diff.py --layer fmt --mode compress   # PH-18 压缩态
  python3 tools/diff/diff.py --layer fmt --mode display    # PH-18 展示态
  python3 tools/diff/diff.py --layer fmt --mode roundtrip  # PH-18 压缩→展示→压缩
  python3 tools/diff/diff.py --layer all --bucket negative

两侧都是 ``testdata/0.1.0`` 的 SUT 协议（命令 + 退出码 + stdout JSON）：
Python 侧读 ``testdata/0.1.0/sut.json``，CT 侧读 ``tools/diff/sut.ct.json``。
用例发现规则与 harness 相同：``positive/**/source.rill`` + ``negative/**/source.rill``。

比较项（逐层取最小可比较面）：
  token 层：成功比完整 ``{"tokens":[...]}`` 信封；诊断比 ``stage/code/line/col`` 与退出码。
  ast 层：成功比忽略 ``span`` 后的 AST；诊断比 ``stage/code/line/col`` 与退出码。
  error 层：用 ``check`` 跑 ``negative/**``；诊断比 ``stage/code/line/col`` 与退出码。
            加载期负例（``negative/load/**``）由此进入对拍；正例不在本层语料内。
  fmt 层：71 个 round-trip 输入（45 个正例 fixture + 26 个 host 脚本）。compress /
            display 逐字节比 Python 的 ``fmt`` 输出（stdout 是纯文本，不走 JSON）；
            roundtrip 再比三段文本与各段 AST（忽略 span），两侧 AST 均须等于原文。
            另含 E-3 的 3 个定向长词用例与 E-4 的 ``//map{`` / ``//map {`` 容忍。

退出码：0 差异为 0；1 存在差异；2 用法或清单错误。
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

SPAN_KEYS = ("span",)

# PH-18 的 round-trip 语料：case.json 里这些 kind 的正例，加上双宿主脚本。
FMT_KINDS = ("ast", "check", "run", "warning", "host-ast-equal")

# E-3 定向用例：长词含空格 / 含双引号 / 含单引号。
FMT_DIRECTED = (
    ("space-longword", "//map{\ns'my application\n}\n<write> `s`.yml\n"),
    ("dquote-longword", "//map{\np'a\"b\n}\n<write> `p`\n"),
    ("squote-longword", "//map{\nq'it's here\n}\n<write> `q`\n"),
)

# E-4：头写法的空格容忍。
FMT_HEADER_TOLERANCE = (
    ("map-header-tight", "//map{\ncfg`configuration\n}\n<read> `cfg`\n"),
    ("map-header-space", "//map {\ncfg`configuration\n}\n<read> `cfg`\n"),
)


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


def run_text(sut, root, args):
    """``fmt`` 的 stdout 是纯文本，不是 JSON 信封。"""
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
        return None, "", "无法启动 %s：%s" % (" ".join(sut["command"]), exc)
    return proc.returncode, proc.stdout, ""


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def write_text(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def text_diff(py_text, ct_text):
    if py_text == ct_text:
        return ""
    limit = min(len(py_text), len(ct_text))
    index = 0
    while index < limit and py_text[index] == ct_text[index]:
        index += 1
    line = py_text.count("\n", 0, index) + 1
    col = index - (py_text.rfind("\n", 0, index) + 1) + 1
    return "第 %d 行第 %d 列起不同：py=%r ct=%r" % (
        line,
        col,
        py_text[index:index + 40],
        ct_text[index:index + 40],
    )


def fmt_sources(root):
    """71 个 round-trip 输入；规则与 ``tests/phase12`` 的 fixture 选择一致。"""
    fixtures = os.path.join(root, "testdata", "0.1.0")
    found = []
    for bucket in ("positive", "host"):
        base = os.path.join(fixtures, bucket)
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames.sort()
            if "source.rill" not in filenames:
                continue
            case_path = os.path.join(dirpath, "case.json")
            if not os.path.isfile(case_path):
                continue
            try:
                with open(case_path, encoding="utf-8") as fh:
                    case = json.load(fh)
            except (OSError, ValueError):
                continue
            if case.get("retired"):
                continue
            if case.get("kind") not in FMT_KINDS:
                continue
            rel = os.path.relpath(os.path.join(dirpath, "source.rill"), fixtures)
            found.append(rel.replace(os.sep, "/"))
    for dirpath, dirnames, filenames in os.walk(os.path.join(fixtures, "host")):
        dirnames.sort()
        if "script.rill" in filenames and "expect.json" in filenames:
            rel = os.path.relpath(os.path.join(dirpath, "script.rill"), fixtures)
            found.append(rel.replace(os.sep, "/"))
    found.sort()
    return found


def fmt_text(sut, root, mode, path):
    code, text, err = run_text(sut, root, ["fmt", "--" + mode, path])
    if err:
        return None, err
    if code != 0:
        return None, "退出码 %s（%s）" % (code, text.strip()[:120])
    return text, ""


def ast_of(sut, root, path):
    code, payload, err = run(
        sut, root, ["parse", "--dump-ast", path, "--profile", "shell"]
    )
    if err:
        return None, err
    if code != 0:
        return None, "parse 退出码 %s" % code
    if "ast" not in payload:
        return None, "缺少 ast 字段"
    return canonical(payload["ast"]), ""


def fmt_pipeline(sut, root, source_path, tmpdir, tag):
    """压缩→展示→压缩；返回三段文本与落盘路径。"""
    compressed, err = fmt_text(sut, root, "compress", source_path)
    if err:
        return None, "compress: " + err
    compress_path = os.path.join(tmpdir, tag + "-compress.rill")
    write_text(compress_path, compressed)

    displayed, err = fmt_text(sut, root, "display", compress_path)
    if err:
        return None, "display: " + err
    display_path = os.path.join(tmpdir, tag + "-display.rill")
    write_text(display_path, displayed)

    recompressed, err = fmt_text(sut, root, "compress", display_path)
    if err:
        return None, "recompress: " + err
    recompress_path = os.path.join(tmpdir, tag + "-recompress.rill")
    write_text(recompress_path, recompressed)

    return {
        "text": {
            "compress": compressed,
            "display": displayed,
            "recompress": recompressed,
        },
        "path": {
            "compress": compress_path,
            "display": display_path,
            "recompress": recompress_path,
        },
    }, ""


def compare_fmt_mode(mode, py_sut, ct_sut, root, source_path):
    py_text, py_err = fmt_text(py_sut, root, mode, source_path)
    ct_text, ct_err = fmt_text(ct_sut, root, mode, source_path)
    if py_err or ct_err:
        return "fmt 失败：py=%s ct=%s" % (py_err or "ok", ct_err or "ok")
    return text_diff(py_text, ct_text)


def compare_roundtrip(py_sut, ct_sut, root, source_path):
    tmpdir = tempfile.mkdtemp(prefix="rill-fmt-")
    try:
        py_run, err = fmt_pipeline(py_sut, root, source_path, tmpdir, "py")
        if err:
            return "python: " + err
        ct_run, err = fmt_pipeline(ct_sut, root, source_path, tmpdir, "ct")
        if err:
            return "ct: " + err

        for stage in ("compress", "display", "recompress"):
            problem = text_diff(py_run["text"][stage], ct_run["text"][stage])
            if problem:
                return "%s 文本不一致：%s" % (stage, problem)

        py_base, err = ast_of(py_sut, root, source_path)
        if err:
            return "python 原 AST: " + err
        ct_base, err = ast_of(ct_sut, root, source_path)
        if err:
            return "ct 原 AST: " + err
        if py_base != ct_base:
            return "原 AST 两侧不一致"

        for stage in ("compress", "display", "recompress"):
            for label, sut, base in (
                ("py", py_sut, py_base),
                ("ct", ct_sut, ct_base),
            ):
                tree, err = ast_of(sut, root, py_run["path"][stage])
                if err:
                    return "%s %s AST: %s" % (label, stage, err)
                if tree != base:
                    return "%s %s AST 与原文不等" % (label, stage)
                other = ct_base if label == "py" else py_base
                if tree != other:
                    return "%s %s AST 与另一实现不等" % (label, stage)
        return ""
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def compare_header_tolerance(mode, py_sut, ct_sut, root, tmpdir):
    """E-4：``//map{`` 与 ``//map {`` 必须产出同一文本。"""
    texts = {}
    for name, text in FMT_HEADER_TOLERANCE:
        path = os.path.join(tmpdir, name + ".rill")
        write_text(path, text)
        if mode == "roundtrip":
            problem = compare_roundtrip(py_sut, ct_sut, root, path)
            if problem:
                return "%s: %s" % (name, problem)
            continue
        py_text, py_err = fmt_text(py_sut, root, mode, path)
        if py_err:
            return "%s: python: %s" % (name, py_err)
        ct_text, ct_err = fmt_text(ct_sut, root, mode, path)
        if ct_err:
            return "%s: ct: %s" % (name, ct_err)
        problem = text_diff(py_text, ct_text)
        if problem:
            return "%s: %s" % (name, problem)
        texts[name] = (py_text, ct_text)
    if mode == "roundtrip":
        return ""
    tight = FMT_HEADER_TOLERANCE[0][0]
    spaced = FMT_HEADER_TOLERANCE[1][0]
    if texts[tight][0] != texts[spaced][0]:
        return "Python 两种头写法输出不一致"
    if texts[tight][1] != texts[spaced][1]:
        return "CT 两种头写法输出不一致"
    return ""


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


def run_fmt_layer(opts, py_sut, ct_sut, root):
    """fmt 层：71 例语料 + E-3 定向用例 + E-4 头写法容忍。"""
    mode = opts.mode
    sources = fmt_sources(root)
    print("== layer=fmt mode=%s" % mode)
    print("   python: %s" % " ".join(py_sut["command"]))
    print("   ct    : %s" % " ".join(ct_sut["command"]))

    diffs = 0
    for source in sources:
        path = os.path.join(root, "testdata", "0.1.0", source)
        if mode == "roundtrip":
            problem = compare_roundtrip(py_sut, ct_sut, root, path)
        else:
            problem = compare_fmt_mode(mode, py_sut, ct_sut, root, path)
        if problem:
            diffs += 1
            print("   DIFF %s: %s" % (source, problem))
        elif opts.verbose:
            print("   PASS %s" % source)
    print("   corpus=%d diffs=%d" % (len(sources), diffs))

    directed = 0
    directed_diffs = 0
    tmpdir = tempfile.mkdtemp(prefix="rill-fmt-case-")
    try:
        for name, text in FMT_DIRECTED:
            directed += 1
            path = os.path.join(tmpdir, name + ".rill")
            write_text(path, text)
            if mode == "roundtrip":
                problem = compare_roundtrip(py_sut, ct_sut, root, path)
            else:
                problem = compare_fmt_mode(mode, py_sut, ct_sut, root, path)
            if problem:
                directed_diffs += 1
                print("   DIFF directed/%s: %s" % (name, problem))
            elif opts.verbose:
                print("   PASS directed/%s" % name)

        problem = compare_header_tolerance(mode, py_sut, ct_sut, root, tmpdir)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    header_diffs = 1 if problem else 0
    if problem:
        print("   DIFF header-tolerance: %s" % problem)
    elif opts.verbose:
        print("   PASS header-tolerance")
    print(
        "   directed=%d direct_diffs=%d headers=%d header_diffs=%d"
        % (directed, directed_diffs, len(FMT_HEADER_TOLERANCE), header_diffs)
    )

    total = diffs + directed_diffs + header_diffs
    print("   RESULT: %s" % ("PASS" if total == 0 else "FAIL"))
    return total


def main(argv):
    parser = argparse.ArgumentParser(description="Python 参考实现 vs CT 实现逐层对拍")
    parser.add_argument(
        "--layer",
        choices=("token", "ast", "error", "eval", "fmt", "all"),
        default="token",
    )
    parser.add_argument("--mode", choices=("compress", "display", "roundtrip"), default="compress")
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

    if opts.layer == "fmt":
        if opts.bucket != "all":
            print("diff.py: --layer fmt 只跑固定的 71 例语料", file=sys.stderr)
            return 2
        return 1 if run_fmt_layer(opts, py_sut, ct_sut, root) else 0

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
