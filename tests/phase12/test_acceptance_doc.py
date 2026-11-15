"""PH-12-T5：验收报告的四类清单与真实计数一致。

用法：python3 tests/phase12/test_acceptance_doc.py（退出 0 = 通过）。
覆盖 E-1/E-2/E-5：通过/失败/pending/host-specific 四类清单齐全，
报告里的用例数与 ``--all --json`` 的真实结果一致，pending 必须写 0。
"""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))

from support import ROOT

DOC = os.path.join(ROOT, "docs", "planning", "rill-0.1.0-acceptance.md")
SCRIPT = os.path.join(ROOT, "tools", "check-0.1.0.sh")


def read_doc():
    assert os.path.isfile(DOC), "缺少验收报告：%s" % DOC
    with open(DOC, encoding="utf-8") as handle:
        return handle.read()


def gate_json():
    result = subprocess.run(
        ["bash", SCRIPT, "--all", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
    return json.loads(result.stdout)


def case_four_lists_exist():
    doc = read_doc()
    for heading in (
        "## 1. 通过",
        "## 2. 失败",
        "## 3. pending",
        "## 4. host-specific",
    ):
        assert heading in doc, "缺少清单：%s" % heading


def case_counts_match_gate():
    doc = read_doc()
    payload = gate_json()
    summary = payload["summary"]
    total = len(payload["cases"])
    passed = summary["compliance"]["PASS"] + summary["smoke"]["PASS"]
    pending = sum(summary["pending"].values())
    assert total == 90, total
    assert passed == 90, (passed, summary)
    assert pending == 0, pending
    for number in (total, passed, pending):
        assert str(number) in doc, "报告缺少计数 %d" % number
    assert "88" in doc, "报告缺少 compliance 通过数 88"
    assert "60" in doc and "27" in doc, "报告缺少 positive/negative 计数"
    assert "90" in doc, "报告缺少总数 90"
    assert "0" in doc, "报告缺少 pending 0"


def case_reports_retired_not_pending():
    doc = read_doc()
    assert "retired" in doc, "报告必须区分 retired 痕迹与 pending"
    assert gate_json()["gate"]["retired"] == 4


def case_reproduce_commands():
    doc = read_doc()
    for command in (
        "bash tools/check-0.1.0.sh --all",
        "bash tools/check-fmt.sh --roundtrip",
        "python3 tests/phase11/test_agent_fixtures.py",
    ):
        assert command in doc, "报告缺少复现命令：%s" % command


def main():
    case_four_lists_exist()
    case_counts_match_gate()
    case_reports_retired_not_pending()
    case_reproduce_commands()
    print("PASS phase12 acceptance: 四类清单 + 真实计数 85/83/pending 0")


if __name__ == "__main__":
    main()
