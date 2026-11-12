"""相对链接有效性：文档中的相对路径链接必须指向存在的文件。

范围：根级 README.md + docs/**/*.md + issues/**/*.md。
跳过：http(s)/mailto 等外部链接、绝对路径、纯锚点、围栏代码块内的内容。
锚点（#Lxxx、#标题）只校验路径部分，不校验 markdown 标题锚点。
"""

import os
import re
import urllib.parse

from common import ROOT, Result, read_lines, rel, walk_markdown

LINK_RX = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE_RX = re.compile(r"^\s*(```|~~~)")

res = Result("doc-links")

files = []
readme = os.path.join(ROOT, "README.md")
if os.path.isfile(readme):
    files.append(readme)
files.extend(walk_markdown(os.path.join(ROOT, "docs")))
files.extend(walk_markdown(os.path.join(ROOT, "issues")))

checked = 0
for path in files:
    base = os.path.dirname(path)
    in_fence = False
    for lineno, line in enumerate(read_lines(path), 1):
        if FENCE_RX.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for match in LINK_RX.finditer(line):
            target = match.group(1).strip()
            if not target or target.startswith("#"):
                continue
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
                continue
            if target.startswith("/"):
                continue
            target_path = urllib.parse.unquote(target.split("#", 1)[0])
            if not target_path:
                continue
            checked += 1
            resolved = os.path.normpath(os.path.join(base, target_path))
            if not os.path.exists(resolved):
                res.fail(
                    "%s:%d 断链 '%s' -> %s"
                    % (rel(path), lineno, target, rel(resolved))
                )

if not res.failed:
    res.ok("%d 个相对链接全部可解析" % checked)

res.finish()
