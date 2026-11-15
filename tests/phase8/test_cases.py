"""PH-8-T4：`positive/run/control/` 用例与轨迹 golden。

用法：python3 tests/phase8/test_cases.py（退出 0 = 通过）。
覆盖 E-1（管道段边界与错误归属）与 E-6（run 用例可独立验收）。
golden 只记录解释器的轨迹投影，不替代 test_if / test_each / test_break
里的语义断言。
"""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))

from support import ROOT, parse_source

from rill import fakes as fakes_mod
from rill.eval_simple import Interpreter

CASES_ROOT = os.path.join(ROOT, "testdata", "0.1.0")
RUN_ROOT = os.path.join(CASES_ROOT, "positive", "run", "control")
GOLDEN_ROOT = os.path.join(CASES_ROOT, "expected", "run")

CASES = (
    "if-subject",
    "each-value",
    "each-round-failure",
    "each-level-error",
    "pipe-three",
    "pipe-segment-error",
    "break-pipe",
)

GOLDEN = ("pipe-segment-error", "each-round-failure")


def case_dir(name):
    return os.path.join(RUN_ROOT, name)


def fakes_path(spec):
    return os.path.join(CASES_ROOT, spec.get("fakes", "fakes/tools.json"))


def run_cli(name, spec):
    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.join(ROOT, "src")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "rill",
            "run",
            os.path.join(case_dir(name), "source.ri"),
            "--profile",
            spec["expect"]["profile"],
            "--fakes",
            fakes_path(spec),
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    expected_exit = 0 if spec["expect"].get("ok", True) else 1
    assert result.returncode == expected_exit, "%s: exit %d（期望 %d），stderr=%r" % (
        name,
        result.returncode,
        expected_exit,
        result.stderr.strip(),
    )
    return json.loads(result.stdout)


def case_run_cases_exist_and_pass():
    for name in CASES:
        directory = case_dir(name)
        assert os.path.isdir(directory), "缺少用例：positive/run/control/%s" % name
        with open(os.path.join(directory, "case.json"), encoding="utf-8") as handle:
            spec = json.load(handle)
        payload = run_cli(name, spec)
        expected = spec["expect"]
        assert payload.get("ok") == expected["ok"], "%s: ok 不符 %r" % (name, payload)
        for key in ("value", "error"):
            if key in expected:
                assert payload.get(key) == expected[key], "%s: %s 不符 %r" % (
                    name,
                    key,
                    payload,
                )


def case_trace_golden():
    for name in GOLDEN:
        path = os.path.join(GOLDEN_ROOT, "control-%s.json" % name)
        assert os.path.isfile(path), "缺少轨迹 golden：expected/run/control-%s.json" % name
        with open(path, encoding="utf-8") as handle:
            golden = json.load(handle)
        with open(os.path.join(case_dir(name), "case.json"), encoding="utf-8") as handle:
            spec = json.load(handle)
        with open(os.path.join(case_dir(name), "source.ri"), encoding="utf-8") as handle:
            source = handle.read()
        interp = Interpreter(fakes_mod.load_tools(fakes_path(spec)))
        outcome = interp.eval_program(parse_source(source))

        assert golden["case"] == "positive/run/control/%s" % name, golden["case"]
        assert outcome.ok is golden["run"]["ok"], "%s: ok 不符" % name
        assert outcome.value == golden["run"]["value"], "%s: value 不符" % name
        assert outcome.error == golden["run"]["error"], "%s: error 不符" % name
        assert interp.trace == golden["trace"], "%s: 轨迹与 golden 不符" % name
        assert interp.log == golden["log"], "%s: 工具调用序列与 golden 不符" % name


def main():
    case_run_cases_exist_and_pass()
    case_trace_golden()
    print("PASS phase8 cases: %d 个 run 用例、%d 份轨迹 golden" % (len(CASES), len(GOLDEN)))


if __name__ == "__main__":
    main()
