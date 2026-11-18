"""G8 g8-version：版本号规则与 phase tag。

检查项（主规范 §6.7 V-1…V-7 的可机械部分）：
- 每个 v* tag：名符合 v<MAJOR>.<MINOR>.<PATCH>；annotated；message 含 PH-<n> 且 MINOR=n；
  phase tag 的 PATCH=0；指向提交是 HEAD 祖先；
- AGENTS.md「版本落点」已声明时：各落点版本一致；tag 版本不得高于落点版本，
  落点版本本身应有对应 tag（tag 常在收口提交之后打，缺失时只提示）。
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


def check_target(tag):
    """返回 tag 指向的 commit sha；失败时已记 FAIL 并返回 None。"""
    target = git(["rev-parse", tag + "^{commit}"])
    sha = target.stdout.strip() if target.returncode == 0 else ""
    if not sha:
        res.fail("tag %s:1 无法解析指向提交" % tag)
        return None
    ancestor = subprocess.run(
        ["git", "-C", ROOT, "merge-base", "--is-ancestor", sha, "HEAD"]
    )
    if ancestor.returncode != 0:
        res.fail("tag %s:1 指向提交 %s 不是 HEAD 祖先" % (tag, sha[:7]))
        return None
    return sha


def read_pkg(tag):
    """读 tag 根下的 ct.pkg；不存在返回 None。"""
    show = git(["show", tag + ":ct.pkg"])
    if show.returncode != 0:
        return None
    data = {}
    for line in show.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        data[key.strip()] = value.strip()
    return data


PKG_MSG_RX = re.compile(r"^(\S+)\s+(\d+\.\d+\.\d+)$")


def check_package_tag(tag, version, message, annotated):
    """识别并校验 CT 包 tag；返回 (是否包 tag, 是否通过)。

    包 tag 形态：message 恰为 `<包名> <version>`，且 tag 内 ct.pkg 的
    name/version/publisher/ns-root 与 tag 自洽。不是包 tag 时返回
    (False, False)，由调用方按 phase tag 处理。
    """
    match = PKG_MSG_RX.match(message.strip())
    if match is None:
        return False, False
    name, msg_version = match.group(1), match.group(2)
    ok = annotated
    if msg_version != version:
        res.fail(
            "tag %s:1 包 tag message 版本 %s 与 tag 名 %s 不一致"
            % (tag, msg_version, version)
        )
        ok = False
    pkg = read_pkg(tag)
    if pkg is None:
        res.fail("tag %s:1 包 tag 缺 ct.pkg" % tag)
        ok = False
    else:
        if pkg.get("name") != name:
            res.fail(
                "tag %s:1 包 tag 名 %s 与 ct.pkg name=%r 不一致"
                % (tag, name, pkg.get("name"))
            )
            ok = False
        if pkg.get("version") != version:
            res.fail(
                "tag %s:1 包 tag 版本 %s 与 ct.pkg version=%r 不一致"
                % (tag, version, pkg.get("version"))
            )
            ok = False
        publisher = pkg.get("publisher", "")
        if not publisher or publisher == "local" or "/" in publisher:
            res.fail(
                "tag %s:1 ct.pkg publisher=%r 非法（非空、非 local、不含 /）"
                % (tag, publisher)
            )
            ok = False
        ns_root = pkg.get("ns-root", "")
        if not ns_root or ns_root.startswith("/") or ".." in ns_root.split("/"):
            res.fail(
                "tag %s:1 ct.pkg ns-root=%r 非法（相对路径、不含 ..）"
                % (tag, ns_root)
            )
            ok = False
        else:
            spec = tag + "^{tree}" if ns_root == "." else tag + ":" + ns_root
            tree = git(["cat-file", "-t", spec])
            if tree.returncode != 0 or tree.stdout.strip() != "tree":
                res.fail(
                    "tag %s:1 ct.pkg ns-root=%r 在 tag 内不是目录"
                    % (tag, ns_root)
                )
                ok = False
    sha = check_target(tag)
    if sha is None:
        ok = False
    if ok:
        res.ok(
            "tag %s：包 tag %s %s、ct.pkg 一致、指向 %s 且可追溯"
            % (tag, name, version, sha[:7])
        )
    return True, ok


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
    version = "%d.%d.%d" % (major, minor, patch)
    kind = git(["cat-file", "-t", tag])
    annotated = kind.returncode == 0 and kind.stdout.strip() == "tag"
    if not annotated:
        res.fail("tag %s:1 不是 annotated tag（git cat-file -t != tag）" % tag)
        tag_failed = True
    contents = git(["for-each-ref", "--format=%(contents)", "refs/tags/" + tag])
    message = contents.stdout if contents.returncode == 0 else ""
    phase = re.search(r"PH-(\d+)", message)
    if phase is None:
        is_package, _package_ok = check_package_tag(tag, version, message, annotated)
        if is_package:
            continue
        res.fail(
            "tag %s:1 message 未含 PH-<n>，也不符合包 tag '<name> <version>'" % tag
        )
        tag_failed = True
    else:
        if int(phase.group(1)) != minor:
            res.fail(
                "tag %s:1 MINOR=%d 与 message 里的 PH-%s 不对应"
                % (tag, minor, phase.group(1))
            )
            tag_failed = True
        if patch != 0:
            res.fail("tag %s:1 phase tag 的 PATCH 必须为 0，实际 %d" % (tag, patch))
            tag_failed = True
        sha = check_target(tag)
        if sha is None:
            tag_failed = True
        if not tag_failed:
            res.ok(
                "tag %s：annotated、PH-%d、指向 %s 且可追溯"
                % (tag, minor, sha[:7])
            )
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
        current = sorted(declared)[0]
        current_key = tuple(int(part) for part in current.split("."))
        future = [
            value for value in tag_text
            if tuple(int(part) for part in value.split(".")) > current_key
        ]
        if future:
            res.fail(
                "tag 版本 %s 高于版本落点 %s"
                % ("、".join(sorted(future)), current)
            )
        if current not in tag_text:
            res.warn(
                "版本落点 %s 尚无对应 tag；收口提交后应打 annotated tag 并推送"
                % current
            )

if not tags:
    res.skip("仓库当前 0 个 tag；phase 收口前无 tag 可校验（V-7 只在收口时生效）")

res.finish()
