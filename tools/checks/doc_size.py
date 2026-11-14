"""DOC-S1/S2：单份文档 <= 300 行。

范围：根级 *.md + docs/**/*.md。
豁免（逐份打印理由，不静默跳过；登记表见 docs/DOC-S2-waivers.md）：
- docs/design/**：v0.1 原文与讨论稿，冻结不改写（主张层 §6 C-1 候选偏离）；
- battle/**：证据材料，不在 DOC-S2 的 docs/** 扫描面内；
- AGENTS.md 的 spec:begin..spec:end 生成块（DOC-S8）；
- WAIVED 表中的冻结正文/生成副本/评审档案：拆开会破坏锚点或 sha256 锁定。
"""

import os

from common import ROOT, Result, read_lines, rel

MAX_LINES = 300
WAIVED = {
    "docs/RILL-0.1.0.md": "语言规范正文，0.1.x 只读；拆分会破坏 PH 卡与决策引用的稳定锚点",
    "docs/spec/ai-coding-workflow.md": "主规范全文副本，sha256 与 AGENTS.md 生成块头锁定，不可拆分",
    "docs/RILL-0.1.0-decision-material.md": "决策评审证据归档，按决策编号连续引用，冻结不改写",
    "docs/RILL-0.1.0-decision-material-ab.md": "决策评审证据归档（A/B 组），与主材料同批冻结",
    "docs/review/v1.1-issues.md": "v1.1 历史评审档案，冻结证据，拆分会打断连续编号",
    "docs/review/v1.2-closure.md": "v1.2 历史收口档案，冻结证据",
    "docs/review/v1.2-rebuttal.md": "v1.2 历史申辩档案，冻结证据",
}
res = Result("doc-size")

scan = []
for name in ("README.md", "AGENTS.md"):
    path = os.path.join(ROOT, name)
    if os.path.isfile(path):
        scan.append(path)

for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, "docs")):
    dirnames.sort()
    for name in sorted(filenames):
        if name.endswith(".md"):
            scan.append(os.path.join(dirpath, name))

waived = []
for path in scan:
    relative = rel(path)
    if relative.startswith("docs/design/"):
        waived.append((relative, "v0.1 原文/讨论稿，冻结不改写（主张层 §6 C-1）"))
        continue
    if relative in WAIVED:
        waived.append((relative, WAIVED[relative]))
        continue

    lines = read_lines(path)
    if relative == "AGENTS.md":
        kept = []
        in_block = False
        for line in lines:
            if line.startswith("<!-- spec:begin"):
                in_block = True
                continue
            if line.startswith("<!-- spec:end"):
                in_block = False
                continue
            if not in_block:
                kept.append(line)
        count = len(kept)
        rule = "DOC-S8（剔除生成块后）"
    else:
        count = len(lines)
        rule = "DOC-S2"

    if count > MAX_LINES:
        res.fail("%s:1 %d 行 > %d（%s）" % (relative, count, MAX_LINES, rule))

if not res.failed:
    res.ok("%d 份文档均在 %d 行以内（含 AGENTS.md 剔除生成块）" % (len(scan) - len(waived), MAX_LINES))

if waived:
    for relative, reason in waived:
        res.warn("豁免 %s：%s" % (relative, reason))

res.finish()
