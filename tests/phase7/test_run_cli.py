"""PH-7-T4：`rill run` 入口能跑通 positive/run 用例并输出结构化结果。

用法：python3 tests/phase7/test_run_cli.py（退出 0 = 通过）。
"""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))

from support import ROOT

RUN_ROOT = os.path.join("testdata", "0.1.0", "positive", "run")
FAKES_ROOT = os.path.join("testdata", "0.1.0")


def cases():
    found = []
    for base, _, files in os.walk(os.path.join(ROOT, RUN_ROOT)):
        if "case.json" in files:
            found.append(base)
    return sorted(found)


def run_cli(relative_case, fakes, expected_exit):
    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.join(ROOT, "src")
    source = os.path.join(relative_case, "source.ri")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "rill",
            "run",
            source,
            "--profile",
            "shell",
            "--fakes",
            fakes,
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == expected_exit, "%s: exit %d（期望 %d），stderr=%r" % (
        relative_case,
        result.returncode,
        expected_exit,
        result.stderr.strip(),
    )
    return result


def main():
    found = cases()
    assert found, "positive/run 下没有用例"
    for case_dir in found:
        with open(os.path.join(case_dir, "case.json"), encoding="utf-8") as handle:
            spec = json.load(handle)
        relative = os.path.relpath(case_dir, ROOT)
        fakes = os.path.join(FAKES_ROOT, spec.get("fakes", "fakes/tools.json"))
        expected = spec["expect"]
        expected_exit = 0 if expected.get("ok", True) else 1
        result = run_cli(relative, fakes, expected_exit)
        try:
            payload = json.loads(result.stdout)
        except ValueError:
            raise AssertionError("%s: stdout 不是 JSON：%r" % (relative, result.stdout))
        assert payload.get("ok") == expected["ok"], "%s: ok 不符 %r" % (
            relative,
            payload,
        )
        for key in ("value", "error"):
            if key in expected:
                assert payload.get(key) == expected[key], "%s: %s 不符 %r" % (
                    relative,
                    key,
                    payload,
                )
    print("PASS phase7 run cli: %d 个 run 用例结构一致" % len(found))


if __name__ == "__main__":
    main()
