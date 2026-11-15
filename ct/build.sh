#!/usr/bin/env bash
# Build the CT-side RILL 0.1.0 entry from a clean checkout.
#
#   ct/build.sh
#
# Requires: the ct-ast mainline `ct` (multi-unit `ct build`, v0.44.1+) and a C
# compiler.  Lookup order for ct: $CT, `ct` on PATH, ~/.local/bin/ct.
# Output: ct/bin/rill_ct
#
# 多单元切分与理由见 docs/phases/pending/ct-multiunit.md。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/ct/bin/rill_ct"

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

mkdir -p "$(dirname "$OUT")"
(
    cd "$ROOT/ct"
    "$CT" build src/main.ct -I src \
        --outdir "$TMP/gen" \
        --cflags "-Wall -Wextra -O2" \
        -o "$OUT"
)
echo "built $OUT"
