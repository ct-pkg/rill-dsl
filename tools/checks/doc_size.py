"""DOC-S1/S2：单份文档 <= 300 行。

范围：根级 *.md + docs/**/*.md。
豁免（显式告警，不静默跳过）：
- docs/design/**：v0.1 原文与讨论稿，冻结不改写（主张层 §6 C-1 候选偏离）；
- battle/**：证据材料，不在 DOC-S2 的 docs/** 扫描面内；
- AGENTS.md 的 spec:begin..spec:end 生成块（DOC-S8）。
"""

import os

from common import ROOT, Result, read_lines, rel

MAX_LINES = 300
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
        waived.append(relative)
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
    res.warn(
        "豁免 %d 份冻结基线：%s（主张层 §6 C-1 候选偏离，未签字）"
        % (len(waived), "、".join(waived))
    )

res.finish()
