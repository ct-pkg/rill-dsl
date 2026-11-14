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

- green: `rc=0`，`PASS ast-json: 29 个节点，字段顺序与 span 归一化符合预期`

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

- green: `rc=0`，`3 passed`（comments/not-header、map/space-header、simple/read-write）

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

- green: `rc=0`，`12 passed / 10 draft`

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

- green: `rc=0`，`20 passed / 3 draft`（golden 补齐后 23/23）

## PH-3-T5

- baseline: `ff534e1`
- 命令: `bash tools/check-0.1.0.sh --phase p2 --bucket negative --kind error`
- 退出码: `1`
- 原始输出：

```text
PASS    negative/parse/break-verb-value (error)  parse E-PARSE-BREAK-VALUE@1:7
PASS    negative/parse/duplicate-error (error)  parse E-PARSE-DUP-ERROR@1:47
PASS    negative/parse/duplicate-ok (error)  parse E-PARSE-DUP-OK@1:44
PASS    negative/parse/fn-def-in-body (error)  parse E-PARSE-FN-DEF-BODY@1:1
PASS    negative/parse/missing-block (error)  parse E-PARSE-MISSING-BLOCK@1:30
PASS    negative/parse/results-in-branch (error)  parse E-PARSE-RESULTS-CONTEXT@2:18
PASS    negative/parse/results-outside-parallel (error)  parse E-PARSE-RESULTS-CONTEXT@1:14
FAIL    negative/parse/unknown-prep (error)  期望诊断，实际成功（退出码 0）
summary
  compliance: 7 passed, 1 failed, 0 blocked, 0 draft
VERDICT: FAIL (exit 1)
```

- green: `rc=0`，`8 passed`（含 unknown-prep）
