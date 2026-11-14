# PH-6 立项卡：值模型与 `{value, ok}`（Runtime 轨）

> 状态：正常开卡。体系见 `docs/phases/README.md`。
> 对齐：`docs/planning/rill-0.1.0-phase-plan.md` phase 6；roadmap phase 6「值模型、`{value, ok}`、`$` 基准」。
> 规范版本快照：`1.9.0`。语言规范：`docs/RILL-0.1.0.md`（0.1.1，只读）。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-6`，目录 `docs/phases/PH-6/` |
| 目标 | 定义运行时值、成败通道、truthy/falsy 与 `$` 基准模型，用 fake 工具，不接真实系统。 |
| 范围 | 做什么：`Value`、`ExecOutcome`、truthy/falsy、默认错误、`$` 三种指代、`Bytes/Opaque`、`exit_code` 钩子。不做什么：尾随块顺序、管道、each/parallel、真实宿主。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | PH-3 的 AST；PH-1 的 fake 资产形状。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `6`（收口目标产品版本 `0.6.0`）。 |
| 已知风险 | `ok` 与 truthy 混淆；`Bytes/Opaque` 后补会改运行时核心；`host_meta` 混入 `$`；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| `Value`：STRING/NUMBER/数组/对象/null/bool，预留 `Bytes`/`Opaque` | 不让 OS 类型进入 AST |
| `ExecOutcome{value, ok, error, host_meta?}`；`[ok]` 只看 `ok` | 不实现尾随块触发顺序（PH-7） |
| truthy/falsy：null/false/0/空串/空数组/空对象为 false | 不实现 `if` 控制流（PH-8） |
| `$` 三种指代：语句结果 / `$name` / `.字段` / self | 不做 each/parallel 的 `$` 场域（PH-8/PH-9） |
| 默认错误 `break "RILL DSL ERROR"`；`exit_code` 只留钩子 | 不写死退出码数字，不接真实进程 |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `src/rill/value.py` | 值类型与 `Bytes/Opaque` |
| `src/rill/result.py` | `ExecOutcome`、`ok` 通道、默认错误 |
| `src/rill/verbs.py` | fake VerbRegistry（只返回可编程结果） |
| `tests/test_value.py` | 值模型与 truthy/falsy 单测 |
| `tests/test_result.py` | `ok` 传播、错误串、`host_meta` 单测 |
| `tests/test_truthy.py` | falsy 集合与 `$` 基准单测 |
| `tests/test_verbs.py` | fake VerbRegistry 与默认错误单测 |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-6-T1 | `src/rill/value.py` | `feat(runtime): PH-6-T1 值类型` | `git revert <sha>` | `python3 -m unittest discover -s tests -p 'test_value*.py'` | M | E-5 |
| PH-6-T2 | `src/rill/result.py` | `feat(runtime): PH-6-T2 ok 通道` | `git revert <sha>` | `python3 -m unittest discover -s tests -p 'test_result*.py'` | M | E-2,E-6 |
| PH-6-T3 | `src/rill/value.py`（truthy/falsy 与 `$` 基准） | `feat(runtime): PH-6-T3 truthy 与美元基准` | `git revert <sha>` | `python3 -m unittest discover -s tests -p 'test_truthy*.py'` | M | E-1,E-4 |
| PH-6-T4 | `src/rill/verbs.py` | `feat(runtime): PH-6-T4 fake VerbRegistry` | `git revert <sha>` | `python3 -m unittest discover -s tests -p 'test_verbs*.py'` | S | E-3,E-7 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | 单测覆盖 6 个 falsy 值 + 非空值 | 测试枚举 7 个用例全绿 |
| E-2 | `ok == true` 且 `value == ""` 时 `[ok]` 仍触发 | `test_result` 断言只看 `ok` |
| E-3 | 默认错误串稳定；顶层失败不继续下一条语句 | 错误串逐字断言 + 轨迹用例 |
| E-4 | `$` 在无介宾语句中可观察 | `test_truthy` 的 `$` 断言 |
| E-5 | `Bytes`/`Opaque` 可构造、可透传，不被 truthy/falsy 误判 | `test_value` 断言 |
| E-6 | `ExecOutcome.exit_code` 钩子存在；Agent 可为空、Shell 可映射 | 接口存在性断言 |
| E-7 | 任务清单每项可独立验收（T-6） | 收口对照表逐项贴 `verify` 原始输出 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | PH-3 的 AST；`testdata/0.1.0/fakes/tools.json` 的 fake 工具形状；`ExecOutcome` 字段与 PH-10/PH-11 的接口约定。 |
| 风险 1 | `ok` 与 truthy 混淆：`[ok]` 只看 `ok`，`if` 才看 truthy。触发信号：空串成功被 `[ok]` 跳过。 |
| 风险 2 | `Bytes/Opaque` 后补：会在 Shell 接入时改运行时核心。触发信号：PH-10 需要新增 `Value` 变体。 |
| 风险 3 | `host_meta` 进入 `$`：破坏规范“`$` 是 value 或错误串”。触发信号：`$` 出现结构化字段。 |

## 6. 收口与 tag

- 收口时产品版本 `0.6.0`；annotated tag `v0.6.0`，message 含 `PH-6` 与收口提交 sha 前 7 位。
- 只推 tag，不推分支、不对外发布。收口对照表：`docs/reviews/closeout-6.md`（收口时新建）。
