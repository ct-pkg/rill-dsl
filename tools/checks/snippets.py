"""snippet 准入：docs/snippets/ 下除 README 外的每个文件都必须被已定稿决策支撑。

当前准入字段（见 docs/snippets/README.md）：
  ---
  decision: D-<n>     # 必须存在对应决策记录
  status: verified    # 未接门禁前不得标 verified，因此当前应为 0 个文件
  source: <正文落点>
  ---
"""

import os
import re

from common import ROOT, Result, read_lines, rel

DECISION_RX = re.compile(r"^decision:\s*(D-\d{3})\s*$")
STATUS_RX = re.compile(r"^status:\s*(\S+)\s*$")
SOURCE_RX = re.compile(r"^source:\s*\S.*$")

res = Result("snippets")

snippet_dir = os.path.join(ROOT, "docs", "snippets")
readme = os.path.join(snippet_dir, "README.md")

if not os.path.isdir(snippet_dir):
    res.fail("docs/snippets/README.md:1 目录缺失")
    res.finish()

if not os.path.isfile(readme):
    res.fail("docs/snippets/README.md:1 准入说明缺失")
else:
    res.ok("docs/snippets/README.md 存在，准入条件可查")

files = []
for dirpath, dirnames, filenames in os.walk(snippet_dir):
    dirnames.sort()
    for name in sorted(filenames):
        if name == "README.md":
            continue
        files.append(os.path.join(dirpath, name))

for path in files:
    relative = rel(path)
    lines = read_lines(path)
    front = {}
    if lines and lines[0].strip() == "---":
        for line in lines[1:]:
            if line.strip() == "---":
                break
            if DECISION_RX.match(line):
                front["decision"] = DECISION_RX.match(line).group(1)
            elif STATUS_RX.match(line):
                front["status"] = STATUS_RX.match(line).group(1)
            elif SOURCE_RX.match(line):
                front["source"] = True

    missing = [key for key in ("decision", "status", "source") if key not in front]
    if missing:
        res.fail("%s:1 snippet 缺字段 %s" % (relative, "、".join(missing)))
        continue

    if front["status"] != "verified":
        res.fail(
            "%s:1 status '%s' 非法；未接门禁前只允许 verified，当前不应有 snippet"
            % (relative, front["status"])
        )

    decision_file = os.path.join(ROOT, "docs", "decisions", front["decision"] + ".md")
    if not os.path.isfile(decision_file):
        res.fail("%s:1 引用的决策 %s 不存在" % (relative, front["decision"]))

if not res.failed:
    res.ok("%d 个 snippet 通过准入字段校验（当前应为 0）" % len(files))

res.finish()
