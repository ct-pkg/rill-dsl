#!/usr/bin/env bash
# 运行插件自测：优先用 node；没有 node 时退到 Electron 的 Node 模式。
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"

NODE_BIN="${RILL_NODE:-}"
if [ -z "$NODE_BIN" ]; then
  if command -v node >/dev/null 2>&1; then
    NODE_BIN="$(command -v node)"
  else
    ELECTRON="/Applications/Trae CN.app/Contents/MacOS/Electron"
    if [ -x "$ELECTRON" ]; then
      export ELECTRON_RUN_AS_NODE=1
      NODE_BIN="$ELECTRON"
    else
      echo "未找到 node，也未找到可用的 Electron；请设置 RILL_NODE 指向 node 可执行文件" >&2
      exit 127
    fi
  fi
fi

"$NODE_BIN" "$HERE/run-tests.js" || exit $?

"$NODE_BIN" "$HERE/scope-dump.js"
SCOPE_RC=$?
if [ "$SCOPE_RC" -eq 2 ]; then
  echo "scope dump: SKIP（未找到 vscode-textmate/vscode-oniguruma）"
  exit 0
fi
exit "$SCOPE_RC"
