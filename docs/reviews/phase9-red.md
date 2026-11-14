# PH-9 红证

基线：`cccd1bd`（PH-9 任务清单复核之后）。
每节的红证都在对应实现提交之前采集，命令与输出原样保留；`exit` 是被测命令的退出码。

## T1 parallel 分支

- 命令：`python3 tests/phase9/test_parallel.py`
- 退出码：`1`
- 原始输出：

```text
Traceback (most recent call last):
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase9/test_parallel.py", line 140, in <module>
    main()
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase9/test_parallel.py", line 129, in main
    case_three_state_array()
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase9/test_parallel.py", line 40, in case_three_state_array
    interp, out = run(source, script)
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase9/support.py", line 51, in run
    return interp, interp.eval_program(parse_source(source), variables=variables)
  File "/Users/samxx/trae-ws/rill-dsl/src/rill/eval_simple.py", line 85, in eval_program
    outcome = self.eval_statement_in_domain(statement, scope, input_value)
  File "/Users/samxx/trae-ws/rill-dsl/src/rill/eval_simple.py", line 129, in eval_statement_in_domain
    return self.eval_statement(statement, scope, dollar)
  File "/Users/samxx/trae-ws/rill-dsl/src/rill/eval_simple.py", line 113, in eval_statement
    raise EvalError(
rill.eval_simple.EvalError: ParallelStmt 不在 PH-8 的执行范围（parallel/@ 见 PH-9）
```

原因：`eval_statement` 仍把 `ParallelStmt` 归入统一未实现分支，没有分支执行与结果汇合路径。

## T2 `[results]` 判据与块

- 命令：`python3 tests/phase9/test_results.py`
- 退出码：`1`
- 原始输出：

```text
Traceback (most recent call last):
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase9/test_results.py", line 130, in <module>
    main()
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase9/test_results.py", line 122, in main
    case_results_only_in_parallel_tail()
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase9/test_results.py", line 53, in case_results_only_in_parallel_tail
    expect_results_context(source, line, col)
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase9/test_results.py", line 23, in expect_results_context
    assert exc.code == "E-PARSE-RESULTS-CONTEXT", exc.code
AssertionError: E-PARSE-UNKNOWN-PREP
```

原因：`[results]` 在普通介宾位落进通用介词表，报的是 `E-PARSE-UNKNOWN-PREP`，
没有一条“只在 parallel 尾随块位置合法”的判据；执行器也还拒绝 results 块。

## T3 `//fn` 绑定与返回

- 命令：`python3 tests/phase9/test_fn.py`
- 退出码：`1`
- 原始输出：

```text
Traceback (most recent call last):
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase9/test_fn.py", line 266, in <module>
    main()
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase9/test_fn.py", line 249, in main
    case_three_occurrences_one_argument()
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase9/test_fn.py", line 37, in case_three_occurrences_one_argument
    interp, out = run_loaded(source, {"send": SEND})
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase9/support.py", line 59, in run_loaded
    interp = Interpreter(registry(script), functions=load.functions)
TypeError: __init__() got an unexpected keyword argument 'functions'
```

原因：解释器没有 `FnTable` 入口，`CallStmt` 无执行路径；模板里的 `?` 默认值
也还没有归约，`//fn` 块内的 `//` 仍会触发 header 特例。

## T4 调用错误码

- 命令：`python3 tests/phase9/test_errors.py`
- 退出码：`1`
- 原始输出：

```text
Traceback (most recent call last):
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase9/test_errors.py", line 91, in <module>
    main()
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase9/test_errors.py", line 84, in main
    case_too_few_arguments()
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase9/test_errors.py", line 65, in case_too_few_arguments
    expect_load_error(
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase9/test_errors.py", line 46, in expect_load_error
    raise AssertionError("应报 %s：%r" % (code, source))
AssertionError: 应报 E-LOAD-FN-ARITY：'//fn{\n@ "two" $x <read> $x |> $y <parse> $y {\n    <read> $x\n}\n}\n@ "two" "a.yml"\n'
```

原因：加载期只查未声明函数，不校验实参个数；少参会被静默放行。

## T5 run 用例与轨迹 golden

- 命令：`python3 tests/phase9/test_cases.py`
- 退出码：`1`
- 原始输出：

```text
Traceback (most recent call last):
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase9/test_cases.py", line 121, in <module>
    main()
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase9/test_cases.py", line 115, in main
    case_run_cases_exist_and_pass()
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase9/test_cases.py", line 72, in case_run_cases_exist_and_pass
    assert os.path.isdir(directory), "缺少用例：positive/run/%s" % name
AssertionError: 缺少用例：positive/run/parallel/three-state
```

原因：`positive/run/parallel/`、`positive/run/call/` 与 `expected/run/{parallel,call}-*.json`
尚未落盘；T5 的交付物就是这批可独立验收的用例与轨迹。

## 转绿记录

| 任务 | 命令 | 结果 |
| --- | --- | --- |
| T1 | `python3 tests/phase9/test_parallel.py` | "PASS phase9 parallel: 分支三态、源序、分支 $ 与作用域"，exit 0 |
| T2 | `python3 tests/phase9/test_results.py` | "PASS phase9 results: 单判据四位置、触发一次、数组 $ 与失败状态"，exit 0 |
| T3 | `python3 tests/phase9/test_fn.py` | "PASS phase9 fn: 去重参数、尾部默认值、返回值、//fn 边界"，exit 0 |
| T4 | `python3 tests/phase9/test_errors.py` | "PASS phase9 errors: 未声明、精确名字、少参/多参、尾部默认值"，exit 0 |
| T5 | `python3 tests/phase9/test_cases.py` | "PASS phase9 cases: 4 个 run 用例、4 份轨迹 golden"，exit 0 |

整桶与整仓：

```text
bash tools/check-0.1.0.sh --bucket negative
→ compliance: 26 passed, 0 failed, 0 blocked, 0 draft
→ VERDICT: PASS (exit 0)

bash tools/check-0.1.0.sh
→ compliance: 83 passed, 0 failed, 0 blocked, 0 draft
→ smoke: 2 passed, 0 failed
→ VERDICT: PASS (exit 0)

bash tools/check.sh g1 / g8
→ g1: PARTIAL（卡片与索引已校验，验收命令按“尚未落盘”登记）
→ g8: PARTIAL（phase 冻结与版本落点已校验）
```

## §8 缺口登记（实测裁定）

| # | 一句话 |
| --- | --- |
| 1 | `[results]` 用单判据 `_reject_results`：只在 parallel 尾随块位合法，其余方括号入口统一报 `E-PARSE-RESULTS-CONTEXT`，不落进通用介词表。 |
| 2 | 分支按源序逐条执行、逐位汇集，逻辑并行、顺序可观察，不做真实调度。 |
| 3 | 任一分支未处理失败 → parallel 整体 `ok=false`，错误串取源序第一个失败分支。 |
| 4 | 部分成功表现为结果数组对应位 `null`，整体失败但 `ExecOutcome.value` 仍是数组。 |
| 5 | 分支内 `$` = 进入 parallel 的当前 `$`（顶层 `null`），不是结果数组。 |
| 6 | 分支内未处理 break → 分支失败、元素 `null`、错误串 = break 值；`->$var` 写 parallel 所在作用域。 |
| 7 | parallel 整体失败时管道下游不执行；`[results]` 分支失败也触发，块自身失败覆盖整体错误串。 |
| 8 | 函数体 break 转成调用失败（错误串 = break 值），调用上的 `[error]` 可处理。 |
| 9 | 函数体 `$` = 调用语句进入时的 `$`；体内新变量不泄漏，外层已有变量按 Scope 链可读。 |
| 10 | 默认值在调用方作用域、调用时求值；同名默认值冲突取首次出现。 |
| 11 | 参数个数在加载期校验，报 `E-LOAD-FN-ARITY`（位置=`@`）；运行期 `E-RUN-FN-ARITY` 仅作绕过加载器的防御。 |
| 12 | `//fn{}` 块内 `//` 一律行注释，不再产生 header；嵌套定义形状由 `E-PARSE-FN-DEF-BODY` 拒绝。 |
| 13 | 模板同名参数在不同出现处写不同默认值时，取首次出现的默认值。 |

## `run` 能力对照（PH-9 之后）

| 脚本类别 | 现状 |
| --- | --- |
| 单语句、管道、尾随 `[into]/[ok]/[error]`、`->$x` | 能跑 |
| `if` / `else-if` / `else`（含主语条件、条件管道） | 能跑 |
| `each`（null/数组/单值、每轮成败、each 级 tail） | 能跑 |
| `break`（program / each / 管道 / 块） | 能跑 |
| `parallel`（分支三态、`[results]`、管道） | 能跑 |
| `@` 函数调用（去重参数、尾部默认值、最后一段返回） | 能跑 |
| 独立 `[ok] $x { ... }` / `[error] $x { ... }` | 不能：`E-RUN-UNSUPPORTED`（PH-7 卡 §8 #5） |
| 真实宿主工具（不带 `--fakes`） | 不能：`E-RUN-VERB-UNREGISTERED`（PH-10 接能力层） |
| `rill fmt` | 不能：`exit 3`（PH-5 不在本线） |
| 真实并发 / 取消 / 生产审批 | 不实现（§1 范围） |
