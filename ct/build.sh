#!/usr/bin/env bash
# Build the CT-side RILL 0.1.0 entry from a clean checkout.
#
#   ct/build.sh
#
# Requires: a `ctc` binary (CT source-to-source compiler) and a C compiler.
# Lookup order for ctc: $CTC, ../ct-lang/ctc (sibling checkout), then PATH.
# Output: ct/bin/rill-ct
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/ct/bin/rill-ct"

if [ -z "${CTC:-}" ]; then
    for candidate in "$ROOT/../ct-lang/ctc" "$(command -v ctc 2>/dev/null || true)"; do
        if [ -n "$candidate" ] && [ -x "$candidate" ]; then
            CTC="$candidate"
            break
        fi
    done
fi
if [ -z "${CTC:-}" ] || [ ! -x "$CTC" ]; then
    echo "ct/build.sh: ctc not found; set CTC=/path/to/ctc" >&2
    exit 1
fi

TMP="$(mktemp -d "${TMPDIR:-/tmp}/rill-ct.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$(dirname "$OUT")"
"$CTC" "$ROOT/ct/rill_ct.ct" -o "$TMP/rill_ct.c"
"${CC:-cc}" -std=c99 -Wall -Wextra -O2 "$TMP/rill_ct.c" -o "$OUT"
echo "built $OUT"
