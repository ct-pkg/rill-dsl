# PH-7 红证

基线：`36a5b0c`（PH-7 任务清单复核与 E-2 归属修正之后）。
每节的红证都在对应实现提交之前采集，命令与输出原样保留；`exit` 是被测命令的退出码。

## T1 `[into]` 顺序与失败

- 命令：`python3 tests/phase7/test_into.py`
- 退出码：`1`
- 原始输出：

```text
Traceback (most recent call last):
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase7/test_into.py", line 14, in <module>
    from rill.eval_simple import Interpreter
ModuleNotFoundError: No module named 'rill.eval_simple'
```

原因：`src/rill/eval_simple.py` 尚未存在，`[into]` 执行器没有落盘。

## T2 `[ok]/[error]` 与 `$`

- 命令：`python3 tests/phase7/test_ok_error.py`
- 退出码：`1`
- 原始输出：

```text
Traceback (most recent call last):
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase7/test_ok_error.py", line 121, in <module>
    main()
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase7/test_ok_error.py", line 110, in main
    case_ok_block_sees_value()
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase7/test_ok_error.py", line 22, in case_ok_block_sees_value
    interp, out = run(
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase7/test_ok_error.py", line 18, in run
    return interp, interp.eval_program(parse_source(source), variables=variables)
  File "/Users/samxx/trae-ws/rill-dsl/src/rill/eval_simple.py", line 85, in eval_program
    outcome = self.eval_statement(statement, scope, input_value)
  File "/Users/samxx/trae-ws/rill-dsl/src/rill/eval_simple.py", line 99, in eval_statement
    return self.eval_simple(statement, scope, dollar)
  File "/Users/samxx/trae-ws/rill-dsl/src/rill/eval_simple.py", line 134, in eval_simple
    raise EvalError(
rill.eval_simple.EvalError: [ok] 在 PH-7-T2 实现
```

原因：T1 只实现 `[into]`，`[ok]/[error]` 仍是显式未实现分支。

