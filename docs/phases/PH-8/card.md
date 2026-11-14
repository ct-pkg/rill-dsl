# PH-8 立项卡：管道、`if`、`each`、`break`（Runtime 轨）

> 状态：正常开卡。体系见 `docs/phases/README.md`。
> 对齐：`docs/planning/rill-0.1.0-phase-plan.md` phase 8；roadmap phase 8「管道、`if`、`each`、`break`」。
> 规范版本快照：`1.9.0`。语言规范：`docs/RILL-0.1.0.md`（0.1.1，只读）。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-8`，目录 `docs/phases/PH-8/` |
| 目标 | 把单语句组合成管道与控制流：管道只传 value，`if` 用 truthy，`each` 产数组并处理失败，`break` 按场域中断。 |
| 范围 | 做什么：`\|>` 分段、`if/else-if/else`、`each` 三种输入与每轮结果、each 级 `[ok]/[error]`、`break` 三场域。不做什么：`parallel`/`[results]`/`//fn`。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | PH-7 的单语句执行；PH-6 的 truthy；PH-3 的 AST。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `8`（收口目标产品版本 `0.8.0`）。 |
| 已知风险 | 每轮作用域、`$` 被 `[in]` 宾语覆盖、`break` 跨场域；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| `\|>`：段间只传 value，下游失败不回溯上游，折行规则按 §4.6 | 不做 OS 管道 |
| `if/else-if/else`：条件无尾随块、truthy/falsy、不参与管道 | 不把 `if` 的 truthy 与 `[ok]` 的 `ok` 混用 |
| `each`：null → 零次/error、数组遍历、非数组单元素一次 | 不实现 parallel 分支 |
| each 每轮 `{value, ok}`：失败未处理为 null 且继续；`[error]` 处理后取 value | 不做真实并发调度 |
| `break`：顶层/管道/块三场域；`break <值> -> $var`；无捕捉丢弃 | 不改变 AST 的书写顺序 |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `src/rill/eval_control.py` | 管道、if、each、break |
| `testdata/0.1.0/positive/run/` | 管道/if/each/break 轨迹用例 |
| `testdata/0.1.0/expected/run/` | 轨迹 golden |
| `testdata/0.1.0/negative/run/` | 场域与 truthy 负例 |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-8-T1 | `src/rill/eval_control.py`（管道） | `feat(runtime): PH-8-T1 管道分段` | `git revert <sha>` | `bash tools/check-0.1.0.sh --show positive/pipe/multi-line` | M | E-1 |
| PH-8-T2 | `src/rill/eval_control.py`（if/else） | `feat(runtime): PH-8-T2 if 控制流` | `git revert <sha>` | `bash tools/check-0.1.0.sh --show positive/if/else-if` | S | E-2 |
| PH-8-T3 | `src/rill/eval_control.py`（each） | `feat(runtime): PH-8-T3 each 遍历` | `git revert <sha>` | `bash tools/check-0.1.0.sh --show positive/each/bareword-value` | M | E-3,E-4 |
| PH-8-T4 | `src/rill/eval_control.py`（break） | `feat(runtime): PH-8-T4 break 场域` | `git revert <sha>` | `bash tools/check-0.1.0.sh --show positive/break/capture` | M | E-5 |
| PH-8-T5 | `testdata/0.1.0/expected/run/` 轨迹 golden | `feat(runtime): PH-8-T5 轨迹 golden` | `git revert <sha>` | `bash tools/check-0.1.0.sh --kind run` | S | E-6 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | 管道 3 段以上，每段 `[error]` 只覆盖本段 | 轨迹 golden：段边界与错误归属 |
| E-2 | `if` 的 truthy/falsy 与 `[ok]` 的 `ok` 分离 | 空串成功仍走 `[ok]`，`if` 走 falsy |
| E-3 | each 空数组 0 次、null 0 次、非数组 1 次 | 三个计数断言 |
| E-4 | 某轮失败后循环继续，结果数组对应位为 null | 数组逐位比对 |
| E-5 | `break` 只中断当前场域；带值 break 可被外部变量捕捉 | 场域轨迹 + 捕捉断言 |
| E-6 | 任务清单每项可独立验收（T-6） | 收口对照表逐项贴 `verify` 原始输出 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | PH-7 的段输出与 `[into]` 顺序；PH-6 的 truthy 与 `$`；`W-01` 只在 `check` 触发，不影响 run。 |
| 风险 1 | each 每轮作用域未固定：会留下“每轮共享 `$`”的二义。触发信号：两轮之间变量可见。 |
| 风险 2 | `$` 被 `[in]` 宾语覆盖：each 体内 `$` 必须是当前项。触发信号：体内 `$` 等于整个数组。 |
| 风险 3 | `break` 跨场域：块内 break 中断整个 program。触发信号：E-5 轨迹越界。 |

## 6. 收口与 tag

- 收口时产品版本 `0.8.0`；annotated tag `v0.8.0`，message 含 `PH-8` 与收口提交 sha 前 7 位。
- 只推 tag，不推分支、不对外发布。收口对照表：`docs/reviews/closeout-8.md`（收口时新建）。
