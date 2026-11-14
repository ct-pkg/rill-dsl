# PH-8 红证

基线：`407adb4`（PH-8 任务清单复核之后）。
每节的红证都在对应实现提交之前采集，命令与输出原样保留；`exit` 是被测命令的退出码。

## T1 `if` 条件求值

- 命令：`python3 tests/phase8/test_if.py`
- 退出码：`1`
- 原始输出：

```text
Traceback (most recent call last):
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase8/test_if.py", line 181, in <module>
    main()
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase8/test_if.py", line 169, in main
    case_truthy_falsy_table()
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase8/test_if.py", line 38, in case_truthy_falsy_table
    assert branch_taken(IF_ELSE, {"send": SEND}, {"v": item}) == "F", (
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase8/test_if.py", line 27, in branch_taken
    interp, out = run(source, script, variables=variables)
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase8/support.py", line 43, in run
    return interp, interp.eval_program(parse_source(source), variables=variables)
  File "/Users/samxx/trae-ws/rill-dsl/src/rill/eval_simple.py", line 85, in eval_program
    outcome = self.eval_statement(statement, scope, input_value)
  File "/Users/samxx/trae-ws/rill-dsl/src/rill/eval_simple.py", line 104, in eval_statement
    raise EvalError(
rill.eval_simple.EvalError: IfStmt 不在 PH-7 的执行范围（PH-8/PH-9）
```

原因：`eval_statement` 仍把 `IfStmt` 归入统一未实现分支；`if` 没有求值路径。
