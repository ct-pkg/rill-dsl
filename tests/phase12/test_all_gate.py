"""PH-12-T2：``tools/check-0.1.0.sh --all`` 全样例门禁。

用法：python3 tests/phase12/test_all_gate.py（退出 0 = 通过）。
覆盖 E-1/E-2/E-5：正例、负例、host、smoke 全部执行；pending 显式计数且为 0；
任何 FAIL/BLOCK/DRAFT 都让门禁非 0。
"""

import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(ROOT, "tools", "check-0.1.0.sh")


def run_gate(*args):
    return subprocess.run(
        ["bash", SCRIPT] + list(args),
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def case_all_is_green():
    result = run_gate("--all")
    assert result.returncode == 0, (
        "check-0.1.0.sh --all 退出 %d" % result.returncode,
        result.stdout[-2000:],
        result.stderr[-2000:],
    )
    output = result.stdout
    assert "VERDICT: PASS" in output, output[-2000:]
    assert re.search(r"pending:\s+0 not run", output), output[-2000:]
    assert re.search(r"compliance:\s+\d+ passed, 0 failed, 0 blocked, 0 draft", output), (
        output[-2000:]
    )
    assert re.search(r"smoke:\s+\d+ passed, 0 failed, 0 blocked, 0 draft", output), (
        output[-2000:]
    )


def case_all_reports_bucket_counts():
    result = run_gate("--all")
    output = result.stdout
    assert re.search(r"fixtures\s*:\s*90\b", output), output[:1000]
    for bucket, count in (("positive", 60), ("negative", 27), ("host", 1), ("smoke", 2)):
        assert re.search(r"%s\s*%d\b" % (bucket, count), output), (
            bucket,
            output[:1000],
        )


def case_pending_bucket_is_empty():
    result = run_gate("--bucket", "pending")
    assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
    assert "fixtures : 0" in result.stdout, result.stdout
    assert re.search(r"pending:\s+0 not run", result.stdout), result.stdout


def main():
    case_all_is_green()
    case_all_reports_bucket_counts()
    case_pending_bucket_is_empty()
    print("PASS phase12 all: --all 全桶绿 + pending 0")


if __name__ == "__main__":
    main()
