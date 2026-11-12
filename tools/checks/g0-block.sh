#!/usr/bin/env bash
# G0 g0-block：AGENTS.md 生成块与主规范逐字一致。
# 只读：调用 sync-agents.sh --check，不改任何文件。
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AGENTS="$ROOT/AGENTS.md"
SPEC="${AI_ENGINEERING_SPEC:-/Users/samxx/trae-ws/.ai-engineering/methodology/ai-coding-workflow.md}"
SYNC="${AI_ENGINEERING_SYNC:-/Users/samxx/trae-ws/.ai-engineering/bin/sync-agents.sh}"
FAILED=0

if [ ! -f "$AGENTS" ]; then
  echo "FAIL  AGENTS.md:1 文件缺失"
  exit 1
fi

if [ ! -f "$SYNC" ]; then
  echo "FAIL  AGENTS.md:8 无法校验生成块：sync-agents.sh 不存在（$SYNC）"
  exit 1
fi

if [ ! -f "$SPEC" ]; then
  echo "FAIL  AGENTS.md:8 无法校验生成块：主规范不存在（$SPEC）"
  exit 1
fi

OUTPUT="$(bash "$SYNC" --check "$AGENTS" 2>&1)"
RC=$?
if [ "$RC" -ne 0 ]; then
  echo "FAIL  AGENTS.md:8 生成块与主规范不一致（sync-agents.sh --check rc=$RC）"
  printf '%s\n' "$OUTPUT" | sed 's/^/      /'
  FAILED=1
else
  echo "PASS  AGENTS.md:8 生成块与主规范逐字一致"
  printf '%s\n' "$OUTPUT" | sed 's/^/      /'
fi

EXPECTED="$(shasum -a 256 "$SPEC" 2>/dev/null | awk '{print $1}')"
ACTUAL="$(sed -n 's/^<!-- spec:begin version=[0-9.]* sha256=\([0-9a-f]\{64\}\) -->$/\1/p' "$AGENTS" | head -n 1)"
if [ -z "$EXPECTED" ] || [ -z "$ACTUAL" ]; then
  echo "FAIL  AGENTS.md:8 无法提取块头 sha256 或主规范实算摘要"
  FAILED=1
elif [ "$EXPECTED" != "$ACTUAL" ]; then
  echo "FAIL  AGENTS.md:8 块头 sha256=$ACTUAL，主规范实算=$EXPECTED"
  FAILED=1
else
  echo "PASS  AGENTS.md:8 块头 sha256 与主规范实算一致"
fi

echo
echo "check g0-block: $((2 - FAILED)) passed, $FAILED failed, 0 warnings, 0 skipped"
exit "$FAILED"
