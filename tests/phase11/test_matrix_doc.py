"""PH-11-T5：能力矩阵文档的机械校验。

用法：python3 tests/phase11/test_matrix_doc.py（退出 0 = 通过）。
覆盖 E-2：五类能力各有 Shell/Agent 两列与一列文字差异；文档必须引用
同一 AST / 同一 HostCapabilities 的边界。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from support import ROOT

DOC = os.path.join(ROOT, "docs", "planning", "rill-0.1.0-host-matrix.md")
CAPABILITIES = ("进程调用", "文件与路径", "环境变量", "标准输入输出", "退出码")


def read_doc():
    assert os.path.isfile(DOC), "缺少能力矩阵：%s" % DOC
    with open(DOC, encoding="utf-8") as handle:
        return handle.read()


def section(text, keyword):
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.startswith("## ") and keyword in line:
            start = index
            break
    assert start is not None, "缺少小节：%s" % keyword
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return "\n".join(lines[start:end])


def table_header(block):
    for line in block.splitlines():
        if line.strip().startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if all(set(cell) <= set("-: ") for cell in cells):
                continue
            return cells
    raise AssertionError("小节缺少表格：\n%s" % block)


def case_document_exists():
    text = read_doc()
    for needle in (
        "HostCapabilities",
        "AST",
        "rill run --profile agent",
        "rill run --profile shell",
    ):
        assert needle in text, "矩阵缺少 %r" % needle


def case_five_capability_sections():
    text = read_doc()
    for capability in CAPABILITIES:
        block = section(text, capability)
        header = table_header(block)
        assert any("Shell" in cell for cell in header), (capability, header)
        assert any("Agent" in cell for cell in header), (capability, header)
        assert any("差异" in cell for cell in header), (capability, header)
        rows = [
            line
            for line in block.splitlines()
            if line.strip().startswith("|") and "---" not in line
        ]
        assert len(rows) >= 3, "%s 至少要有表头 + 一行内容" % capability
        for row in rows[1:]:
            cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
            assert all(cells), "%s 出现空单元格：%r" % (capability, cells)


def case_differences_are_explained():
    text = read_doc()
    for capability in CAPABILITIES:
        block = section(text, capability)
        body = "\n".join(
            line for line in block.splitlines() if not line.strip().startswith("|")
        )
        assert len(body.strip()) >= 20, "%s 缺少文字差异说明" % capability


def main():
    case_document_exists()
    case_five_capability_sections()
    case_differences_are_explained()
    print("PASS phase11 matrix: 五类能力 Shell/Agent 两列 + 文字差异")


if __name__ == "__main__":
    main()
