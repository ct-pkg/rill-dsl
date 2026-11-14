"""PH-12-T4：双 profile 验收结果写回能力矩阵。

用法：python3 tests/phase12/test_host_matrix.py（退出 0 = 通过）。
覆盖 E-4：文档保留五类能力对照，新增 PH-12 验收章节、run 能力对照表
与 host-specific 差异表；同源 fixture 在 harness 中仍全绿。
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))

from support import ROOT

DOC = os.path.join(ROOT, "docs", "planning", "rill-0.1.0-host-matrix.md")
SCRIPT = os.path.join(ROOT, "tools", "check-0.1.0.sh")


def read_doc():
    assert os.path.isfile(DOC), "缺少能力矩阵：%s" % DOC
    with open(DOC, encoding="utf-8") as handle:
        return handle.read()


def case_keeps_five_capabilities():
    doc = read_doc()
    for title in (
        "## 1. 进程调用",
        "## 2. 文件与路径",
        "## 3. 环境变量",
        "## 4. 标准输入输出",
        "## 5. 退出码",
    ):
        assert title in doc, "缺少能力章节：%s" % title
    for column in ("| 维度 | Shell 宿主 | Agent 宿主 | 差异 |",):
        assert doc.count(column) >= 5, "五类能力缺少 shell/agent/差异三列"


def case_ph12_acceptance_section():
    doc = read_doc()
    assert "## 9. PH-12 双 profile 验收" in doc, "缺少 PH-12 验收章节"
    for needle in (
        "run 能否真实跑脚本",
        "同源 AST",
        "能否读真实文件",
        "能否起真实进程",
        "能否读真实环境变量",
        "未处理失败是否有 OS 退出码",
        "host-specific",
        "不影响语法/AST",
    ):
        assert needle in doc, "验收章节缺少：%s" % needle


def case_host_bucket_is_green():
    result = subprocess.run(
        ["bash", SCRIPT, "--bucket", "host"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
    assert "PASS" in result.stdout, result.stdout
    assert "host/shared/read-send" in result.stdout, result.stdout


def main():
    case_keeps_five_capabilities()
    case_ph12_acceptance_section()
    case_host_bucket_is_green()
    print("PASS phase12 matrix: 五类能力 + PH-12 验收 + host 桶绿")


if __name__ == "__main__":
    main()
