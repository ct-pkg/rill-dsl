# PH-3 红证记录

每个任务在实现提交之前记录一次：`baseline`、命令、原始输出、退出码。
`baseline` 为实现落地前的提交（`git merge-base --is-ancestor <baseline> HEAD` 必须为真）。
实现完成后追加 `green` 行，原始输出不覆盖、不美化。

## PH-3-T1

- baseline: `ff534e1`
- 命令: `python3 tests/phase3/test_ast_json.py`
- 退出码: `1`
- 原始输出:

```text
Traceback (most recent call last):
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase3/test_ast_json.py", line 13, in <module>
    from rill import ast
ImportError: cannot import name 'ast' from 'rill' (/Users/samxx/trae-ws/rill-dsl/tests/phase3/../../src/rill/__init__.py)
```

- green: 待实现

## PH-3-T2

- baseline: `ff534e1`
- 命令: `bash tools/check-0.1.0.sh --kind ast --bucket positive`
- 退出码: `3`
- 原始输出（节选，完整 22 条中 19 条 DRAFT）：

```text
BLOCK   positive/comments/not-header (ast)  not implemented: parse (P1 only implements tokenize)
BLOCK   positive/map/space-header (ast)  not implemented: parse (P1 only implements tokenize)
BLOCK   positive/simple/read-write (ast)  not implemented: parse (P1 only implements tokenize)
summary
  compliance: 0 passed, 0 failed, 3 blocked, 19 draft
VERDICT: NOT IMPLEMENTED (exit 3)
```

- green: 待实现
