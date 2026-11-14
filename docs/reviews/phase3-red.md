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

## PH-3-T3

- baseline: `ff534e1`
- 命令: `bash tools/check-0.1.0.sh --kind ast --bucket positive`
- 退出码: `1`
- 原始输出（节选；`map/verb-marker` 与 `simple/subject-var` 已被 T2 覆盖，故提前 PASS）：

```text
FAIL    positive/call/basic (ast)  SUT 错误：//fn{} 区块在 PH-3-T3 加入
FAIL    positive/map/header (ast)  SUT 错误：管道在 PH-3-T3 加入
FAIL    positive/pipe/multi-line (ast)  SUT 错误：管道在 PH-3-T3 加入
FAIL    positive/prep/ok-as-prep (ast)  SUT 错误：尾随块在 PH-3-T4 加入
FAIL    positive/quotes/escapes (ast)  SUT 错误：尾随块在 PH-3-T4 加入
FAIL    positive/simple/assign (ast)  SUT 错误：-> 赋值在 PH-3-T3 加入
FAIL    positive/simple/prep-phrases (ast)  SUT 错误：尾随块在 PH-3-T4 加入
summary
  compliance: 5 passed, 7 failed, 0 blocked, 10 draft
VERDICT: FAIL (exit 1)
```

- green: 待实现

## PH-3-T4

- baseline: `ff534e1`
- 命令: `bash tools/check-0.1.0.sh --kind ast --bucket positive`
- 退出码: `1`
- 原始输出：

```text
FAIL    positive/block/into-independent (ast)  SUT 错误：独立介宾块在 PH-3-T4 加入
FAIL    positive/block/trailing (ast)  SUT 错误：尾随块在 PH-3-T4 加入
FAIL    positive/break/bareword-value (ast)  SUT 错误：关键字 'break' 的语句在 PH-3-T4 加入
FAIL    positive/break/capture (ast)  SUT 错误：尾随块在 PH-3-T4 加入
FAIL    positive/each/bareword-value (ast)  SUT 错误：关键字 'each' 的语句在 PH-3-T4 加入
FAIL    positive/if/else-if (ast)  SUT 错误：关键字 'if' 的语句在 PH-3-T4 加入
FAIL    positive/parallel/results (ast)  SUT 错误：关键字 'parallel' 的语句在 PH-3-T4 加入
FAIL    positive/value/five-branches (ast)  SUT 错误：关键字 'break' 的语句在 PH-3-T4 加入
summary
  compliance: 12 passed, 8 failed, 0 blocked, 3 draft
VERDICT: FAIL (exit 1)
```

- green: 待实现
