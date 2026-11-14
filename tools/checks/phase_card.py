"""G1 g1-phase-card：phase 卡片必填项、任务四要素与退出判据。

判据（主规范 §6.2 / §6.6）：
- 必填十项齐全且非空；编号与目录一致；
- 任务行四要素齐全（交付物 / verify / 一次实现提交 / git revert 回滚），effort ∈ {S,M}；
- 退出判据每行带 ID 与可核对锚点，并显式含「任务清单每项可独立验收（T-6）」；
- 任一任务不得覆盖全部退出判据（T-5）；
- version-minor 等于 PH-<n>（子检查前缀 g1-version）。
"""

import os
import re

from common import ROOT, Result, read_lines, rel

REQUIRED_FIELDS = [
    "编号",
    "目标",
    "范围",
    "交付物清单",
    "任务清单",
    "退出判据",
    "依赖",
    "规范版本",
    "version-minor",
    "已知风险",
]
REQUIRED_TASK_COLUMNS = ["ID", "交付物", "提交", "回滚", "verify", "effort", "覆盖"]
EXIT_ID_RX = re.compile(r"^E-(\d+)$")
TASK_ID_RX = re.compile(r"^PH-(\d+)-T\d+$")
NUMBER_RX = re.compile(r"\d+")

res = Result("g1-phase-card")


def split_row(line):
    body = line.strip().strip("|")
    parts = re.split(r"(?<!\\)\|", body)
    return [cell.strip().replace("\\|", "|") for cell in parts]


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


def section(lines, keyword):
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
    return start, end


def table_rows(lines, start, end):
    rows = []
    for idx in range(start + 1, end):
        line = lines[idx]
        if not line.strip().startswith("|"):
            continue
        cells = split_row(line)
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append((idx + 1, cells))
    return rows


def check_card(number, dirname, path, lines):
    tag = "docs/phases/%s/card.md" % dirname

    # §0 必填十项
    sec = section(lines, "开卡必填")
    if sec is None:
        res.fail("%s:1 缺少「## 0. 开卡必填」节" % tag)
        return
    fields = {}
    for lineno, cells in table_rows(lines, sec[0], sec[1]):
        if len(cells) < 2:
            res.fail("%s:%d 必填项行应为 2 列，实际 %d 列" % (tag, lineno, len(cells)))
            continue
        if cells[0] in ("字段", "项"):
            continue
        fields[cells[0]] = (lineno, cells[1])
    for name in REQUIRED_FIELDS:
        if name not in fields:
            res.fail("%s:%d 缺必填项「%s」" % (tag, sec[0] + 1, name))
        elif not fields[name][1]:
            res.fail("%s:%d 必填项「%s」为空" % (tag, fields[name][0], name))

    if "编号" in fields and ("PH-%d" % number) not in fields["编号"][1]:
        res.fail(
            "%s:%d 编号「%s」与目录 PH-%d 不一致"
            % (tag, fields["编号"][0], fields["编号"][1], number)
        )

    # g1-version：version-minor == n
    if "version-minor" in fields:
        lineno, value = fields["version-minor"]
        match = NUMBER_RX.search(value)
        if match is None or int(match.group(0)) != number:
            res.fail(
                "%s:%d g1-version: version-minor 应为 %d，实际「%s」"
                % (tag, lineno, number, value)
            )
        else:
            res.ok("g1-version: %s version-minor=%d" % (dirname, number))

    # 退出判据
    exit_ids = []
    exit_sec = section(lines, "退出判据")
    if exit_sec is None:
        res.fail("%s:1 缺少「退出判据」节" % tag)
    else:
        body = "\n".join(lines[exit_sec[0] : exit_sec[1]])
        if "任务清单每项可独立验收" not in body:
            res.fail(
                "%s:%d 退出判据未显式包含「任务清单每项可独立验收」"
                % (tag, exit_sec[0] + 1)
            )
        if "T-6" not in body:
            res.fail("%s:%d 退出判据未标注「T-6」" % (tag, exit_sec[0] + 1))
        rows = table_rows(lines, exit_sec[0], exit_sec[1])
        header = None
        for lineno, cells in rows:
            if header is None and "ID" in cells:
                header = cells
                continue
            if header is None:
                continue
            if len(cells) < 2:
                res.fail("%s:%d 退出判据行少于 2 列" % (tag, lineno))
                continue
            if EXIT_ID_RX.match(cells[0]):
                exit_ids.append(cells[0])
                if not cells[1] or cells[1] in ("TBD", "待定"):
                    res.fail("%s:%d 退出判据 %s 条件为空或 TBD" % (tag, lineno, cells[0]))
                if len(cells) < 3 or not cells[2]:
                    res.fail("%s:%d 退出判据 %s 缺「判定」列" % (tag, lineno, cells[0]))
            else:
                res.fail("%s:%d 退出判据 ID 非法：%s" % (tag, lineno, cells[0]))
        if len(exit_ids) < 2:
            res.fail("%s:%d 退出判据少于 2 条，无法证明 phase 被切开" % (tag, exit_sec[0] + 1))

    # 任务清单
    task_sec = section(lines, "任务清单")
    if task_sec is None:
        res.fail("%s:1 缺少「任务清单」节" % tag)
        return
    rows = table_rows(lines, task_sec[0], task_sec[1])
    header = None
    covered = {}
    task_count = 0
    for lineno, cells in rows:
        if header is None:
            if "ID" in cells:
                header = cells
            continue
        if len(cells) != len(header):
            res.fail(
                "%s:%d 任务行列数 %d 与表头 %d 不一致"
                % (tag, lineno, len(cells), len(header))
            )
            continue
        item = dict(zip(header, cells))
        task_id = item.get("ID", "")
        match = TASK_ID_RX.match(task_id)
        if not match or int(match.group(1)) != number:
            res.fail("%s:%d 任务 ID「%s」不符合 PH-%d-T<n>" % (tag, lineno, task_id, number))
            continue
        task_count += 1
        for column in REQUIRED_TASK_COLUMNS:
            if column not in header:
                res.fail("%s:%d 任务表缺列「%s」" % (tag, lineno, column))
            elif not item.get(column, ""):
                res.fail("%s:%d 任务 %s 的「%s」为空" % (tag, lineno, task_id, column))
        effort = item.get("effort", "").strip("` ")
        if effort not in ("S", "M"):
            res.fail(
                "%s:%d 任务 %s 的 effort=%r 非法（只允许 S/M，L 必须再拆）"
                % (tag, lineno, task_id, effort)
            )
        commit = item.get("提交", "")
        if commit and not re.search(r"(feat|fix|docs|test|refactor|chore)\(", commit):
            res.fail(
                "%s:%d 任务 %s 的提交未写成 <type>(<scope>): ..." % (tag, lineno, task_id)
            )
        rollback = item.get("回滚", "")
        if rollback and "git revert" not in rollback:
            res.fail("%s:%d 任务 %s 的回滚未写 git revert" % (tag, lineno, task_id))
        verify = item.get("verify", "")
        if verify and ("TBD" in verify or "`" not in verify):
            res.fail("%s:%d 任务 %s 的 verify 缺可执行命令" % (tag, lineno, task_id))
        ids = re.findall(r"E-\d+", item.get("覆盖", ""))
        if not ids:
            res.fail("%s:%d 任务 %s 未标注覆盖的退出判据" % (tag, lineno, task_id))
        elif exit_ids and set(ids) >= set(exit_ids):
            res.fail(
                "%s:%d 任务 %s 覆盖全部退出判据，违反 T-5（phase 未被切开）"
                % (tag, lineno, task_id)
            )
        for exit_id in ids:
            covered.setdefault(exit_id, []).append(task_id)

    if task_count == 0:
        res.fail("%s:%d 任务清单为空" % (tag, task_sec[0] + 1))
    for exit_id in exit_ids:
        if exit_id not in covered:
            res.warn("%s 退出判据 %s 无任务覆盖（收口时需说明由谁验收）" % (tag, exit_id))

    if not res.failed:
        res.ok("%s 必填项/任务四要素/退出判据/T-5 均通过" % dirname)


cards = find_cards()
if not cards:
    res.fail("docs/phases:1 未找到任何 PH-<n>/card.md")
for number, dirname, path in cards:
    check_card(number, dirname, path, read_lines(path))

res.finish()
