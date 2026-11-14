"""G8 g8-version：版本号规则与 phase tag。

检查项（主规范 §6.7 V-1…V-7 的可机械部分）：
- 每个 v* tag：名符合 v<MAJOR>.<MINOR>.<PATCH>；annotated；message 含 PH-<n> 且 MINOR=n；
  phase tag 的 PATCH=0；指向提交是 HEAD 祖先；
- AGENTS.md「版本落点」已声明时：各落点版本一致；tag 版本等于落点版本；
- 落点写「缺失/未建」或无 tag 时只提示，不伪造通过。

未覆盖（收口对照表人工核）：V-2/V-3/V-4/V-5 的提交级 PATCH 计数与同提交落点。
"""

import os
import re
import subprocess

from common import ROOT, Result, read_lines, rel

TAG_RX = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
VERSION_RX = re.compile(r"\d+\.\d+\.\d+")
res = Result("g8-version")


def git(args):
    return subprocess.run(
        ["git", "-C", ROOT] + args, capture_output=True, text=True
    )


probe = git(["rev-parse", "--show-toplevel"])
if probe.returncode != 0:
    res.skip("当前 ROOT 不是 git 仓库：%s" % ROOT)
    res.finish()

tags = []
listing = git(["tag", "-l"])
if listing.returncode == 0:
    tags = [line.strip() for line in listing.stdout.splitlines() if line.strip()]

tag_versions = set()
for tag in sorted(tags):
    match = TAG_RX.match(tag)
    if match is None:
        res.fail(
            "tag %s:1 名称不符合 v<MAJOR>.<MINOR>.<PATCH>（fix 不打 tag）" % tag
        )
        continue
    tag_failed = False
    major, minor, patch = (int(part) for part in match.groups())
    kind = git(["cat-file", "-t", tag])
    annotated = kind.returncode == 0 and kind.stdout.strip() == "tag"
    if not annotated:
        res.fail("tag %s:1 不是 annotated tag（git cat-file -t != tag）" % tag)
        tag_failed = True
    contents = git(["for-each-ref", "--format=%(contents)", "refs/tags/" + tag])
    message = contents.stdout if contents.returncode == 0 else ""
    phase = re.search(r"PH-(\d+)", message)
    if phase is None:
        res.fail("tag %s:1 message 未含 PH-<n>" % tag)
        tag_failed = True
    elif int(phase.group(1)) != minor:
        res.fail(
            "tag %s:1 MINOR=%d 与 message 里的 PH-%s 不对应"
            % (tag, minor, phase.group(1))
        )
        tag_failed = True
    if patch != 0:
        res.fail("tag %s:1 phase tag 的 PATCH 必须为 0，实际 %d" % (tag, patch))
        tag_failed = True
    target = git(["rev-parse", tag + "^{commit}"])
    sha = target.stdout.strip() if target.returncode == 0 else ""
    if not sha:
        res.fail("tag %s:1 无法解析指向提交" % tag)
        tag_failed = True
    else:
        ancestor = subprocess.run(
            ["git", "-C", ROOT, "merge-base", "--is-ancestor", sha, "HEAD"]
        )
        if ancestor.returncode != 0:
            res.fail("tag %s:1 指向提交 %s 不是 HEAD 祖先" % (tag, sha[:7]))
            tag_failed = True
    if not tag_failed:
        res.ok("tag %s：annotated、PH-%d、指向 %s 且可追溯" % (tag, minor, sha[:7]))
    tag_versions.add((major, minor, patch))

# 版本落点
agents = os.path.join(ROOT, "AGENTS.md")
landing = None
if os.path.isfile(agents):
    for lineno, line in enumerate(read_lines(agents), 1):
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] == "版本落点":
            landing = (lineno, cells[1])
            break

declared = set()
if landing is None:
    res.warn("AGENTS.md 未声明的「版本落点」行（6.7：未声明即 G0 失败，本检查不代判）")
elif any(hint in landing[1] for hint in ("缺失", "未建", "未定")):
    res.warn(
        "AGENTS.md:%d 版本落点仍为「%s」；落点声明前只校验 tag，不校验落点一致性"
        % (landing[0], landing[1])
    )
else:
    locations = re.findall(r"`([^`]+)`", landing[1])
    if not locations:
        res.warn("AGENTS.md:%d 版本落点未用反引号给出可解析路径：%s" % (landing[0], landing[1]))
    for spec in locations:
        path_part, _, pattern = spec.partition("#")
        target_path = os.path.join(ROOT, path_part)
        if not os.path.isfile(target_path):
            res.fail("版本落点 %s 不存在（%s）" % (path_part, rel(target_path)))
            continue
        text = "\n".join(read_lines(target_path))
        if pattern and "\\d" in pattern:
            versions = re.findall(pattern, text)
        elif pattern:
            rx = r"[\"']?%s[\"']?\s*[:=]\s*[\"']?(\d+\.\d+\.\d+)" % re.escape(pattern)
            versions = re.findall(rx, text)
        else:
            versions = VERSION_RX.findall(text)
        unique = sorted(set(versions))
        if len(unique) != 1:
            res.fail(
                "版本落点 %s 解析到 %d 个版本 %s，无法确定当前版本"
                % (path_part, len(unique), unique)
            )
            continue
        declared.add(unique[0])
    if len(declared) > 1:
        res.fail("版本落点之间不一致：%s" % "、".join(sorted(declared)))
    elif declared:
        res.ok("版本落点一致：%s" % sorted(declared)[0])

    if declared and tag_versions:
        tag_text = {"%d.%d.%d" % item for item in tag_versions}
        missing = tag_text - declared
        if missing:
            res.fail(
                "tag 版本 %s 与版本落点 %s 不一致"
                % ("、".join(sorted(missing)), "、".join(sorted(declared)))
            )

if not tags:
    res.skip("仓库当前 0 个 tag；phase 收口前无 tag 可校验（V-7 只在收口时生效）")

res.finish()
