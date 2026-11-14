"""G8 g8-phase-freeze：首个实现提交后，退出判据与任务清单不可改。

做法：对每张卡片取 git 历史；找到第一条 subject 为 feat/fix 且含 `PH-<n>` 的提交作为
首个实现提交；把该提交的父提交里的卡片作为冻结基线，与工作树逐字比对
`exit-criteria`（退出判据）与 `tasks`（任务清单）两节。

- 卡片尚未提交（如事后补记阶段）→ SKIP，不伪造通过；
- 没有实现提交 → SKIP（尚未进入冻结窗口）；
- 卡片在首个实现提交时才加入 → FAIL（无法冻结）。

勘误白名单（`tools/checks/phase-freeze-errata.json`）只放行“能逐条对上”的整行替换：
phase / file / section / 旧行哈希 / 新行哈希 / 收口锚点全部匹配才放行。匹配不上、哈希
不一致、锚点缺失、条目未生效（名单腐烂）一律 FAIL。

用法：
  python3 tools/checks/g8_phase_freeze.py               # 门禁检查（含自测）
  python3 tools/checks/g8_phase_freeze.py --self-test   # 只跑白名单负例
  python3 tools/checks/g8_phase_freeze.py --list-errata # 列出当前生效勘误
"""

import difflib
import hashlib
import json
import os
import re
import subprocess
import sys

from common import ROOT, Result, read_lines

ERRATA_REL = "tools/checks/phase-freeze-errata.json"
ERRATA_PATH = os.path.join(ROOT, ERRATA_REL)
ERRATA_SCHEMA = "phase-freeze-errata/1"
FROZEN_SECTIONS = ("退出判据", "任务清单")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
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


def extract_section_lines(text, keyword):
    """返回 (section 行列表, 起始下标 0 基)；找不到章节返回 (None, None)。"""
    lines = text.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if line.startswith("## ") and keyword in line:
            start = idx
            break
    if start is None:
        return None, None
    end = len(lines)
    for idx in range(start + 1, len(lines)):
        if lines[idx].startswith("## "):
            end = idx
            break
    return [line.rstrip() for line in lines[start:end]], start


def heading_line(lines, keyword):
    for idx, line in enumerate(lines):
        if line.startswith("## ") and keyword in line:
            return idx + 1
    return 1


def line_hash(text):
    return hashlib.sha256(text.rstrip().encode("utf-8")).hexdigest()


def changed_line_pairs(frozen_lines, current_lines, current_start):
    """只接受等长整行替换；增删行、行数不等的替换都算失败。"""
    matcher = difflib.SequenceMatcher(a=frozen_lines, b=current_lines, autojunk=False)
    pairs = []
    problems = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag != "replace":
            problems.append(
                "仅允许整行替换，检测到 %s（冻结 %d 行 → 当前 %d 行）"
                % (tag, i2 - i1, j2 - j1)
            )
            continue
        if (i2 - i1) != (j2 - j1):
            problems.append(
                "替换段行数不一致（%d → %d），不能逐条对白名单" % (i2 - i1, j2 - j1)
            )
            continue
        for offset in range(i2 - i1):
            pairs.append(
                (
                    frozen_lines[i1 + offset],
                    current_lines[j1 + offset],
                    current_start + 1 + j1 + offset,
                )
            )
    return pairs, problems


def apply_errata(pairs, entries, phase, filerel, section):
    """返回 (命中的条目 id 集合, [(行号, 错误)])。"""
    consumed = set()
    errors = []
    for old, new, lineno in pairs:
        old_sha = line_hash(old)
        new_sha = line_hash(new)
        candidates = [
            entry
            for entry in entries
            if entry["phase"] == phase
            and entry["file"] == filerel
            and entry["section"] == section
            and entry["old_sha256"] == old_sha
            and entry["new_sha256"] == new_sha
        ]
        if len(candidates) == 1:
            consumed.add(candidates[0]["id"])
        elif not candidates:
            errors.append(
                (
                    lineno,
                    "未登记的修改（old=%s new=%s）" % (old_sha[:12], new_sha[:12]),
                )
            )
        else:
            errors.append(
                (
                    lineno,
                    "同一条修改命中多条白名单：%s"
                    % ", ".join(entry["id"] for entry in candidates),
                )
            )
    return consumed, errors


def stale_entries(entries, consumed):
    return [entry["id"] for entry in entries if entry["id"] not in consumed]


def load_errata():
    if not os.path.isfile(ERRATA_PATH):
        res.fail("%s:1 白名单文件不存在" % ERRATA_REL)
        return []
    try:
        with open(ERRATA_PATH, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        res.fail("%s:1 无法解析：%s" % (ERRATA_REL, exc))
        return []
    if not isinstance(doc, dict) or doc.get("schema") != ERRATA_SCHEMA:
        res.fail("%s:1 schema 必须是 %s" % (ERRATA_REL, ERRATA_SCHEMA))
        return []
    raw = doc.get("entries")
    if not isinstance(raw, list):
        res.fail("%s:1 entries 必须是数组" % ERRATA_REL)
        return []

    cards = {dirname: path for _, dirname, path in find_cards()}
    entries = []
    seen_ids = set()
    seen_fingerprints = set()
    required = (
        "id",
        "phase",
        "file",
        "section",
        "line",
        "old_sha256",
        "new_sha256",
        "closeout",
        "date",
        "reason",
    )
    for idx, item in enumerate(raw):
        prefix = "%s:1 白名单第 %d 条" % (ERRATA_REL, idx + 1)
        problems = []
        if not isinstance(item, dict):
            res.fail("%s 必须是对象" % prefix)
            continue
        missing = [key for key in required if key not in item]
        if missing:
            res.fail("%s 缺少字段 %s" % (prefix, ", ".join(missing)))
            continue

        entry_id = item.get("id")
        if not isinstance(entry_id, str) or not entry_id.strip():
            problems.append("id 必须是非空字符串")
        elif entry_id in seen_ids:
            problems.append("id 重复：%s" % entry_id)

        phase = item.get("phase")
        if phase not in cards:
            problems.append("phase %r 没有对应卡片" % phase)
        file_rel = item.get("file")
        expected_file = "docs/phases/%s/card.md" % phase
        if file_rel != expected_file:
            problems.append("file 必须是 %s" % expected_file)

        section = item.get("section")
        if section not in FROZEN_SECTIONS:
            problems.append("section 必须是 %s 之一" % " / ".join(FROZEN_SECTIONS))

        lineno = item.get("line")
        if not isinstance(lineno, int) or lineno < 1:
            problems.append("line 必须是正整数")

        for key in ("old_sha256", "new_sha256"):
            value = item.get(key)
            if not isinstance(value, str) or not HASH_RE.match(value):
                problems.append("%s 必须是 64 位小写 sha256" % key)

        date = item.get("date")
        if not isinstance(date, str) or not DATE_RE.match(date):
            problems.append("date 必须是 YYYY-MM-DD")

        reason = item.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            problems.append("reason 必须是非空字符串")

        closeout = item.get("closeout")
        if not isinstance(closeout, dict) or any(
            key not in closeout for key in ("file", "section", "must_contain")
        ):
            problems.append("closeout 必须包含 file / section / must_contain")
        else:
            anchor = os.path.join(ROOT, closeout["file"])
            if not os.path.isfile(anchor):
                problems.append("收口锚点文件不存在：%s" % closeout["file"])
            else:
                with open(anchor, encoding="utf-8") as fh:
                    anchor_text = fh.read()
                anchor_lines, _ = extract_section_lines(anchor_text, closeout["section"])
                if anchor_lines is None:
                    problems.append(
                        "收口锚点章节不存在：%s#%s"
                        % (closeout["file"], closeout["section"])
                    )
                elif closeout["must_contain"] not in "\n".join(anchor_lines):
                    problems.append(
                        "收口锚点章节缺少标记 %r" % closeout["must_contain"]
                    )

        if file_rel == expected_file:
            card_path = os.path.join(ROOT, expected_file)
            if os.path.isfile(card_path):
                card_lines = read_lines(card_path)
                if isinstance(lineno, int) and 1 <= lineno <= len(card_lines):
                    if line_hash(card_lines[lineno - 1]) != item.get("new_sha256"):
                        problems.append(
                            "line %d 的内容与新哈希不一致（行号过期或条目被篡改）"
                            % lineno
                        )
                else:
                    problems.append(
                        "line %s 超出 %s 的行数 %d"
                        % (lineno, expected_file, len(card_lines))
                    )
                section_lines, section_start = extract_section_lines(
                    "\n".join(card_lines), section
                )
                if section_lines is None:
                    problems.append("卡片缺少「%s」节" % section)
                elif isinstance(lineno, int) and not (
                    section_start + 1 <= lineno <= section_start + len(section_lines)
                ):
                    problems.append("line %d 不在「%s」节内" % (lineno, section))

        if problems:
            for problem in problems:
                res.fail("%s：%s" % (prefix, problem))
            continue

        fingerprint = (
            item["phase"],
            item["file"],
            item["section"],
            item["old_sha256"],
            item["new_sha256"],
        )
        if fingerprint in seen_fingerprints:
            res.fail("%s：与前面的条目重复" % prefix)
            continue
        seen_ids.add(item["id"])
        seen_fingerprints.add(fingerprint)
        entries.append(item)
    return entries


def self_test():
    """白名单负例：合法放行、篡改新行、伪造旧行、增删行、条目失效、锚点缺失。"""

    def expect(name, condition, detail=""):
        if condition:
            res.ok("self-test %s" % name)
        else:
            res.fail("self-test %s%s" % (name, "：" + detail if detail else ""))

    old = "| PH-X-T1 | 旧命令 |"
    new = "| PH-X-T1 | 新命令 |"
    entry = {
        "id": "SELFTEST",
        "phase": "PH-99",
        "file": "docs/phases/PH-99/card.md",
        "section": "任务清单",
        "line": 1,
        "old_sha256": line_hash(old),
        "new_sha256": line_hash(new),
    }
    args = ("PH-99", entry["file"], entry["section"])

    consumed, errors = apply_errata([(old, new, 1)], [entry], *args)
    expect(
        "合法勘误逐条放行",
        consumed == {"SELFTEST"} and not errors,
        "consumed=%s errors=%s" % (consumed, errors),
    )

    consumed, errors = apply_errata([(old, new + "（篡改）", 1)], [entry], *args)
    expect(
        "篡改新行未更新哈希必须报红",
        not consumed and len(errors) == 1,
        "consumed=%s errors=%s" % (consumed, errors),
    )

    consumed, errors = apply_errata([(old + "（伪造）", new, 1)], [entry], *args)
    expect(
        "伪造旧行必须报红",
        not consumed and len(errors) == 1,
        "consumed=%s errors=%s" % (consumed, errors),
    )

    pairs, problems = changed_line_pairs(["a", "b"], ["a", "x", "b"], 0)
    expect(
        "插入/删除行必须报红",
        not pairs and len(problems) == 1,
        "pairs=%s problems=%s" % (pairs, problems),
    )

    expect(
        "未生效的白名单条目必须报红",
        stale_entries([entry], set()) == ["SELFTEST"],
    )

    anchor_text = "## 3. 任务 verify\n\n2026-11-15 勘误：命令已改。\n"
    anchor_lines, _ = extract_section_lines(anchor_text, "3. 任务 verify")
    expect(
        "收口锚点可解析",
        anchor_lines is not None and "勘误" in "\n".join(anchor_lines),
    )
    missing_lines, _ = extract_section_lines(anchor_text, "不存在的章节")
    expect("收口锚点缺失必须报错", missing_lines is None)


def list_errata():
    entries = load_errata()
    if res.failed:
        res.finish()
    print("%-36s %-7s %-42s %-6s %s" % ("ID", "PHASE", "FILE:LINE", "STATUS", "REASON"))
    for entry in entries:
        card_lines = read_lines(os.path.join(ROOT, entry["file"]))
        applied = (
            1 <= entry["line"] <= len(card_lines)
            and line_hash(card_lines[entry["line"] - 1]) == entry["new_sha256"]
        )
        print(
            "%-36s %-7s %-42s %-6s %s"
            % (
                entry["id"],
                entry["phase"],
                "%s:%d" % (entry["file"], entry["line"]),
                "APPLIED" if applied else "STALE",
                entry["reason"],
            )
        )
        if not applied:
            res.fail("%s:1 白名单条目 %s 已失效" % (ERRATA_REL, entry["id"]))
    res.ok("errata: %d 条生效" % len(entries))
    res.finish()


def run_checks():
    entries = load_errata()
    consumed = set()
    history = git(["log", "--reverse", "--format=%H%x09%s"])
    if history.returncode != 0:
        res.fail("git log 失败：%s" % history.stderr.strip())
        res.finish()
    commits = [
        line.split("\t", 1) for line in history.stdout.splitlines() if line.strip()
    ]

    for number, dirname, path in find_cards():
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
        current_lines_all = read_lines(path)
        changed = False
        for keyword in FROZEN_SECTIONS:
            frozen_lines, _ = extract_section_lines(frozen_raw.stdout, keyword)
            current_lines, current_start = extract_section_lines(current_text, keyword)
            if frozen_lines is None:
                res.fail("%s:1 冻结基线缺「%s」节，判据不完整" % (relpath, keyword))
                changed = True
                continue
            if current_lines is None:
                res.fail("%s:1 当前卡片缺「%s」节" % (relpath, keyword))
                changed = True
                continue
            if frozen_lines == current_lines:
                continue

            changed = True
            pairs, problems = changed_line_pairs(
                frozen_lines, current_lines, current_start
            )
            for problem in problems:
                res.fail(
                    "%s:%d 「%s」%s"
                    % (relpath, heading_line(current_lines_all, keyword), keyword, problem)
                )
            matched, errors = apply_errata(
                pairs, entries, dirname, relpath, keyword
            )
            consumed |= matched
            for lineno, message in errors:
                res.fail("%s:%d 「%s」%s" % (relpath, lineno, keyword, message))
            for entry_id in sorted(matched):
                res.ok("%s 「%s」勘误放行：%s" % (relpath, keyword, entry_id))

        if not changed:
            res.ok("%s 的退出判据与任务清单自 %s 起未变" % (relpath, impl[0][:7]))

    for entry_id in sorted(stale_entries(entries, consumed)):
        res.fail(
            "%s:1 白名单条目 %s 未生效（对应行不存在或哈希对不上）"
            % (ERRATA_REL, entry_id)
        )
    if entries:
        res.ok("errata: %d 条生效" % len(consumed))
    self_test()
    res.finish()


if "--list-errata" in sys.argv:
    list_errata()
elif "--self-test" in sys.argv:
    self_test()
    res.finish()
else:
    run_checks()
