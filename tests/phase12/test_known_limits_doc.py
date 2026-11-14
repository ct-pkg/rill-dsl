"""PH-12-T6：已知限制清单。

用法：python3 tests/phase12/test_known_limits_doc.py（退出 0 = 通过）。
覆盖 E-7 的收尾说明：生产工具/权限、并发调度、pending、formatter 缺口与
``tools/check.sh all`` 的既有失败必须逐类写清，且基线数量与实测一致。
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))

from support import ROOT

DOC = os.path.join(ROOT, "docs", "planning", "rill-0.1.0-known-limits.md")
CHECK = os.path.join(ROOT, "tools", "check.sh")


def read_doc():
    assert os.path.isfile(DOC), "缺少已知限制：%s" % DOC
    with open(DOC, encoding="utf-8") as handle:
        return handle.read()


def case_sections_exist():
    doc = read_doc()
    for heading in (
        "## 1. 生产工具与权限",
        "## 2. 并发与调度",
        "## 3. pending",
        "## 4. 格式化器",
        "## 5. 文档门禁基线",
    ):
        assert heading in doc, "缺少限制章节：%s" % heading


def case_key_limits_are_named():
    doc = read_doc()
    for needle in (
        "未接",
        "未调度",
        "pending",
        "retired",
        "PH-5",
        "round-trip",
        "不影响语法/AST",
    ):
        assert needle in doc, "限制清单缺少：%s" % needle
    assert "pending=0" in doc or "pending 0" in doc or "pending（0" in doc, (
        "必须显式写 pending 0"
    )


def case_baseline_failures_match():
    doc = read_doc()
    result = subprocess.run(
        ["bash", CHECK, "all"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    fails = [line for line in result.stdout.splitlines() if line.startswith("FAIL")]
    assert len(fails) == 20, (
        "check.sh all 的 FAIL 数变了：%d（先判断是否本阶段新增）" % len(fails),
        fails[:5],
    )
    assert "20" in doc, "限制清单必须写出基线 FAIL 数 20"
    for kind in ("DOC-S2", "断链", "未定义版本"):
        assert kind in doc, "基线失败分类缺少：%s" % kind


def main():
    case_sections_exist()
    case_key_limits_are_named()
    case_baseline_failures_match()
    print("PASS phase12 limits: 生产/并发/pending/formatter/基线 20 FAIL")


if __name__ == "__main__":
    main()
