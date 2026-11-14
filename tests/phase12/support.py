"""PH-12 测试共用夹具：定位仓库、跑真实 CLI、读 AST。

不在本模块 import 被测实现：实现缺失时由各 test_*.py 直接报错，
红证才看得见缺的是哪一层。
"""

import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, SRC)

FIXTURE_ROOT = os.path.join(ROOT, "testdata", "0.1.0")


def env_with_src(extra=None):
    env = dict(os.environ)
    env["PYTHONPATH"] = SRC
    env.pop("RILL_TEST_SECRET", None)
    env.update(extra or {})
    return env


def run_cli(args, cwd=None, env=None):
    """真实 CLI：``python3 -m rill ...``；返回 CompletedProcess。"""
    return subprocess.run(
        [sys.executable, "-m", "rill"] + list(args),
        cwd=cwd or ROOT,
        env=env_with_src(env),
        capture_output=True,
        text=True,
    )


def payload_of(result):
    try:
        return json.loads(result.stdout)
    except ValueError:
        raise AssertionError(
            "stdout 不是 JSON：%r（stderr=%r）" % (result.stdout, result.stderr)
        )


def write_file(directory, name, text):
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def canonical(node):
    if isinstance(node, dict):
        return {key: canonical(value) for key, value in node.items() if key != "span"}
    if isinstance(node, list):
        return [canonical(item) for item in node]
    return node


def ast_of(source_path, profile="shell"):
    result = run_cli(["parse", "--dump-ast", source_path, "--profile", profile])
    assert result.returncode == 0, (source_path, profile, result.stdout, result.stderr)
    return canonical(payload_of(result)["ast"])


def fixture_sources(kinds=None):
    """返回 (rel, source_path, case) 列表；只取 case.json 合法的正例。"""
    found = []
    for bucket in ("positive", "host"):
        base = os.path.join(FIXTURE_ROOT, bucket)
        for dirpath, dir_names, file_names in os.walk(base):
            dir_names.sort()
            if "source.rill" not in file_names:
                continue
            case_path = os.path.join(dirpath, "case.json")
            if not os.path.isfile(case_path):
                continue
            with open(case_path, encoding="utf-8") as handle:
                case = json.load(handle)
            if case.get("retired"):
                continue
            if kinds is not None and case.get("kind") not in kinds:
                continue
            rel = os.path.relpath(dirpath, FIXTURE_ROOT).replace(os.sep, "/")
            found.append((rel, os.path.join(dirpath, "source.rill"), case))
    found.sort()
    return found
