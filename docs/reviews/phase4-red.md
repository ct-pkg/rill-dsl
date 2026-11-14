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
