"""G0 g0-landing：AGENTS.md 块外三段（实例化 8 行 / 话术路由 / 偏离登记位）。

结构判据来自 AGENTS.md §11.5 L-2：
- 0.1 实例化表 8 行且每行两列非空；
- 0.2 话术路由表每行三段非空；
- 0.3 偏离项存在（无偏离写“无”）。

注意：本次任务约束“不改 AGENTS.md”，因此 0.1 中仍写“未建/缺失”的行只告警，
不判失败；是否需要刷新由 AGENTS.md 的落笔权持有人决定。
"""

import os
import re

from common import ROOT, Result, read_lines, rel

REQUIRED_ROWS = [
    "对话清单",
    "任务-对话映射",
    "门禁入口",
    "文档 snippet",
    "Issue 台账",
    "决策记录",
    "版本落点",
    "偏离项",
]
STALE_HINTS = ("未建", "缺失", "未定")

res = Result("g0-landing")

path = os.path.join(ROOT, "AGENTS.md")
if not os.path.isfile(path):
    res.fail("AGENTS.md:1 文件缺失")
    res.finish()

lines = read_lines(path)


def last_heading(prefix):
    found = None
    for idx, line in enumerate(lines):
        if line.startswith("### ") and prefix in line:
            found = idx
    return found


def table_rows(start):
    """从标题行后收集第一张表，返回分隔行之后的数据行 [(lineno, cells)]。"""
    block = []
    idx = start + 1
    while idx < len(lines):
        line = lines[idx]
        if line.startswith("### ") or line.startswith("## "):
            break
        if line.strip().startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            block.append((idx + 1, cells))
        elif block:
            break
        idx += 1

    for position, (_, cells) in enumerate(block):
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            return block[position + 1 :]
    return block


landing = last_heading("0.1 本项目实例化")
if landing is None:
    res.fail("AGENTS.md:1 缺块外 0.1 实例化节")
else:
    rows = table_rows(landing)
    if len(rows) < 8:
        res.fail("AGENTS.md:%d 实例化表只有 %d 行，要求 8 行" % (landing + 1, len(rows)))
    else:
        res.ok("0.1 实例化表 %d 行（要求 >=8）" % len(rows))

    by_name = {}
    stale = []
    for lineno, cells in rows:
        if len(cells) != 2:
            res.fail("AGENTS.md:%d 实例化行应为 2 列，实际 %d 列" % (lineno, len(cells)))
            continue
        name, value = cells
        by_name[name] = (lineno, value)
        if not value:
            res.fail("AGENTS.md:%d %s 的值为空" % (lineno, name))
        if any(hint in value for hint in STALE_HINTS):
            stale.append(name)

    for name in REQUIRED_ROWS:
        if name not in by_name:
            res.fail("AGENTS.md:%d 实例化表缺行 '%s'" % (landing + 1, name))

    if stale:
        res.warn(
            "AGENTS.md 0.1 仍有 %d 行写“未建/缺失”：%s；本次约束不改 AGENTS.md，"
            "对应产物已建但该表需由落笔权持有人另行刷新"
            % (len(stale), "、".join(stale))
        )

routes = last_heading("0.2 话术路由")
if routes is None:
    res.fail("AGENTS.md:1 缺块外 0.2 话术路由节")
else:
    rows = table_rows(routes)
    bad = False
    if not rows:
        res.fail("AGENTS.md:%d 话术路由表为空" % (routes + 1))
        bad = True
    for lineno, cells in rows:
        if len(cells) != 3 or not all(cells):
            res.fail("AGENTS.md:%d 话术路由行应为 3 段非空，实际 %d 列" % (lineno, len(cells)))
            bad = True
    if not bad:
        res.ok("0.2 话术路由 %d 行，每行三段非空" % len(rows))

deviation = last_heading("0.3 偏离项")
if deviation is None:
    res.fail("AGENTS.md:1 缺块外 0.3 偏离登记位")
else:
    body = [line.strip() for line in lines[deviation + 1 :] if line.strip()]
    if not body:
        res.fail("AGENTS.md:%d 0.3 偏离项为空" % (deviation + 1))
    else:
        res.ok("0.3 偏离登记位存在且非空（首行：%s）" % body[0])

res.finish()
