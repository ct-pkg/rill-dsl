#!/usr/bin/env bash
# rill-dsl 门禁入口（AGENTS.md §6.4：tools/check.sh g0..g9）。
#
# 当前仓库是纯文档仓库（阶段 0）。只有可离线执行、且此刻不应失败的检查被启用；
# 依赖实现的检查显式标记为 DISABLED（Phase 1+），不计为通过，也不会让 all 变红。
#
# 用法：
#   tools/check.sh g0
#   tools/check.sh g4
#   tools/check.sh all
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CHECKS="$ROOT/tools/checks"
OVERALL=0

run_py() {
  local name="$1"
  printf '\n--- %s ---\n' "$name"
  if ! ROOT="$ROOT" python3 "$CHECKS/$name"; then
    OVERALL=1
  fi
}

run_sh() {
  local name="$1"
  printf '\n--- %s ---\n' "$name"
  if ! ROOT="$ROOT" bash "$CHECKS/$name"; then
    OVERALL=1
  fi
}

disabled() {
  local gate="$1"
  local reason="$2"
  printf '\n--- %s ---\n' "$gate"
  printf 'SKIP  %s: DISABLED（Phase 1 后启用）— %s\n' "$gate" "$reason"
}

g0() {
  run_sh g0-block.sh
  run_py g0_landing.py
  run_py session_map.py
}

g1() {
  run_py spec_index.py
  printf '\nNOTE  g1: PARTIAL — S/T 编号与索引已校验；每条要求的验收命令/阈值与 phase 卡片检查在 Phase 1 后启用（当前统一写“尚未落盘”）\n'
}

g4() {
  run_py doc_size.py
  run_py doc_links.py
  run_py version_wording.py
  run_py snippets.py
  printf '\nNOTE  g4: PARTIAL — snippet 渲染/编译（g4-snippets）与 applies-to 时效检查在 Phase 1 后启用\n'
}

g6() {
  run_py decision_frontmatter.py
  run_py decision_refs.py
  printf '\nNOTE  g6: PARTIAL — Issue 状态词与台账闭合在 Phase 1 后启用（当前 0 条 issue）\n'
}

g9() {
  run_py g9_spec_pin.py
  printf '\nNOTE  g9: PARTIAL — 主规范仓库侧的 sync-agents.sh 校验已由 g0-block 覆盖\n'
}

all() {
  g0
  g1
  g4
  g6
  g9
  disabled g2 "无 ACC-* 条目"
  disabled g3 "无构建、无单测"
  disabled g5 "无测试用例与红证"
  disabled g7 "无源码与依赖锁"
  disabled g8 "无实现提交；提交粒度与红证规则从 Phase 1 起生效"
  printf '\ndisabled: g2 g3 g5 g7 g8（依赖实现或 ACC/测试资产，当前启用必然失败）\n'
}

case "${1:-all}" in
  g0) g0 ;;
  g1) g1 ;;
  g2) disabled g2 "无 ACC-* 条目" ;;
  g3) disabled g3 "无构建、无单测" ;;
  g4) g4 ;;
  g5) disabled g5 "无测试用例与红证" ;;
  g6) g6 ;;
  g7) disabled g7 "无源码与依赖锁" ;;
  g8) disabled g8 "无实现提交" ;;
  g9) g9 ;;
  all) all ;;
  *)
    echo "用法: $0 {g0|g1|...|g9|all}" >&2
    exit 2
    ;;
esac

printf '\n== overall: %s ==\n' "$([ "$OVERALL" -eq 0 ] && echo PASS || echo FAIL)"
exit "$OVERALL"
