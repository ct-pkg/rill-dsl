#!/usr/bin/env bash
# Build the CT-side RILL 0.1.0 entry from a clean checkout.
#
#   ct/build.sh
#
# Requires: the ct-ast mainline `ct` (multi-unit `ct build`, v0.44.1+) and a C
# compiler.  Lookup order for ct: $CT, `ct` on PATH, ~/.local/bin/ct.
# Output: ct/bin/rill_ct
#
# 两次 `ct build`：ct 前端的「已解析调用点」表全局 1024 条（fill-in 见
# docs/reviews/diff/PH-20.md §3），整套实现一次编译会超表。于是分两层：
#   1. 语言核心（common/lexer/parser/loader/formatter）→ build/librill_core.a
#   2. 宿主与入口（eval/json/exec/host/*/cli/main）→ 链接核心静态库
# 跨层用生成头 `#include` + `-L/-l`，ct 的多单元 import 只在层内使用。
# 多单元切分与理由见 docs/phases/pending/ct-multiunit.md。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/ct/bin/rill_ct"
BUILD="$ROOT/ct/build"
LIBGEN="$BUILD/gen-lib"
LIB="$BUILD/librill_core.a"

if [ -z "${CT:-}" ]; then
    if command -v ct >/dev/null 2>&1; then
        CT="$(command -v ct)"
    elif [ -x "$HOME/.local/bin/ct" ]; then
        CT="$HOME/.local/bin/ct"
    fi
fi
if [ -z "${CT:-}" ] || [ ! -x "$CT" ]; then
    echo "ct/build.sh: ct-ast mainline 'ct' not found; set CT=/path/to/ct" >&2
    exit 1
fi

TMP="$(mktemp -d "${TMPDIR:-/tmp}/rill-ct.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$(dirname "$OUT")" "$BUILD"
rm -rf "$LIBGEN"
mkdir -p "$LIBGEN"

# 第一层：语言核心 -> 静态库（导出头落在 $LIBGEN）
(
    cd "$ROOT/ct"
    "$CT" build \
        src/lexer/lexer.h.ct \
        src/parser/parser.h.ct \
        src/loader/loader.h.ct \
        src/formatter/formatter.h.ct \
        --lib -I src --outdir "$LIBGEN" \
        --cflags "-Wall -Wextra -O2" \
        -o "$LIB"
)

# 第二层：宿主 + 入口，消费第一层的生成头与静态库
(
    cd "$ROOT/ct"
    "$CT" build src/main.ct -I src \
        --outdir "$TMP/gen" \
        --cflags "-Wall -Wextra -O2 -I$LIBGEN -I$ROOT/ct/src/host" \
        --ldflags "$LIB" \
        -o "$OUT"
)
echo "built $OUT"
