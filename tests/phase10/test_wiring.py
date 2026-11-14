"""PH-10-T3：真实 VerbRegistry、CLI 接线、fakes 优先级与未映射动词。

用法：python3 tests/phase10/test_wiring.py（退出 0 = 通过）。
覆盖 E-1（动词映射边界）与 E-4 的接线半边：真实 read/write/run/env、
能力拒绝变成 ``ok=false``、未映射动词报 ``E-RUN-VERB-UNREGISTERED``、
``--fakes`` 优先于真实宿主、agent 无真实宿主、shell 动词集只在 shell 生效。
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from support import payload_of, run_cli, write_script

from rill import lexer, loader, parser
from rill.errors import LoadError
from rill.host.shell import (
    ShellHost,
    ShellPolicy,
    ShellVerbRegistry,
    load_shell_profile,
)

ALLOW_ALL = {
    "process": ["run"],
    "fs": ["read", "write"],
    "env": ["get"],
    "stdio": ["write"],
}


def entry(verb, subject=None, object=None, input_value=None, post=None):
    return {
        "verb": verb,
        "subject": subject,
        "object": object,
        "post": post or [],
        "input": input_value,
    }


def host(policy, cwd=None, env=None):
    return ShellHost(policy, cwd=cwd, env=env)


def call(policy, verb, **kwargs):
    return ShellVerbRegistry(host(policy)).call(verb, entry(verb, **kwargs))


def parse_source(text):
    return parser.parse(lexer.tokenize(text))


def case_verb_map_boundary():
    mapping = ShellVerbRegistry.VERB_MAP
    assert mapping["read"] == ("fs", "read"), mapping
    assert mapping["write"] == ("fs", "write"), mapping
    assert mapping["run"] == ("process", "run"), mapping
    assert mapping["env"] == ("env", "get"), mapping
    for name in ("search", "parse", "replace", "contains", "review"):
        assert name not in mapping, "%s 不应有真实映射" % name


def case_unmapped_verbs_raise():
    registry = ShellVerbRegistry(host(ShellPolicy(ALLOW_ALL)))
    for name in ("search", "parse", "replace", "contains", "review"):
        try:
            registry.call(name, entry(name, object="x"))
        except KeyError as exc:
            text = str(exc)
            assert "E-RUN-VERB-UNREGISTERED" in text, text
            assert name in text, text
        else:
            raise AssertionError("%s 不应静默成功" % name)


def case_real_read_write_run_env():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "config.txt"), "w", encoding="utf-8") as handle:
            handle.write("port: 8080\n")
        registry = ShellVerbRegistry(
            host(ShellPolicy(ALLOW_ALL), cwd=tmp, env={"RILL_TEST_PORT": "8080"})
        )

        read = registry.call("read", entry("read", object="config.txt"))
        assert read.ok is True and read.value == "port: 8080\n", read

        write = registry.call(
            "write", entry("write", object="copy.txt", input_value=read.value)
        )
        assert write.ok is True and write.value == "copy.txt", write
        with open(os.path.join(tmp, "copy.txt"), encoding="utf-8") as handle:
            assert handle.read() == "port: 8080\n"

        run = registry.call(
            "run",
            entry("run", object="python3 -c \"print('hi')\""),
        )
        assert run.ok is True, run
        assert run.value == "hi\n", run.value
        assert run.host_meta["process"]["code"] == 0, run.host_meta

        env = registry.call("env", entry("env", object="RILL_TEST_PORT"),)
        assert env.ok is True and env.value == "8080", env


def case_denial_becomes_failure():
    policy = ShellPolicy({"fs": ["read"]})
    with tempfile.TemporaryDirectory() as tmp:
        outcome = ShellVerbRegistry(host(policy, cwd=tmp)).call(
            "write", entry("write", object="out.txt", input_value="x")
        )
        assert outcome.ok is False, outcome
        assert "E-HOST-CAPABILITY-DENIED" in outcome.error, outcome.error
        assert "fs.write" in outcome.error, outcome.error
        assert outcome.host_meta["denied"]["slot"] == "fs", outcome.host_meta
        assert not os.path.exists(os.path.join(tmp, "out.txt"))


def case_profile_loads_manifest():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "full.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "schema": "rill.shell-profile/0",
                    "name": "full",
                    "allow": ALLOW_ALL,
                    "exit_codes": {"ok": 0, "unhandled": 7},
                },
                handle,
            )
        policy = load_shell_profile(path)
        assert policy.allows("process", "run") is True
        assert policy.allows("fs", "write") is True
        assert policy.exit_code(False) == 7, policy.exit_codes
        assert policy.name == "full"


def case_cli_real_read():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "config.txt"), "w", encoding="utf-8") as handle:
            handle.write("port: 8080\n")
        write_script(tmp, "script.rill", "<read> config.txt\n")
        result = run_cli(["run", "script.rill", "--profile", "shell"], cwd=tmp)
        assert result.returncode == 0, (result.returncode, result.stderr)
        payload = payload_of(result)
        assert payload["ok"] is True, payload
        assert payload["value"] == "port: 8080\n", payload


def case_cli_fakes_win_over_real_host():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "config.txt"), "w", encoding="utf-8") as handle:
            handle.write("REAL\n")
        write_script(tmp, "script.rill", "<read> config.txt\n")
        fakes = os.path.join(tmp, "fakes.json")
        with open(fakes, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "schema": "rill-fakes-tools/0",
                    "tools": {"read": {"queue": [{"ok": True, "value": "FAKE"}]}},
                },
                handle,
            )
        result = run_cli(
            ["run", "script.rill", "--profile", "shell", "--fakes", fakes], cwd=tmp
        )
        assert result.returncode == 0, (result.returncode, result.stderr)
        payload = payload_of(result)
        assert payload["value"] == "FAKE", payload

        # fake 连能力声明都不需要：默认 shell profile 拒绝 fs.write，fake write 仍成功。
        write_script(
            tmp, "write.rill", '<write> out.txt "x"\n'
        )
        with open(fakes, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "schema": "rill-fakes-tools/0",
                    "tools": {"write": {"queue": [{"ok": True, "value": "fake"}]}},
                },
                handle,
            )
        result = run_cli(
            ["run", "write.rill", "--profile", "shell", "--fakes", fakes], cwd=tmp
        )
        payload = payload_of(result)
        assert result.returncode == 0 and payload["ok"] is True, (result.returncode, payload)
        assert payload["value"] == "fake", payload
        assert not os.path.exists(os.path.join(tmp, "out.txt"))


def case_agent_without_host_is_diagnostic():
    with tempfile.TemporaryDirectory() as tmp:
        write_script(tmp, "script.rill", "<read> config.txt\n")
        result = run_cli(["run", "script.rill", "--profile", "agent"], cwd=tmp)
        assert result.returncode == 2, (result.returncode, result.stdout, result.stderr)
        payload = payload_of(result)
        assert payload["error"]["code"] == "E-RUN-HOST-UNAVAILABLE", payload


def case_unmapped_verb_via_cli():
    with tempfile.TemporaryDirectory() as tmp:
        write_script(tmp, "script.rill", "<parse> config.txt\n")
        result = run_cli(["run", "script.rill", "--profile", "shell"], cwd=tmp)
        assert result.returncode == 2, (result.returncode, result.stdout)
        error = payload_of(result)["error"]
        assert error["code"] == "E-RUN-VERB-UNREGISTERED", error
        assert "parse" in error["message"], error


def case_missing_host_profile_is_diagnostic():
    with tempfile.TemporaryDirectory() as tmp:
        write_script(tmp, "script.rill", "<read> config.txt\n")
        result = run_cli(
            ["run", "script.rill", "--profile", "shell", "--host-profile", "nope.json"],
            cwd=tmp,
        )
        assert result.returncode == 2, (result.returncode, result.stdout)
        assert payload_of(result)["error"]["code"] == "E-RUN-HOST-PROFILE"


def case_shell_verbs_are_profile_scoped():
    tree = parse_source('<run> "echo hi"\n')
    tables = loader.check_program(tree, "shell")
    assert "run" in tables.verbs and "env" in tables.verbs
    for profile in ("agent",):
        try:
            loader.check_program(parse_source('<run> "echo hi"\n'), profile)
        except LoadError as exc:
            assert exc.code == "E-LOAD-VERB-UNKNOWN", exc.code
        else:
            raise AssertionError("%s 不应接受 run 动词" % profile)


def main():
    case_verb_map_boundary()
    case_unmapped_verbs_raise()
    case_real_read_write_run_env()
    case_denial_becomes_failure()
    case_profile_loads_manifest()
    case_cli_real_read()
    case_cli_fakes_win_over_real_host()
    case_agent_without_host_is_diagnostic()
    case_unmapped_verb_via_cli()
    case_missing_host_profile_is_diagnostic()
    case_shell_verbs_are_profile_scoped()
    print("PASS phase10 wiring: 映射边界/真实宿主/fakes 优先/未映射动词")


if __name__ == "__main__":
    main()
