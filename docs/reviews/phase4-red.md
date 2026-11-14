# PH-4 红证记录

每个任务在实现提交之前记录一次：`baseline`、命令、原始输出、退出码。
`baseline` 为实现落地前的提交（`git merge-base --is-ancestor <baseline> HEAD` 必须为真）。
实现完成后追加 `green` 行，原始输出不覆盖、不美化。

## PH-4-T1

- baseline: `19d5cc7`
- 命令: `bash tools/check-0.1.0.sh --case negative/load/map-duplicate-short`
- 退出码: `3`
- 原始输出:

```text
RILL 0.1.0 harness
root     : testdata/0.1.0
sut      : python3 -m rill
profiles : agent, shell
fixtures : 1 (negative 1)
filters  : case=negative/load/map-duplicate-short

BLOCK   negative/load/map-duplicate-short (error)  not implemented: check (P1 only implements tokenize)

summary
  compliance: 0 passed, 0 failed, 1 blocked, 0 draft
  smoke:     0 passed, 0 failed, 0 blocked, 0 draft
  pending:   0 not run (A 0, B 0)
VERDICT: NOT IMPLEMENTED (exit 3)
```

- E-5 附加断言:
  - 命令: `python3 tests/phase4/test_no_exec.py`
  - 退出码: `1`
  - 原始输出:

```text
Traceback (most recent call last):
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase4/test_no_exec.py", line 16, in <module>
    from rill import loader
ImportError: cannot import name 'loader' from 'rill' (/Users/samxx/trae-ws/rill-dsl/tests/phase4/../../src/rill/__init__.py)
```

- green: `bash tools/check-0.1.0.sh --case negative/load/map-duplicate-short` → `rc=0`，
  `PASS load E-LOAD-MAP-DUP-SHORT@3:1`；`python3 tests/phase4/test_no_exec.py` → `rc=0`。

## PH-4-T2

- baseline: `19d5cc7`
- 命令: `bash tools/check-0.1.0.sh --case negative/load/unknown-function`
- 退出码: `1`
- 原始输出:

```text
RILL 0.1.0 harness
root     : testdata/0.1.0
sut      : python3 -m rill
profiles : agent, shell
fixtures : 1 (negative 1)
filters  : case=negative/load/unknown-function

FAIL    negative/load/unknown-function (error)  期望诊断，实际成功（退出码 0）

summary
  compliance: 0 passed, 1 failed, 0 blocked, 0 draft
  smoke:     0 passed, 0 failed, 0 blocked, 0 draft
  pending:   0 not run (A 0, B 0)
VERDICT: FAIL (exit 1)
```

- green: `bash tools/check-0.1.0.sh --case negative/load/unknown-function` → `rc=0`，
  `PASS load E-LOAD-FN-UNDECLARED@1:1`。

## PH-4-T3

- baseline: `19d5cc7`
- 命令: `bash tools/check-0.1.0.sh --case negative/load/unknown-verb --case positive/check/host-profiles`
- 退出码: `1`
- 原始输出:

```text
RILL 0.1.0 harness
root     : testdata/0.1.0
sut      : python3 -m rill
profiles : agent, shell
fixtures : 2 (positive 1, negative 1)
filters  : case=negative/load/unknown-verb,positive/check/host-profiles

FAIL    negative/load/unknown-verb (error)  期望诊断，实际成功（退出码 0）
PASS    positive/check/host-profiles (check)  check 通过（shell / agent）

summary
  compliance: 1 passed, 1 failed, 0 blocked, 0 draft
  smoke:     0 passed, 0 failed, 0 blocked, 0 draft
  pending:   0 not run (A 0, B 0)
VERDICT: FAIL (exit 1)
```

- green: `bash tools/check-0.1.0.sh --case negative/load/unknown-verb
  --case positive/check/host-profiles` → `rc=0`，
  `PASS load E-LOAD-VERB-UNKNOWN@1:1`、`PASS check 通过（shell / agent）`。

## PH-4-T4

- baseline: `19d5cc7`
- 命令: `bash tools/check-0.1.0.sh --case positive/check/each-bareword-w01`
- 退出码: `1`
- 原始输出:

```text
RILL 0.1.0 harness
root     : testdata/0.1.0
sut      : python3 -m rill
profiles : agent, shell
fixtures : 1 (positive 1)
filters  : case=positive/check/each-bareword-w01

FAIL    positive/check/each-bareword-w01 (warning)  未产生 W-01；实际警告：无

summary
  compliance: 0 passed, 1 failed, 0 blocked, 0 draft
  smoke:     0 passed, 0 failed, 0 blocked, 0 draft
  pending:   0 not run (A 0, B 0)
VERDICT: FAIL (exit 1)
```



