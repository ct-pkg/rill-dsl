#!/usr/bin/env bash
# RILL 0.1.0 门禁入口（Phase 0 基座）。
#
# 用法：
#   tools/check-0.1.0.sh                # 跑全部可运行用例
#   tools/check-0.1.0.sh --all          # 全样例门禁：pending=0 且任何非 PASS 都失败
#   tools/check-0.1.0.sh --list         # 列出用例与资产
#   tools/check-0.1.0.sh --check-fakes  # 校验 profile 与 fake 资产
#   tools/check-0.1.0.sh --show <case>  # 查看某个用例的被测输出
#
# 退出码：0 全过；1 有失败或用例不合法；3 用例仍需实现或 golden（not implemented）。
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$ROOT/tools/rill_harness/cli.py" --repo-root "$ROOT" "$@"
