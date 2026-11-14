# PH-16 立项卡：CT 求值核心（P4）

> 状态：正常开卡。CT 重写轨道第 4 层。体系见 `docs/phases/README.md`，
> 上游 `docs/planning/rill-0.1.0-ct-rewrite-roadmap.md`。语言规范 `docs/RILL-0.1.0.md`（0.1.1，只读）。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-16`，目录 `docs/phases/PH-16/` |
| 目标 | CT 版实现动态 `Value`、`{value, ok}`、`$`、管道与固有动词，跑通简单语句/段输出/管道/调用共 10 个 run 用例。 |
| 范围 | 做什么：tagged union、arena + retain/release、`ok` 通道、`$` 三种指代、管道只传 value、固有动词。不做什么：`if`/`each`/`break`/`parallel`/`//fn`（PH-17），宿主能力（PH-19/20）。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | PH-14 的 AST；PH-15 的只读表接口；`testdata/0.1.0/positive/run/{segment,into,pipe,call}`。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `16`（目标产品版本 `0.16.0`）。 |
| 已知风险 | 所有权与释放、`ok` 与 truthy 混淆、`$` 结构化污染；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| `Value` tagged union：string/number/array/object/null/bool + `Bytes`/`Opaque` | 不让 OS 类型进入 AST |
| arena 生命周期 + 显式 retain/release；单次执行结束统一释放 | 不做 GC、跨进程共享 |
| `ExecOutcome{value, ok, error}`；`[ok]` 只看 `ok` | 不做控制流触发顺序（PH-17） |
| `$`：语句结果 / `$name` / `.字段` / self | 不做 each/parallel 场域（PH-17） |
| 管道只把 value 传给下游；固有动词用 fake 表 | 不做真实进程/文件/网络 |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `ct/src/value.h.ct` | `Value` 定义、构造/销毁、truthy/falsy |
| `ct/src/value.m.ct` | retain/release、arena、深拷贝边界 |
| `ct/src/eval.h.ct` | 简单语句执行接口与 `{value, ok}` |
| `ct/src/eval.m.ct` | 段输出、`$`、尾随块顺序 |
| `ct/src/pipe.h.ct` | 管道接口 |
| `ct/src/pipe.m.ct` | 分段与 value 传递 |
| `ct/src/verbs.h.ct` | 固有动词表（含 fake 注册） |
| `ct/src/verbs.m.ct` | 10 个固有动词实现 |
| `docs/reviews/diff/PH-16.md` | 本阶段差异报告 |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-16-T1 | `ct/src/value.h.ct`、`ct/src/value.m.ct` | `feat(ct): PH-16-T1 Value 与 arena` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --show positive/run/segment/success-plain` | M | E-1,E-2 |
| PH-16-T2 | `ct/src/eval.h.ct`、`ct/src/eval.m.ct` | `feat(ct): PH-16-T2 段输出与 ok 通道` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --show positive/run/into/order` | M | E-2,E-3 |
| PH-16-T3 | `ct/src/pipe.h.ct`、`ct/src/pipe.m.ct` | `feat(ct): PH-16-T3 管道` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --show positive/run/pipe/downstream` | M | E-4 |
| PH-16-T4 | `ct/src/verbs.h.ct`、`ct/src/verbs.m.ct` | `feat(ct): PH-16-T4 固有动词` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --show positive/run/call/defaults` | M | E-1,E-5 |
| PH-16-T5 | `docs/reviews/diff/PH-16.md` | `docs(diff): PH-16-T5 求值差异报告` | `git revert <sha>` | `python3 tools/diff/diff.py --layer eval` | S | E-6,E-7 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | `positive/run/{segment,into,pipe,call}` 共 10 个用例通过 | `--kind run --bucket positive` 的子集复跑 |
| E-2 | `[ok]` 只看 `ok`：空串成功仍触发 | `segment/success-ok` 与 `success-plain` |
| E-3 | `$` 三指代可观察；`host_meta` 不进入 `$` | `into/order` 逐字段断言 |
| E-4 | 管道下游只收 value；上游失败不回溯 | `pipe/downstream`、`pipe/failure-stops` |
| E-5 | `Bytes`/`Opaque` 可透传，不被 truthy 误判 | value 单测 + run 用例 |
| E-6 | eval 层对拍 10/10，0 未解释差异 | `docs/reviews/diff/PH-16.md` |
| E-7 | 任务清单每项可独立验收（T-6） | 收口对照表逐项贴 `verify` 原始输出 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | PH-15 的四表只读接口；PH-14 的 AST；`testdata/0.1.0/expected/run/` 的轨迹 golden。 |
| 风险 1 | 所有权：字符串短词/切片共享缓冲，Value 释放后悬垂。绕法：插入即复制 + arena。触发信号：ASan/valgrind 报 use-after-free。 |
| 风险 2 | `ok` 与 truthy 混淆：`[ok]` 用 `ok`，`if` 用 truthy（PH-17）。触发信号：空串成功被 `[ok]` 跳过。 |
| 风险 3 | 为省事把 `host_meta` 塞进 `$`。触发信号：`$` 出现结构化字段。 |
| 风险 4 | 固有动词直接调 Python：违反“CT 正式实现”定位。触发信号：二进制链接 Python 或起子进程。 |

## 6. 收口与 tag

- 收口附 `docs/reviews/diff/PH-16.md` 与 `docs/reviews/closeout-16.md`。
- 版本 `0.16.0`；tag 按 `docs/phases/README.md` §4，本卡不自动打 tag、不 push。
- 收口后 PH-17 才可开工；PH-19/PH-20 可先定接口。
