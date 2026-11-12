"""G9（可离线部分）：AGENTS.md 生成块头 version/sha256 与主规范一致且不落后。

完整 G9 还需要主规范仓库的 sync-agents.sh；本检查只做块头与主规范的比对。
主规范缺失时 SKIP，不伪造通过。
"""

import hashlib
import os
import re

from common import ROOT, Result, read_lines, rel

DEFAULT_SPEC = "/Users/samxx/trae-ws/.ai-engineering/methodology/ai-coding-workflow.md"

res = Result("g9-spec-pin")

spec_path = os.environ.get("AI_ENGINEERING_SPEC", DEFAULT_SPEC)
agents_path = os.path.join(ROOT, "AGENTS.md")

if not os.path.isfile(spec_path):
    res.skip("主规范不存在：%s（设置 AI_ENGINEERING_SPEC 后重跑）" % spec_path)
    res.finish()

if not os.path.isfile(agents_path):
    res.fail("AGENTS.md:1 文件缺失")
    res.finish()

header_rx = re.compile(r"^<!-- spec:begin version=(\d+\.\d+\.\d+) sha256=([0-9a-f]{64}) -->$")
header = None
for lineno, line in enumerate(read_lines(agents_path), 1):
    match = header_rx.match(line)
    if match:
        header = (lineno, match.group(1), match.group(2))
        break

if header is None:
    res.fail("AGENTS.md:1 未找到未转义的 spec:begin 块头（version + sha256）")
    res.finish()

spec_version = None
for line in read_lines(spec_path):
    match = re.search(r"spec-version\s*\|\s*`?(\d+\.\d+\.\d+)`?", line)
    if match:
        spec_version = match.group(1)
        break

if spec_version is None:
    res.fail("%s:1 主规范未声明 spec-version" % rel(spec_path))
    res.finish()

with open(spec_path, "rb") as fh:
    digest = hashlib.sha256(fh.read()).hexdigest()

if header[2] != digest:
    res.fail(
        "AGENTS.md:%d 块头 sha256=%s，主规范实算=%s"
        % (header[0], header[2], digest)
    )

if tuple(int(x) for x in header[1].split(".")) < tuple(int(x) for x in spec_version.split(".")):
    res.fail(
        "AGENTS.md:%d 块头 version=%s 落后于主规范 %s"
        % (header[0], header[1], spec_version)
    )

if not res.failed:
    res.ok("块头 version=%s 与主规范一致，sha256 与实算一致" % header[1])

res.finish()
