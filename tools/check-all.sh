#!/usr/bin/env bash
# 全量门禁 dry-run 入口：等价于 tools/check.sh all。
# 保留独立文件名，对应 AGENTS.md §8 / §12 的「首次全量门禁 dry-run」。
set -uo pipefail
exec "$(cd "$(dirname "$0")" && pwd)/check.sh" all
