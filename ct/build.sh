#!/usr/bin/env bash
# Build the CT-side RILL 0.1.0 entry from a clean checkout.
#
#   ct/build.sh
#
# Requires: the ct-ast mainline `ct` (multi-unit `ct build`, v0.44.1+) and a C
# compiler.  Lookup order for ct: $CT, `ct` on PATH, ~/.local/bin/ct.
# Output: ct/bin/rill
#
# 构建完成后，如果 ~/.local/bin 可写，会把它链成 `rill` 放上 PATH，
# 这样 `#!/usr/bin/env rill` 的 shebang 才找得到解释器。
#
# 两次 `ct build`：ct 前端的「已解析调用点」表全局 1024 条（fill-in 见
# docs/reviews/diff/PH-20.md §3），整套实现一次编译会超表。于是分两层：
#   1. 语言核心（common/lexer/parser/loader/formatter）→ build/librill_core.a
#   2. 宿主与入口（eval/json/exec/host/*/cli/main）→ 链接核心静态库
# 跨层用生成头 `#include` + `-L/-l`，ct 的多单元 import 只在层内使用。
# 多单元切分与理由见 docs/phases/pending/ct-multiunit.md。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/ct/bin/rill"
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

# ct 0.65+ 默认 strict C 边界；本实现用 #include 与内联 C，需显式 allow。
# 第一层：语言核心 -> 静态库（导出头落在 $LIBGEN）
(
    cd "$ROOT/ct"
    "$CT" build \
        src/lexer/lexer.h.ct \
        src/parser/parser.h.ct \
        src/loader/loader.h.ct \
        src/formatter/formatter.h.ct \
        --lib -I src --outdir "$LIBGEN" \
        --c-boundary=allow \
        --cflags "-Wall -Wextra -O2" \
        -o "$LIB"
)

# 第二层：宿主 + 入口，消费第一层的生成头与静态库
(
    cd "$ROOT/ct"
    "$CT" build src/main.ct -I src \
        --outdir "$TMP/gen" \
        --c-boundary=allow \
        --cflags "-Wall -Wextra -O2 -I$LIBGEN -I$ROOT/ct/src/host" \
        --ldflags "$LIB" \
        -o "$OUT"
)
echo "built $OUT"
# 兼容旧名：PH-19/PH-20 的对拍脚本与文档里写的是 ct/bin/rill_ct。
ln -sf rill "$ROOT/ct/bin/rill_ct"

# PATH 入口：shebang 行 `#!/usr/bin/env rill` 需要 PATH 上有 rill。
if [ -d "$HOME/.local/bin" ] && [ -w "$HOME/.local/bin" ]; then
    ln -sf "$OUT" "$HOME/.local/bin/rill"
    echo "linked $HOME/.local/bin/rill -> $OUT"
    case ":$PATH:" in
        *":$HOME/.local/bin:"*) ;;
        *) echo "note: $HOME/.local/bin 不在 PATH，shebang 需要它；请加进 shell 配置" ;;
    esac
fi
