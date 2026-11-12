"""session-map 结构与阶段 0 事实。

判据（AGENTS.md §9.5）：四列表头 任务 / 对话 / 角色 / phase；
数据行四列非空；对话标题符合 §9.3。阶段 0 允许零任务行，但必须显式写明阶段。
"""

import os
import re

from common import ROOT, Result, read_lines, rel

HEADER_RX = re.compile(r"^\|\s*任务\s*\|\s*对话\s*\|\s*角色\s*\|\s*phase\s*\|\s*$")
TITLE_RX = re.compile(r"^\[rill-dsl\] (P\d{2} · .+|需求池|技术池|评审)$")

res = Result("session-map")

path = os.path.join(ROOT, "docs", "session-map.md")
if not os.path.isfile(path):
    res.fail("docs/session-map.md:1 文件缺失")
    res.finish()

lines = read_lines(path)
header_line = None
for lineno, line in enumerate(lines, 1):
    if HEADER_RX.match(line):
        header_line = lineno
        break

if header_line is None:
    res.fail("docs/session-map.md:1 缺少四列表头 '| 任务 | 对话 | 角色 | phase |'")
    res.finish()

text = "\n".join(lines)
if "阶段 0" not in text:
    res.fail("docs/session-map.md:1 未写明当前阶段 0")

rows = 0
lineno = header_line + 2  # 跳过表头与分隔行
while lineno <= len(lines):
    line = lines[lineno - 1]
    if not line.strip().startswith("|"):
        break
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    if len(cells) != 4:
        res.fail(
            "docs/session-map.md:%d 任务行应为 4 列，实际 %d 列" % (lineno, len(cells))
        )
    elif not all(cells):
        res.fail("docs/session-map.md:%d 任务行存在空列" % lineno)
    else:
        rows += 1
        if not TITLE_RX.match(cells[1]):
            res.fail(
                "docs/session-map.md:%d 对话标题 '%s' 不符合 §9.3"
                % (lineno, cells[1])
            )
    lineno += 1

if not res.failed:
    if rows == 0:
        res.ok("四列表头有效；阶段 0 无已派发任务（0 行），与“编码前”状态一致")
    else:
        res.ok("四列表头有效，%d 行任务映射四列非空且标题合规" % rows)

res.finish()
