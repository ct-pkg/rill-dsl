#!/usr/bin/env bash
# PH-22 样例门禁：CT 与 Python 都跑 examples/phase22/shape-fn.ri，
# 归一化 JSON 空白后与 expected.out 逐行比较。
set -uo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/../.." && pwd)"
out="$(mktemp -d)"
trap 'rm -rf "$out"' EXIT

normalize() {
  python3 - "$1" "$2" <<'PY'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
lines = [line for line in open(src, encoding="utf-8").read().splitlines() if line]
rows = []
for line in lines:
    try:
        rows.append(json.dumps(json.loads(line), ensure_ascii=False, separators=(",", ":")))
    except ValueError:
        rows.append(line)
open(dst, "w", encoding="utf-8").write("\n".join(rows) + "\n")
PY
}

status=0
for side in ct py; do
  if [ "$side" = ct ]; then
    ( cd "$root" && "$root/ct/bin/rill" run examples/phase22/shape-fn.ri \
        --profile shell >"$out/$side.stdout" 2>"$out/$side.stderr" )
  else
    ( cd "$root" && PYTHONPATH="$root/src" python3 -m rill run examples/phase22/shape-fn.ri \
        --profile shell >"$out/$side.stdout" 2>"$out/$side.stderr" )
  fi
  rc=$?
  if [ $rc -ne 0 ]; then
    echo "FAIL $side: 退出码 $rc" >&2
    status=1
    continue
  fi
  cat "$out/$side.stderr" "$out/$side.stdout" >"$out/$side.raw"
  normalize "$out/$side.raw" "$out/$side.norm"
  if diff -u "$root/examples/phase22/expected.out" "$out/$side.norm" >"$out/$side.diff"; then
    echo "PASS $side examples/phase22"
  else
    echo "FAIL $side examples/phase22" >&2
    cat "$out/$side.diff" >&2
    status=1
  fi
done
exit $status
