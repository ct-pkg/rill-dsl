"""G8 g8-phase-freeze：首个实现提交后，退出判据与任务清单不可改。

做法：对每张卡片取 git 历史；找到第一条 subject 为 feat/fix 且含 `PH-<n>` 的提交作为
首个实现提交；把该提交的父提交里的卡片作为冻结基线，与工作树逐字比对
`exit-criteria`（退出判据）与 `tasks`（任务清单）两节。

- 卡片尚未提交（如事后补记阶段）→ SKIP，不伪造通过；
- 没有实现提交 → SKIP（尚未进入冻结窗口）；
- 卡片在首个实现提交时才加入 → FAIL（无法冻结）。
"""

import os
import re
import subprocess

from common import ROOT, Result, read_lines, rel

FROZEN_SECTIONS = ("退出判据", "任务清单")
res = Result("g8-phase-freeze")


def git(args):
    return subprocess.run(
        ["git", "-C", ROOT] + args, capture_output=True, text=True
    )


def find_cards():
    top = os.path.join(ROOT, "docs", "phases")
    found = []
    if not os.path.isdir(top):
        return found
    for name in sorted(os.listdir(top)):
        match = re.fullmatch(r"PH-(\d+)", name)
        if not match:
            continue
        path = os.path.join(top, name, "card.md")
        if os.path.isfile(path):
            found.append((int(match.group(1)), name, path))
    return found


def extract_section(text, keyword):
    lines = text.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if line.startswith("## ") and keyword in line:
            start = idx
            break
    if start is None:
        return None
    end = len(lines)
    for idx in range(start + 1, len(lines)):
        if lines[idx].startswith("## "):
            end = idx
            break
    return "\n".join(line.rstrip() for line in lines[start:end]).strip("\n")


def heading_line(lines, keyword):
    for idx, line in enumerate(lines):
        if line.startswith("## ") and keyword in line:
            return idx + 1
    return 1


probe = git(["rev-parse", "--show-toplevel"])
if probe.returncode != 0:
    res.skip("当前 ROOT 不是 git 仓库：%s" % ROOT)
    res.finish()

cards = find_cards()
if not cards:
    res.fail("docs/phases:1 未找到任何 PH-<n>/card.md")

history = git(["log", "--reverse", "--format=%H%x09%s"])
if history.returncode != 0:
    res.fail("git log 失败：%s" % history.stderr.strip())
    res.finish()
commits = [line.split("\t", 1) for line in history.stdout.splitlines() if line.strip()]

for number, dirname, path in cards:
    relpath = "docs/phases/%s/card.md" % dirname
    impl = None
    for sha, subject in commits:
        if re.match(r"^(feat|fix)(\([^)]*\))?:", subject) and re.search(
            r"\bPH-%d\b" % number, subject
        ):
            impl = (sha, subject)
            break
    if impl is None:
        res.skip("%s 无实现提交，冻结窗口未打开" % dirname)
        continue

    parent = impl[0] + "~1"
    frozen_raw = git(["show", "%s:%s" % (parent, relpath)])
    if frozen_raw.returncode != 0:
        res.fail(
            "%s:1 首个实现提交 %s 的父提交没有该卡片，无法冻结判据"
            % (relpath, impl[0][:7])
        )
        continue

    current_text = "\n".join(read_lines(path))
    current_lines = read_lines(path)
    changed = False
    for keyword in FROZEN_SECTIONS:
        frozen = extract_section(frozen_raw.stdout, keyword)
        current = extract_section(current_text, keyword)
        if frozen is None:
            res.fail("%s:1 冻结基线缺「%s」节，判据不完整" % (relpath, keyword))
            changed = True
        elif current != frozen:
            res.fail(
                "%s:%d 「%s」在首个实现提交 %s 之后被修改；要改只能关闭当前 phase 另开"
                % (relpath, heading_line(current_lines, keyword), keyword, impl[0][:7])
            )
            changed = True
    if not changed:
        res.ok("%s 的退出判据与任务清单自 %s 起未变" % (relpath, impl[0][:7]))

res.finish()
