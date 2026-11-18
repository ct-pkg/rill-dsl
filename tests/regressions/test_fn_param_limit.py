"""RILL-003 回归：函数参数收集不得有 64/512 的静默上限。

``eval_fn_call`` 原来用 ``pname[64]`` / ``stack[512]``，超限分支静默丢弃；
本测试用 65 与 600 个介宾参数覆盖这两个边界，CT 与 Python 都必须成功。
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


def _source(n):
    preps = " ".join("[to] $p%d" % i for i in range(1, n + 1))
    values = " ".join('[to] "v%d"' % i for i in range(1, n + 1))
    return (
        '//fn{\n@ <send> "x" %s { <send> $p%d }\n}\n'
        '@ <send> "x" %s\n' % (preps, n, values)
    )


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


def _assert_boundary(n):
    source = _source(n)
    for sut in (CT, PY):
        rc, payload = _run(sut, source)
        assert rc == 0, (n, rc, payload)
        assert payload.get("ok") is True, (n, payload)
        assert payload.get("value") == "v%d" % n, (n, payload)


def test_65_params_are_bound():
    _assert_boundary(65)


def test_600_params_are_bound():
    _assert_boundary(600)


if __name__ == "__main__":
    test_65_params_are_bound()
    test_600_params_are_bound()
    print("PASS")
