#!/usr/bin/env bash
# Run the first-layer fixtures through the CT entry.
#
#   ct/test.sh              # uses ct/bin/rill_ct
#   ct/test.sh /path/to/bin # uses an explicit binary
#
# Covers: positive/tokens (12), positive/ast (23), negative/tokenize +
# negative/parse errors (19).  The Python reference and the goldens are left
# untouched; the harness compares the CT output against them.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${1:-$ROOT/ct/bin/rill_ct}"

if [ ! -x "$BIN" ]; then
    echo "ct/test.sh: $BIN is missing or not executable; run ct/build.sh first" >&2
    exit 2
fi

rc=0
run() {
    echo ""
    echo "== $*"
    "$@" || rc=1
}

run python3 "$ROOT/tools/rill_harness/cli.py" --repo-root "$ROOT" \
    --sut "$BIN" --bucket positive --kind tokens
run python3 "$ROOT/tools/rill_harness/cli.py" --repo-root "$ROOT" \
    --sut "$BIN" --bucket positive --kind ast

args=()
for d in "$ROOT"/testdata/0.1.0/negative/tokenize/*/ \
         "$ROOT"/testdata/0.1.0/negative/parse/*/; do
    rel="${d#"$ROOT"/testdata/0.1.0/}"
    args+=(--case "${rel%/}")
done
run python3 "$ROOT/tools/rill_harness/cli.py" --repo-root "$ROOT" \
    --sut "$BIN" --bucket negative --kind error "${args[@]}"

echo ""
if [ "$rc" -eq 0 ]; then
    echo "ct/test.sh: PASS"
else
    echo "ct/test.sh: FAIL" >&2
fi
exit "$rc"
