"""S/T 条目编号唯一、标题匹配、被索引收录、索引链接存在。

S-*：docs/spec/S-*.md；T-*：docs/spec/tools/T-*.md。
索引文件：docs/spec/README.md（表格一行一个 ID）。
"""

import os
import re

from common import ROOT, Result, read_lines, rel

ID_RX = re.compile(r"^([ST]-\d{3})-")
HEAD_RX = re.compile(r"^#\s+([ST]-\d{3})\b")
INDEX_LINK_RX = re.compile(r"\[([ST]-\d{3})\]\(([^)]+)\)")

res = Result("spec-index")

spec_dir = os.path.join(ROOT, "docs", "spec")
index_path = os.path.join(spec_dir, "README.md")

entries = []
for dirpath, dirnames, filenames in os.walk(spec_dir):
    dirnames.sort()
    for name in sorted(filenames):
        match = ID_RX.match(name)
        if match and name.endswith(".md"):
            entries.append((match.group(1), os.path.join(dirpath, name)))

if not os.path.isfile(index_path):
    res.fail("docs/spec/README.md:1 索引文件缺失")
    res.finish()

index_lines = read_lines(index_path)
index_text = "\n".join(index_lines)

seen = {}
for entry_id, path in entries:
    if entry_id in seen:
        res.fail("%s:1 编号 %s 与 %s 重复" % (rel(path), entry_id, rel(seen[entry_id])))
        continue
    seen[entry_id] = path

    lines = read_lines(path)
    if not lines or not HEAD_RX.match(lines[0]):
        res.fail("%s:1 首行标题不是 '# %s ...'" % (rel(path), entry_id))
    elif not HEAD_RX.match(lines[0]).group(1) == entry_id:
        res.fail("%s:1 标题编号与文件名不一致" % rel(path))

    if not re.search(r"\b%s\b" % re.escape(entry_id), index_text):
        res.fail("%s:1 未被 docs/spec/README.md 索引收录" % rel(path))

for lineno, line in enumerate(index_lines, 1):
    for match in INDEX_LINK_RX.finditer(line):
        entry_id, target = match.group(1), match.group(2)
        resolved = os.path.normpath(os.path.join(spec_dir, target))
        if not os.path.isfile(resolved):
            res.fail(
                "docs/spec/README.md:%d 索引链接 %s 指向不存在的文件 %s"
                % (lineno, entry_id, target)
            )

if not res.failed:
    s_count = sum(1 for entry_id, _ in entries if entry_id.startswith("S-"))
    t_count = sum(1 for entry_id, _ in entries if entry_id.startswith("T-"))
    res.ok("%d 条（S-%d / T-%d）编号唯一、标题匹配且已被索引收录" % (len(entries), s_count, t_count))

res.finish()
