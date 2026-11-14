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

## T2 `each` 遍历与每轮成败

- 命令：`python3 tests/phase8/test_each.py`
- 退出码：`1`
- 原始输出：

```text
Traceback (most recent call last):
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase8/test_each.py", line 193, in <module>
    main()
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase8/test_each.py", line 179, in main
    case_three_input_shapes()
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase8/test_each.py", line 24, in case_three_input_shapes
    interp, out = run(EACH_SEND, {"send": SEND}, {"v": None})
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase8/support.py", line 43, in run
    return interp, interp.eval_program(parse_source(source), variables=variables)
  File "/Users/samxx/trae-ws/rill-dsl/src/rill/eval_simple.py", line 85, in eval_program
    outcome = self.eval_statement(statement, scope, input_value)
  File "/Users/samxx/trae-ws/rill-dsl/src/rill/eval_simple.py", line 109, in eval_statement
    raise EvalError(
rill.eval_simple.EvalError: EachStmt 不在 PH-8 的执行范围（each 见 T2，parallel/@ 见 PH-9）
```

原因：`EachStmt` 仍在统一未实现分支；三种输入、每轮作用域与 each 级
`[ok]/[error]` 都没有执行路径。

## T3 `break` 三场域

- 命令：`python3 tests/phase8/test_break.py`
- 退出码：`1`
- 原始输出：

```text
Traceback (most recent call last):
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase8/test_break.py", line 161, in <module>
    main()
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase8/test_break.py", line 150, in main
    case_pipe_break_stops_pipe_only()
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase8/test_break.py", line 50, in case_pipe_break_stops_pipe_only
    assert called(interp) == ["read", "write", "send"], "break 不应中断 program"
AssertionError: break 不应中断 program
```

原因：块内 `break` 一路穿到 `eval_program` 的总捕获，管道没有自己的场域；
`break` 之后的下一条语句不会执行，each 也不会在循环层截住 break。

## T4 run 用例与轨迹 golden

- 命令：`python3 tests/phase8/test_cases.py`
- 退出码：`1`
- 原始输出：

```text
Traceback (most recent call last):
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase8/test_cases.py", line 119, in <module>
    main()
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase8/test_cases.py", line 113, in main
    case_run_cases_exist_and_pass()
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase8/test_cases.py", line 77, in case_run_cases_exist_and_pass
    assert os.path.isdir(directory), "缺少用例：positive/run/control/%s" % name
AssertionError: 缺少用例：positive/run/control/if-subject
```

原因：`control/` 下的 run 用例与 `expected/run/control-*.json` 尚未落盘；
T4 的交付物就是这批可独立验收的用例与轨迹。

## 转绿记录

| 任务 | 命令 | 结果 |
| --- | --- | --- |
| T1 | `python3 tests/phase8/test_if.py` | `PASS phase8 if: truthy 表、[ok] 分离、主语条件、else-if、条件管道`，exit 0 |
| T2 | `python3 tests/phase8/test_each.py` | `PASS phase8 each: 三形态、每轮作用域、失败轮 null、each 级 ok/error`，exit 0 |
| T3 | `python3 tests/phase8/test_break.py` | `PASS phase8 break: 三场域、each+break 三组合、裸词捕捉`，exit 0 |
| T4 | `python3 tests/phase8/test_cases.py` | `PASS phase8 cases: 7 个 run 用例、2 份轨迹 golden`，exit 0 |

整桶与整仓：

```text
bash tools/check-0.1.0.sh --kind run --bucket positive
→ compliance: 15 passed, 0 failed, 0 blocked, 0 draft
→ VERDICT: PASS (exit 0)

bash tools/check-0.1.0.sh
→ compliance: 73 passed, 0 failed, 0 blocked, 0 draft
→ smoke: 2 passed, 0 failed
→ VERDICT: PASS (exit 0)

bash tools/check.sh g1 / g8
→ g1: PARTIAL（卡片与索引已校验，验收命令按“尚未落盘”登记）
→ g8: PARTIAL（phase 冻结与版本落点已校验）
```
