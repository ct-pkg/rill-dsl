#!/usr/bin/env bash
# RILL 0.1.0 格式化门禁入口。
#
# 用法：
#   tools/check-fmt.sh --roundtrip   # compress -> display -> compress 的 AST 等价
#
# 退出码：0 通过；1 失败；2 用法错误。
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

case "${1:-}" in
  --roundtrip)
    exec python3 "$ROOT/tests/phase12/test_roundtrip.py"
    ;;
  *)
    echo "用法: $0 --roundtrip" >&2
    exit 2
    ;;
esac
