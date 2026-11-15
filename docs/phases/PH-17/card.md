# PH-17 立项卡：CT 控制流与函数（P5）

> 状态：正常开卡。CT 重写轨道第 5 层。体系见 `docs/phases/README.md`，
> 上游 `docs/planning/rill-0.1.0-ct-rewrite-roadmap.md`。语言规范 `docs/RILL-0.1.0.md`（0.1.1，只读）。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-17`，目录 `docs/phases/PH-17/` |
| 目标 | CT 版跑通 `if`/`each`/`break`/`parallel`/`[results]`/`//fn`，处理完 9 个 control/parallel run 用例与函数用例。 |
| 范围 | 做什么：truthy 控制流、each 三态、break 场域、并行分支结果数组、`[results]`、函数去重参数/默认值/返回。不做什么：真实并发调度、宿主能力、格式化。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | PH-16 的 `Value`/`ExecOutcome`/管道；PH-15 的 `FnTable`；`positive/run/{control,parallel,call}`。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `17`（目标产品版本 `0.17.0`）。 |
| 已知风险 | 函数返回值二选一、分支内 `$` 成环、break 跨场域；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| `if/else-if/else` 用 truthy，不参与管道 | 不做线程/进程调度 |
| `each`：null 0 次、空数组 0 次、非数组 1 次；失败位为 null 且继续 | 不做流式迭代 |
| `break` 顶层/管道/块三场域；带值可捕捉 | 不做异常/try |
| `parallel` 分支 `$`、结果数组、`[results]` 只允许块级 | 不做取消/超时 |
| `//fn` 名字匹配、参数去重、默认值仅尾部、返回最后一条语句段输出 | 不做递归/闭包 |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `ct/src/eval/eval.h.ct`（控制流分区） | if/each/break：truthy、场域、each 结果数组 |
| `ct/src/eval/eval.h.ct`（并行分区） | 并行分支三态与 `[results]` |
| `ct/src/eval/eval.h.ct`（函数分区） | 参数绑定、默认值、返回 |
| `docs/reviews/diff/PH-17.md` | 本阶段差异报告 |

> 路径修订（PH-17 首个实现提交前）：原卡写 `eval_control.m.ct` 等，但 `.m.ct` 是映射单元，
> 不产产物且不能定义函数（实测 `a .m.ct unit cannot define a function`）。多单元化后求值域
> 落在 `ct/src/eval/eval.h.ct` 一个单元内分三区，理由见 `docs/phases/pending/ct-multiunit.md` §1。

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-17-T1 | `ct/src/eval/eval.h.ct`（if） | `feat(ct): PH-17-T1 if 控制流` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --show positive/run/control/if-subject` | S | E-2 |
| PH-17-T2 | `ct/src/eval/eval.h.ct`（each） | `feat(ct): PH-17-T2 each 遍历` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --show positive/run/control/each-round-failure` | M | E-3 |
| PH-17-T3 | `ct/src/eval/eval.h.ct`（break） | `feat(ct): PH-17-T3 break 场域` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --show positive/run/control/break-pipe` | M | E-4 |
| PH-17-T4 | `ct/src/eval/eval.h.ct`（parallel） | `feat(ct): PH-17-T4 parallel 与 results` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --show positive/run/parallel/three-state` | M | E-5 |
| PH-17-T5 | `ct/src/eval/eval.h.ct`（fn） | `feat(ct): PH-17-T5 fn 绑定与返回` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --show positive/run/call/return-last` | M | E-6 |
| PH-17-T6 | `docs/reviews/diff/PH-17.md` | `docs(diff): PH-17-T6 控制流差异报告` | `git revert <sha>` | `python3 tools/diff/diff.py --layer eval` | S | E-1,E-7,E-8 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | `positive/run/{control,parallel}` 9 个用例通过 | 子集复跑退出 0 |
| E-2 | `if` 用 truthy，`[ok]` 用 `ok`，两者不混 | `control/if-subject` + `segment/success-ok` |
| E-3 | each 空数组/null 0 次、非数组 1 次；某轮失败后继续 | 计数与结果数组逐位断言 |
| E-4 | break 只中断当前场域；带值可被捕捉 | `control/break-pipe` 轨迹 |
| E-5 | parallel 分支三态与 `[results]` 数组顺序正确 | `parallel/three-state`、`results-array` |
| E-6 | 函数去重参数、默认值仅尾部、返回最后一条语句 | `call/return-last`、`call/defaults` |
| E-7 | eval 层对拍 19/19，0 未解释差异 | `docs/reviews/diff/PH-17.md` |
| E-8 | 任务清单每项可独立验收（T-6） | 收口对照表逐项贴 `verify` 原始输出 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | PH-16 的 `ExecOutcome`、管道、`Value` 释放；PH-15 的 `FnTable` 只读接口；run golden。 |
| 风险 1 | 返回值二选一：固定为“最后一条语句段输出”，与 Python 一致。触发信号：golden 两种结果。 |
| 风险 2 | 分支内 `$` 取最终数组：成环。触发信号：分支读到自己未完成的结果。 |
| 风险 3 | break 跨场域：块内 break 中断整个 program。触发信号：轨迹越界。 |
| 风险 4 | parallel 用真实线程导致顺序不稳：本层先按源序串行模拟，接口留并发位。触发信号：结果数组顺序抖动。 |

## 6. 收口与 tag

- 收口附 `docs/reviews/diff/PH-17.md` 与 `docs/reviews/closeout-17.md`。
- 版本 `0.17.0`；tag 按 `docs/phases/README.md` §4，本卡不自动打 tag、不 push。
- 收口后 PH-19 才可开工；PH-20 可并行前半程。
