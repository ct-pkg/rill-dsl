"""正文与条目引用的决策编号必须存在。

范围：规范层、决策层、主张层、教程、session-map、snippets、issues、根 README。
不含 docs/design/**（历史输入）与 battle/**（证据），也不含 AGENTS.md（主规范示例）。
"""

import os
import re

from common import ROOT, Result, read_lines, rel, walk_markdown

REF_RX = re.compile(r"\bD-\d{3}\b")

res = Result("decision-refs")

files = []
for sub in ("docs/spec", "docs/decisions", "docs/requirements", "docs/guides", "docs/snippets", "issues"):
    files.extend(walk_markdown(os.path.join(ROOT, sub)))
for name in ("docs/session-map.md", "README.md"):
    path = os.path.join(ROOT, name)
    if os.path.isfile(path):
        files.append(path)

count = 0
missing = {}
for path in files:
    for lineno, line in enumerate(read_lines(path), 1):
        for ref in REF_RX.findall(line):
            count += 1
            target = os.path.join(ROOT, "docs", "decisions", ref + ".md")
            if not os.path.isfile(target):
                missing.setdefault((rel(path), lineno, ref), 0)
                missing[(rel(path), lineno, ref)] += 1

for (relative, lineno, ref), _ in sorted(missing.items()):
    res.fail("%s:%d 引用 %s，但 docs/decisions/%s.md 不存在" % (relative, lineno, ref, ref))

if not res.failed:
    res.ok("%d 处 D-* 引用全部指向存在的决策记录" % count)

res.finish()
