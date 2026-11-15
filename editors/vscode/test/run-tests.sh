#!/usr/bin/env bash
# 运行插件自测：优先用 node；没有 node 时退到 Electron 的 Node 模式。
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"

if [ -n "${RILL_NODE:-}" ]; then
  exec "$RILL_NODE" "$HERE/run-tests.js"
fi

if command -v node >/dev/null 2>&1; then
  exec node "$HERE/run-tests.js"
fi

ELECTRON="/Applications/Trae CN.app/Contents/MacOS/Electron"
if [ -x "$ELECTRON" ]; then
  export ELECTRON_RUN_AS_NODE=1
  exec "$ELECTRON" "$HERE/run-tests.js"
fi

echo "未找到 node，也未找到可用的 Electron；请设置 RILL_NODE 指向 node 可执行文件" >&2
exit 127
