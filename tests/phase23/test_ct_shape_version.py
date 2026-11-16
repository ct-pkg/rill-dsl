"""PH-23-T3：CT 侧版本断言与 Python 同码同位。

覆盖 E-10。需要 ct 编译器和 ct/build.sh；两者缺失时直接失败，不跳过。
"""

import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GEN = os.path.join(ROOT, "ct", "build", "gen-lib")
LIB = os.path.join(ROOT, "ct", "build", "librill_core.a")
SOURCE = os.path.join(ROOT, "tests", "phase23", "ct", "shape_version_test.c")


def _run(command, cwd=ROOT):
    return subprocess.run(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )


def test_ct_loader_rejects_v1_shape():
    build = _run(["bash", os.path.join(ROOT, "ct", "build.sh")])
    assert build.returncode == 0, build.stdout + build.stderr

    with tempfile.TemporaryDirectory(prefix="rill-ph23-ct-") as tmp:
        exe = os.path.join(tmp, "shape_version_test")
        compile_ = _run(
            [
                "cc",
                "-std=c99",
                "-Wall",
                "-Wextra",
                "-I",
                GEN,
                "-I",
                os.path.join(ROOT, "ct", "src", "host"),
                SOURCE,
                LIB,
                "-o",
                exe,
            ]
        )
        assert compile_.returncode == 0, compile_.stderr
        proc = _run([exe])

    assert proc.stdout.strip() != "NOFAIL", "CT 未断言 shape_version"
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    error = payload["error"]
    assert error["code"] == "E-LOAD-FN-SHAPE-VERSION", error
    assert (error["line"], error["col"]) == (2, 1), error


TESTS = [value for key, value in sorted(globals().items()) if key.startswith("test_")]


def main():
    for test in TESTS:
        test()
    print("PASS phase23 ct shape version: %d 项" % len(TESTS))


if __name__ == "__main__":
    main()
