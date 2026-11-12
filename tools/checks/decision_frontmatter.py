"""决策记录字段齐全与取值合法（D0-12 / §7.12）。

最少字段：id、date、anchor、status、trigger、verdict、judge、seats、scope、
criteria、rationale、invalidation、affected。
字段可写在 YAML frontmatter，也可按 §7.12 写成同名 H2 段；两者取并集。
"""

import os
import re

from common import ROOT, Result, read_lines, rel

REQUIRED = [
    "id",
    "date",
    "anchor",
    "status",
    "trigger",
    "verdict",
    "judge",
    "seats",
    "scope",
    "criteria",
    "rationale",
    "invalidation",
    "affected",
]

# §7.12 的段名与字段名对应；段名命中任一别名即视为该字段已落盘。
SECTION_ALIASES = {
    "anchor": ["出证"],
    "trigger": ["争点"],
    "seats": ["主张书", "反证清单"],
    "verdict": ["判决"],
    "scope": ["生效范围"],
    "criteria": ["判据"],
    "rationale": ["理由"],
    "invalidation": ["失效条件"],
    "affected": ["影响面"],
}

STATUS = {"accepted", "rejected", "superseded"}
DATE_RX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FILE_ID_RX = re.compile(r"^(D-\d{3})\.md$")

res = Result("decision-frontmatter")

decisions_dir = os.path.join(ROOT, "docs", "decisions")
paths = []
if os.path.isdir(decisions_dir):
    for name in sorted(os.listdir(decisions_dir)):
        if FILE_ID_RX.match(name):
            paths.append(os.path.join(decisions_dir, name))

if not paths:
    res.fail("docs/decisions/D-001.md:1 未找到任何决策记录")
    res.finish()

for path in paths:
    relative = rel(path)
    lines = read_lines(path)
    file_id = FILE_ID_RX.match(os.path.basename(path)).group(1)

    front = {}
    if lines and lines[0].strip() == "---":
        for idx, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                break
            if line and not line.startswith(" ") and ":" in line:
                key, value = line.split(":", 1)
                front[key.strip()] = value.strip()
    else:
        res.fail("%s:1 缺少 YAML frontmatter" % relative)

    heads = [line[3:].strip() for line in lines if line.startswith("## ")]

    def present(field):
        if field in front:
            return True
        for alias in SECTION_ALIASES.get(field, []):
            if any(alias in head for head in heads):
                return True
        return False

    missing = [field for field in REQUIRED if not present(field)]
    if missing:
        res.fail("%s:1 缺字段 %s（frontmatter 或 H2 段均未提供）" % (relative, "、".join(missing)))

    if front.get("id") != file_id:
        res.fail("%s:1 id 字段 '%s' 与文件名 %s 不一致" % (relative, front.get("id"), file_id))

    if front.get("status") not in STATUS:
        res.fail(
            "%s:1 status '%s' 非法（只允许 accepted / rejected / superseded）"
            % (relative, front.get("status"))
        )

    if not DATE_RX.match(front.get("date", "")):
        res.fail("%s:1 date '%s' 不是 YYYY-MM-DD" % (relative, front.get("date")))

if not res.failed:
    res.ok("%d 份决策记录的 13 个最少字段齐全，status/date/id 合法" % len(paths))

res.finish()
