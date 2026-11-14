# PH-9 立项卡：`parallel`、`[results]` 与 `//fn` 函数（Runtime 轨）

> 状态：正常开卡。体系见 `docs/phases/README.md`。
> 对齐：`docs/planning/rill-0.1.0-phase-plan.md` phase 9；roadmap phase 9「`parallel`、`[results]`、`//fn`」。
> 规范版本快照：`1.9.0`。语言规范：`docs/RILL-0.1.0.md`（0.1.1，只读）。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-9`，目录 `docs/phases/PH-9/` |
| 目标 | 实现并行分支的结果汇合与函数调用：分支三态、`[results]`、`//fn` 去重参数/默认值/返回。 |
| 范围 | 做什么：分支 `$`、结果数组、`[results]` 触发、多分支失败、`//fn` 名字匹配与绑定、调用错误码。不做什么：真实并发调度、取消、生产审批。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | PH-8 的控制流；PH-4 的 map/fn 表只读接口；PH-3 的 `call_stmt` AST。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `9`（收口目标产品版本 `0.9.0`）。 |
| 已知风险 | 函数返回值二选一、分支内 `$` 成环、调用绑定与 SVO 混用；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| `parallel` 分支内 `$` = 当前分支块输出；`[into]` 按分支内顺序 | 不做真实线程/进程调度 |
| 结果数组按源序、长度 = 分支数；成功/未处理失败 null/已处理失败 value | 不在执行中把分支数组暴露给 `$` |
| `[results]` 只在 parallel 块级、全部完成后触发一次；`$` = 结果数组 | 不在非 parallel 或分支内接受 `[results]` |
| `//fn` 名字精确匹配、参数去重顺序、同名同实参、默认值仅尾部 | 不把 VerbRegistry 的 SVO 绑定混进函数绑定 |
| 多分支同时失败按源序取第一个错误串 | 不实现工具侧审批 |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `src/rill/eval_parallel.py` | 分支执行与结果汇合 |
| `src/rill/eval_fn.py` | 函数调用与参数绑定 |
| `src/rill/parser.py` | `[results]` 单判据；`$变量?默认值` 归约 |
| `src/rill/lexer.py` | `//fn{}` 区块边界：块内 `//` 不再触发 header 特例 |
| `src/rill/loader.py` | 模板参数表、默认值位置、调用 arity 校验 |
| `testdata/0.1.0/positive/run/parallel/` | 分支三态、`[results]` run 用例 |
| `testdata/0.1.0/positive/run/call/` | 函数调用、默认值、返回值 run 用例 |
| `testdata/0.1.0/expected/run/` | 轨迹/结果 golden |
| `tests/phase9/` | 可失败的单测（parallel / results / fn / errors / cases） |
| `docs/reviews/phase9-red.md` | 逐任务红证与转绿记录 |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-9-T1 | `src/rill/eval_parallel.py`（分支与结果数组） | `feat(runtime): PH-9-T1 parallel 分支` | `git revert <sha>` | `python3 tests/phase9/test_parallel.py` | M | E-1 |
| PH-9-T2 | `src/rill/eval_parallel.py`（`[results]`）+ `parser.py`（单判据） | `feat(runtime): PH-9-T2 results 块` | `git revert <sha>` | `python3 tests/phase9/test_results.py` | S | E-2 |
| PH-9-T3 | `src/rill/eval_fn.py` + `parser.py`（默认值）+ `lexer.py`（区块边界） | `feat(runtime): PH-9-T3 fn 绑定与返回` | `git revert <sha>` | `python3 tests/phase9/test_fn.py` | M | E-3,E-4,E-6 |
| PH-9-T4 | `src/rill/loader.py` + `src/rill/eval_fn.py`（调用错误码） | `feat(runtime): PH-9-T4 调用错误码` | `git revert <sha>` | `python3 tests/phase9/test_errors.py` | S | E-5 |
| PH-9-T5 | `testdata/0.1.0/positive/run/` 分支/函数 golden | `feat(runtime): PH-9-T5 golden 接入` | `git revert <sha>` | `python3 tests/phase9/test_cases.py` | S | E-7 |

verify 一律是可失败的单测命令：`--show` 只打印被测输出，不作为验收依据。

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | 分支三态数组顺序与长度正确 | `test_parallel.py`：成功/未处理失败/已处理失败三例逐位比对，并断言分支内 `$` 不是结果数组 |
| E-2 | `[results]` 在非 parallel / 分支内出现时解析期报错 | `test_results.py`：尾随块位、普通介宾位、独立介宾位、parallel 分支四个位置统一断言 `code/line/col` |
| E-3 | 模板 3 处 `$path` 只收 1 个实参 | `test_fn.py`：参数位计数与同名绑定断言 |
| E-4 | 默认值只允许尾部；中间缺省报错 | `test_fn.py`：两个负例 + 一个正例；正例断言默认值实参可省略 |
| E-5 | 未声明函数、错误参数个数有稳定错误码 | `test_errors.py`：未声明（加载期）与少参/多参（加载期）逐条断言 |
| E-6 | 函数返回值为最后一条语句的段输出 | `test_fn.py`：golden 与源码末语句一致，空体返回 `null` |
| E-7 | 任务清单每项可独立验收（T-6） | `test_cases.py` + 全量 harness；收口对照表逐项贴 `verify` 原始输出 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | PH-8 的段输出与 `break` 场域；PH-4 的 `FnTable` 只读接口；PH-3 的 `call_stmt` 与 `trailing_block*`。 |
| 风险 1 | 返回值二选一（最后一条语句 / `$` 最终值）：PH-9 固定为“最后一条语句段输出”。触发信号：golden 出现两种结果。 |
| 风险 2 | 分支内 `$` 取最终数组：会成环。触发信号：分支读到自己尚未完成的结果。 |
| 风险 3 | 调用绑定混入 SVO：会让函数签名依赖动词表。触发信号：函数调用需要 VerbRegistry 才可解析。 |

## 6. 收口与 tag

- 收口时产品版本 `0.9.0`；annotated tag `v0.9.0`，message 含 `PH-9` 与收口提交 sha 前 7 位。
- 只推 tag，不推分支、不对外发布。收口对照表：`docs/reviews/closeout-9.md`（收口时新建）。

## 8. 规范缺口与实现裁定（不改变规范正文）

下列各条在规范里没有唯一表述。**先实测、再裁定**：裁定只写进本表，不写进
`docs/RILL-0.1.0.md`；后续 CR 需要逐条收口。红证与实现位置见
`docs/reviews/phase9-red.md`。

| # | 位置 | 缺口 | 本 phase 的实测与裁定 |
| --- | --- | --- | --- |
| 1 | §4.5 / §4.14 | `[results]` 与通用介词表的关系：只写“不是通用介词”，未给判定位置 | **实测：单判据 `_reject_results`**，在尾随块位、普通介宾位、独立介宾位、语句尾方括号四处统一报 `E-PARSE-RESULTS-CONTEXT`（位置=`[`）；只有 `parallel` 尾随块路径消费它，不落进 `_PREPS`。`case_results_only_in_parallel_tail` |
| 2 | §4.14 | 分支自身产出按什么顺序汇集；逻辑并行还是真并发 | **实测：按源序逐条执行、逐位汇集**（“逻辑并行、顺序可观察”，无真实调度）。`case_all_success_keeps_source_order` |
| 3 | §4.14 | 某个分支失败时 parallel 整体的 `ok`/错误串；“不论整体成败”未定义成败判据 | **实测：任一分支未处理失败 → 整体 `ok=false`**，错误串取源序第一个失败分支的错误串；已处理失败不算整体失败。`case_three_state_array` |
| 4 | §4.14 | 部分成功的表示：结果数组占位还是整体失败吞掉数组 | **实测：整体失败但 `value` 仍是结果数组**，失败位置为 `null`；顶层 `run` 只暴露 `error`，数组留在 `ExecOutcome.value`。`case_three_state_array` |
| 5 | §4.14 / §4.8 | 分支内 `$` 的初始值（进入 parallel 的 `$`、`null`，还是分支未完成输出） | **实测：进入 parallel 的当前 `$`**（顶层为 `null`），不是结果数组；避免执行中成环。`case_branch_dollar_is_not_results_array` |
| 6 | §4.14 / §4.15 | 分支内未处理 `break` 的归属与 `->$var` 捕捉落点 | **实测：分支失败、元素 `null`，错误串 = break 值**；`->$var` 写 parallel 所在作用域（显式捕捉，不按“禁止分支写外部变量”处理）。`case_three_state_array` |
| 7 | §4.14 / §4.6 | parallel 有失败时其后的 `\|>` 是否执行；`[results]` 块失败时整体状态 | 管道：**整体失败则下游不执行**（`case_pipe_skipped_after_failure`）。`[results]`：**分支失败也触发**，值=结果数组、状态仍失败；块自身失败（含块内未处理 break）**覆盖整体错误串**（`case_results_block_failure_overrides`） |
| 8 | §4.18 | 函数体 `break` 的场域：中断函数返回、转成调用失败，还是穿到调用方 | 待实测（T3） |
| 9 | §4.18 / §4.8 | 函数体内 `$` 的初始值；函数体写外层变量的可见性 | 待实测（T3） |
| 10 | §4.18 | 默认值表达式在何处求值（调用方作用域/函数体作用域）；同名默认值冲突 | 待实测（T3） |
| 11 | §4.18 | 参数个数不匹配的报错阶段（加载期静态可知 vs 运行期） | 待实测（T4） |
| 12 | §3.1 / §4.18 | `//fn{}` 块内再出现 `//fn {` / `//map {` 时的词法归属 | 待实测（T3） |
| 13 | §4.18 | 模板同名参数在不同出现处写不同默认值的行为 | 待实测（T3） |
