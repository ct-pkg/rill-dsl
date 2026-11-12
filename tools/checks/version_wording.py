"""禁止未定义版本的措辞（如 v0.2）。

当前仓库唯一定义的规范版本是 v0.1（草案）；产品版本尚不存在。
允许出现的版本字样：v0.1、v1.7.0（主规范 pin）。其余 vX.Y[.Z] 一律报错。

范围：与 decision_refs 相同的规范面；docs/design/**（历史讨论）与
battle/**（证据）、AGENTS.md（主规范示例，如 v0.20.0）不在扫描面内。
"""

import os
import re

from common import ROOT, Result, read_lines, rel, walk_markdown

VERSION_RX = re.compile(r"\bv\d+\.\d+(?:\.\d+)?\b")
ALLOWED = {"v0.1", "v1.7.0"}

res = Result("version-wording")

files = []
for sub in ("docs/spec", "docs/decisions", "docs/requirements", "docs/guides", "docs/snippets", "issues"):
    files.extend(walk_markdown(os.path.join(ROOT, sub)))
for name in ("docs/session-map.md", "README.md"):
    path = os.path.join(ROOT, name)
    if os.path.isfile(path):
        files.append(path)

for path in files:
    for lineno, line in enumerate(read_lines(path), 1):
        for token in VERSION_RX.findall(line):
            if token not in ALLOWED:
                res.fail(
                    "%s:%d 出现未定义版本 '%s'（允许：%s）"
                    % (rel(path), lineno, token, "、".join(sorted(ALLOWED)))
                )

if not res.failed:
    res.ok("规范面未出现未定义版本措辞（允许 %s）" % "、".join(sorted(ALLOWED)))

res.finish()
