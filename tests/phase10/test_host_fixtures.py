"""PH-10-T5：真实宿主 fixture 与端到端真脚本。

用法：python3 tests/phase10/test_host_fixtures.py（退出 0 = 通过）。
覆盖 E-1/E-4/E-6：五类能力各成功/失败共 12 例逐条断言，
每个 fixture 的 AST 在 shell / agent 下相等，并跑通 e2e 真脚本
（真读文件 → 真起进程 → 真输出）。
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from support import HOST_ROOT, ROOT, payload_of, run_cli

CAPABILITIES = ("process", "fs", "env", "stdio", "exit")
PROFILES = {"min": "min.json", "full": "full.json", "no-stdio": "no-stdio.json"}
E2E_SCRIPT = os.path.join(HOST_ROOT, "e2e", "script.rill")


def canonical(node):
    """AST 比对忽略 span；与 harness 的口径一致。"""
    if isinstance(node, dict):
        return {key: canonical(value) for key, value in node.items() if key != "span"}
    if isinstance(node, list):
        return [canonical(item) for item in node]
    return node


def fixture_dirs():
    found = []
    for name in sorted(os.listdir(HOST_ROOT)):
        path = os.path.join(HOST_ROOT, name)
        if os.path.isdir(path) and os.path.isfile(os.path.join(path, "expect.json")):
            found.append(path)
    return found


def profile_path(name):
    return os.path.join(HOST_ROOT, "profiles", PROFILES[name])


def materialize(directory, files):
    for relative, text in files.items():
        path = os.path.join(directory, relative)
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)


def check_ast(fixture, script):
    seen = {}
    for profile in ("shell", "agent"):
        result = run_cli(["parse", "--dump-ast", script, "--profile", profile])
        assert result.returncode == 0, (fixture, profile, result.stdout, result.stderr)
        seen[profile] = canonical(payload_of(result)["ast"])
    assert seen["shell"] == seen["agent"], "%s: AST 跨 profile 不一致" % fixture


def run_fixture(path):
    fixture = os.path.basename(path)
    with open(os.path.join(path, "expect.json"), encoding="utf-8") as handle:
        spec = json.load(handle)
    script = os.path.join(path, "script.rill")

    check_ast(fixture, script)

    with tempfile.TemporaryDirectory() as tmp:
        materialize(tmp, spec.get("files", {}))
        args = [
            "run",
            script,
            "--profile",
            spec.get("profile_name", "shell"),
            "--host-profile",
            profile_path(spec.get("profile", "min")),
        ]
        result = run_cli(args, cwd=tmp, env=spec.get("env"))
        payload = payload_of(result)
        expect = spec["expect"]

        assert result.returncode == expect["exit"], (
            fixture,
            result.returncode,
            result.stdout,
            result.stderr,
        )
        if "diagnostic" in expect:
            error = payload.get("error", {})
            assert error.get("code") == expect["diagnostic"]["code"], (fixture, error)
            needle = expect["diagnostic"].get("message_contains")
            if needle:
                assert needle in error.get("message", ""), (fixture, error)
        else:
            assert payload.get("ok") is expect["ok"], (fixture, payload)
            if "value" in expect:
                assert payload.get("value") == expect["value"], (fixture, payload)
            if "value_contains" in expect:
                assert expect["value_contains"] in str(payload.get("value")), (fixture, payload)
            if "error_contains" in expect:
                assert expect["error_contains"] in str(payload.get("error")), (fixture, payload)
            if "process_code" in expect:
                meta = payload.get("host_meta", {}).get("process", {})
                assert meta.get("code") == expect["process_code"], (fixture, payload)
        if "stderr_contains" in expect:
            assert expect["stderr_contains"] in result.stderr, (fixture, result.stderr)
        for relative, text in spec.get("files_after", {}).items():
            target = os.path.join(tmp, relative)
            assert os.path.isfile(target), "%s: 缺少产物 %s" % (fixture, relative)
            with open(target, encoding="utf-8") as handle:
                assert handle.read() == text, "%s: 产物内容不符" % fixture
        for relative in spec.get("files_absent", []):
            assert not os.path.exists(os.path.join(tmp, relative)), (
                "%s: %s 不应存在" % (fixture, relative)
            )
    return spec["capability"], spec["outcome"]


def case_fixture_coverage():
    found = fixture_dirs()
    assert len(found) == 12, "期望 12 个 fixture，实际 %d：%r" % (
        len(found),
        [os.path.basename(path) for path in found],
    )
    seen = {}
    for path in found:
        capability, outcome = run_fixture(path)
        assert capability in CAPABILITIES, capability
        assert outcome in ("success", "failure"), outcome
        seen.setdefault(capability, set()).add(outcome)
    for capability in CAPABILITIES:
        assert seen.get(capability) == {"success", "failure"}, (
            "%s 缺成功或失败 fixture：%r" % (capability, seen.get(capability))
        )


def case_e2e_real_script():
    result = run_cli(
        [
            "run",
            E2E_SCRIPT,
            "--profile",
            "shell",
            "--host-profile",
            profile_path("full"),
        ]
    )
    assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
    payload = payload_of(result)
    assert payload["ok"] is True, payload
    assert payload["value"] == "8080", payload
    assert result.stderr.strip() == "8080", result.stderr


def main():
    case_fixture_coverage()
    case_e2e_real_script()
    print("PASS phase10 fixtures: 12 例五类能力 + AST 一致 + e2e 真脚本")


if __name__ == "__main__":
    main()
