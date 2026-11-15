"""PH-11-T4：Agent fixture 与同源 AST 比对。

用法：python3 tests/phase11/test_agent_fixtures.py（退出 0 = 通过）。
覆盖 E-1/E-4：agent profile 跑完与 Shell 同源 fixture，逐 fixture 比对
两个 profile 的 AST；五类能力各有成功/失败观察点；agent 专属的
role/limits/type 也由 fixture 覆盖。
"""

import argparse
import json
import os
import shlex
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from support import (
    HOST_ROOT,
    SHARED_ROOT,
    payload_of,
    run_cli,
    write_manifest,
    write_tools,
)

SUT = []

CAPABILITIES = ("process", "fs", "env", "stdio", "exit", "role", "limits")


def canonical(node):
    if isinstance(node, dict):
        return {key: canonical(value) for key, value in node.items() if key != "span"}
    if isinstance(node, list):
        return [canonical(item) for item in node]
    return node


def fixture_dirs():
    assert os.path.isdir(HOST_ROOT), "缺少 agent fixture 目录：%s" % HOST_ROOT
    found = []
    for name in sorted(os.listdir(HOST_ROOT)):
        path = os.path.join(HOST_ROOT, name)
        if os.path.isdir(path) and os.path.isfile(os.path.join(path, "expect.json")):
            found.append(path)
    return found


def check_ast(fixture, script):
    seen = {}
    for profile in ("shell", "agent"):
        result = run_cli(["parse", "--dump-ast", script, "--profile", profile], sut=SUT)
        assert result.returncode == 0, (fixture, profile, result.stdout, result.stderr)
        seen[profile] = canonical(payload_of(result)["ast"])
    assert seen["shell"] == seen["agent"], "%s: AST 跨 profile 不一致" % fixture


def contains(actual, expected, path="$"):
    if isinstance(expected, dict):
        assert isinstance(actual, dict), (path, actual)
        for key, value in expected.items():
            assert key in actual, "%s.%s 缺失（实际 %r）" % (path, key, actual)
            contains(actual[key], value, "%s.%s" % (path, key))
        return
    if isinstance(expected, list):
        assert isinstance(actual, list) and len(actual) == len(expected), (path, actual)
        for index, (left, right) in enumerate(zip(expected, actual)):
            contains(left, right, "%s[%d]" % (path, index))
        return
    assert actual == expected, "%s: %r ≠ %r" % (path, expected, actual)


def materialize(directory, files):
    for relative, text in files.items():
        path = os.path.join(directory, relative)
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)


def run_fixture(path):
    fixture = os.path.basename(path)
    with open(os.path.join(path, "expect.json"), encoding="utf-8") as handle:
        spec = json.load(handle)
    script = os.path.join(path, "script.ri")

    check_ast(fixture, script)

    with tempfile.TemporaryDirectory() as tmp:
        materialize(tmp, spec.get("files", {}))
        write_tools(tmp, spec.get("tools", {}))
        manifest = write_manifest(tmp, **spec.get("manifest", {}))
        result = run_cli(
            [
                "run",
                script,
                "--profile",
                "agent",
                "--host-profile",
                manifest,
            ],
            cwd=tmp,
            sut=SUT,
        )
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
            if "error" in expect:
                assert payload.get("error") == expect["error"], (fixture, payload)
            if "error_contains" in expect:
                assert expect["error_contains"] in str(payload.get("error")), (fixture, payload)
            if "host_meta" in expect:
                contains(payload.get("host_meta"), expect["host_meta"])
        if "stderr" in expect:
            assert result.stderr == expect["stderr"], (fixture, result.stderr)
        for relative, text in spec.get("files_after", {}).items():
            target = os.path.join(tmp, relative)
            assert os.path.isfile(target), "%s: 缺少产物 %s" % (fixture, relative)
            with open(target, encoding="utf-8") as handle:
                assert handle.read() == text, "%s: 产物内容不符" % fixture
        for relative in spec.get("files_absent", []):
            assert not os.path.exists(os.path.join(tmp, relative)), (
                "%s: %s 不应存在" % (fixture, relative)
            )
    return spec["capability"], spec.get("outcome", "success")


def case_fixture_coverage():
    found = fixture_dirs()
    assert len(found) >= 12, "期望至少 12 个 fixture，实际 %d：%r" % (
        len(found),
        [os.path.basename(path) for path in found],
    )
    seen = {}
    for path in found:
        capability, outcome = run_fixture(path)
        assert capability in CAPABILITIES, (path, capability)
        seen.setdefault(capability, set()).add(outcome)
    for capability in CAPABILITIES:
        assert capability in seen, "缺能力 fixture：%s（实际 %r）" % (capability, seen)
    for capability in ("process", "fs", "env", "stdio"):
        assert "success" in seen[capability], (capability, seen[capability])
        assert "failure" in seen[capability], (capability, seen[capability])


def case_shared_source_is_identical():
    shared = os.path.join(SHARED_ROOT, "read-send", "source.ri")
    agent = os.path.join(HOST_ROOT, "shared-read-send", "script.ri")
    with open(shared, encoding="utf-8") as handle:
        shared_text = handle.read()
    with open(agent, encoding="utf-8") as handle:
        agent_text = handle.read()
    assert agent_text == shared_text, "同源 fixture 的源码必须逐字相同"


def case_canonical_manifest_loads():
    profile = os.path.join(HOST_ROOT, "profiles", "agent.json")
    tools = os.path.join(HOST_ROOT, "profiles", "tools.json")
    assert os.path.isfile(profile), "缺少 canonical agent manifest：%s" % profile
    assert os.path.isfile(tools), "缺少 canonical tools 注册表：%s" % tools
    from rill.host.agent import load_agent_profile

    policy = load_agent_profile(profile, cwd=HOST_ROOT)
    assert policy.role == "engineer", policy.role
    assert policy.types == {"file": "path", "net": "text"}, policy.types
    assert policy.tools.names == ("read", "run", "send", "write"), policy.tools.names
    assert policy.limits["steps"] == 32, policy.limits


def main(argv=None):
    parser = argparse.ArgumentParser(description="PH-11 agent fixture 回归")
    parser.add_argument(
        "--sut", default="", help="覆盖被测命令，如 './ct/bin/rill'；缺省 python3 -m rill"
    )
    opts = parser.parse_args(argv)
    SUT[:] = shlex.split(opts.sut) if opts.sut else []
    case_fixture_coverage()
    case_shared_source_is_identical()
    case_canonical_manifest_loads()
    print("PASS phase11 fixtures: agent 五类能力 + role/limits/type + AST 一致")


if __name__ == "__main__":
    main()
