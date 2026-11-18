"""RILL-002 回归：非字符串 break 值不得把失败吞成成功。

覆盖三处使用 ``break_error`` 的位置：parallel 分支、``[results]`` 块、函数体。
CT 与 Python 两侧都跑，断言 ``ok=false`` 且 break 值按 §4.15 落成字符串。
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CT = [os.path.join(ROOT, "ct", "bin", "rill")]
PY = [sys.executable, "-m", "rill"]


def _env():
    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.join(ROOT, "src")
    return env


def _run(sut, source):
    with tempfile.TemporaryDirectory() as tmp:
        script = os.path.join(tmp, "script.ri")
        with open(script, "w", encoding="utf-8") as handle:
            handle.write(source)
        result = subprocess.run(
            sut + ["run", script, "--profile", "shell"],
            cwd=tmp,
            env=_env(),
            capture_output=True,
            text=True,
        )
    try:
        payload = json.loads(result.stdout)
    except ValueError:
        raise AssertionError(
            "stdout 不是 JSON：%r（stderr=%r）" % (result.stdout, result.stderr)
        )
    return result.returncode, payload


def _assert_failure(sut, source, expected_error, expected_value="unchecked"):
    rc, payload = _run(sut, source)
    assert rc == 1, "退出码 %r，payload=%r" % (rc, payload)
    assert payload.get("ok") is False, payload
    assert payload.get("error") == expected_error, payload
    if expected_value != "unchecked":
        assert payload.get("value") == expected_value, payload


def test_parallel_break_number_is_failure():
    source = 'parallel {\n    <read> missing.rill [error] { break 42 }\n}\n'
    for sut in (CT, PY):
        _assert_failure(sut, source, "42", [None])


def test_results_break_number_is_failure():
    source = 'parallel {\n    <send> "x"\n} [results] {\n    break 42\n}\n'
    for sut in (CT, PY):
        _assert_failure(sut, source, "42")


def test_fn_break_number_reaches_error_block():
    source = (
        '//fn{\n@ <send> "x" { break 42 }\n}\n'
        '@ <send> "x" [error] { break $ }\n'
    )
    for sut in (CT, PY):
        rc, payload = _run(sut, source)
        assert rc == 0, (rc, payload)
        assert payload.get("ok") is True, payload
        assert payload.get("value") == "42", payload


def test_parallel_break_string_keeps_value():
    source = 'parallel {\n    <read> missing.rill [error] { break "boom" }\n}\n'
    for sut in (CT, PY):
        _assert_failure(sut, source, "boom", [None])


if __name__ == "__main__":
    test_parallel_break_number_is_failure()
    test_results_break_number_is_failure()
    test_fn_break_number_reaches_error_block()
    test_parallel_break_string_keeps_value()
    print("PASS")
