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
| `testdata/0.1.0/positive/run/` | 分支三态、`[results]`、函数 golden |
| `testdata/0.1.0/expected/run/` | 轨迹/结果 golden |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-9-T1 | `src/rill/eval_parallel.py`（分支与结果数组） | `feat(runtime): PH-9-T1 parallel 分支` | `git revert <sha>` | `bash tools/check-0.1.0.sh --show positive/parallel/results` | M | E-1 |
| PH-9-T2 | `src/rill/eval_parallel.py`（`[results]`） | `feat(runtime): PH-9-T2 results 块` | `git revert <sha>` | `bash tools/check-0.1.0.sh --show positive/parallel/results` | S | E-2 |
| PH-9-T3 | `src/rill/eval_fn.py` | `feat(runtime): PH-9-T3 fn 绑定与返回` | `git revert <sha>` | `bash tools/check-0.1.0.sh --show positive/call/basic` | M | E-3,E-4,E-6 |
| PH-9-T4 | `src/rill/eval_fn.py`（调用错误码） | `feat(runtime): PH-9-T4 调用错误码` | `git revert <sha>` | `bash tools/check-0.1.0.sh --show negative/load/unknown-function` | S | E-5 |
| PH-9-T5 | `testdata/0.1.0/expected/run/` 分支/函数 golden | `feat(runtime): PH-9-T5 golden 接入` | `git revert <sha>` | `bash tools/check-0.1.0.sh --kind run` | S | E-7 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | 分支三态数组顺序与长度正确 | 成功/未处理失败/已处理失败三例逐位比对 |
| E-2 | `[results]` 在非 parallel / 分支内出现时解析期报错 | 负例断言 `code/line/col` |
| E-3 | 模板 3 处 `$path` 只收 1 个实参 | 参数位计数断言 |
| E-4 | 默认值只允许尾部；中间缺省报错 | 两个负例 + 一个正例 |
| E-5 | 未声明函数、错误参数个数有稳定错误码 | 负例逐条断言 |
| E-6 | 函数返回值为最后一条语句的段输出 | golden 与源码末语句一致 |
| E-7 | 任务清单每项可独立验收（T-6） | 收口对照表逐项贴 `verify` 原始输出 |

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
