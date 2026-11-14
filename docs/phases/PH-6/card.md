# PH-6 立项卡：值模型与 `{value, ok}`（Runtime 轨）

> 状态：正常开卡。体系见 `docs/phases/README.md`。
> 对齐：`docs/planning/rill-0.1.0-phase-plan.md` phase 6；roadmap phase 6「值模型、`{value, ok}`、`$` 基准」。
> 规范版本快照：`1.9.0`。语言规范：`docs/RILL-0.1.0.md`（0.1.1，只读）。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-6`，目录 `docs/phases/PH-6/` |
| 目标 | 定义运行时值、成败通道、truthy/falsy、`$` 基准与 `\|>` 值传播模型，用 fake 工具，不接真实系统。 |
| 范围 | 做什么：`Value`、`ExecOutcome`、truthy/falsy、默认错误、`$` 三种指代、`Bytes/Opaque`、`exit_code` 钩子、`expr`/`simple_stmt` 两条管道的值传播、each 轮结果归约。不做什么：尾随块调度、AST 求值器、真实宿主。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | PH-3 的 AST；PH-1 的 fake 资产形状。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `6`（收口目标产品版本 `0.6.0`）。 |
| 已知风险 | `ok` 与 truthy 混淆；`Bytes/Opaque` 后补会改运行时核心；`host_meta` 混入 `$`；管道与尾随块边界混淆；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| `Value`：STRING/NUMBER/数组/对象/null/bool；`Bytes`/`Opaque` 最小不可变包装 | 不让 OS 类型进入 AST；不定义二进制/流的具体 IO |
| `ExecOutcome{value, ok, error, host_meta?, exit_code?}`；`[ok]` 只看 `ok`；`$` 投影忽略 `host_meta` | 不实现尾随块触发顺序（PH-7） |
| truthy/falsy：null/false/0/`""`/`[]`/`{}` 为 false | 不实现 `if` 控制流（PH-8） |
| `$` 基准：无介宾语句 = `value`；失败 = 错误串；`.字段` 只读现有键 | 不做 each/parallel 的 `$` 场域（PH-8/PH-9） |
| `|>` 值传播：只传 `value`；段成功 → 下一跳；未处理失败 → 短路（§4.6） | 不做 AST 求值器与尾随块执行（PH-7） |
| each 轮结果归约：失败轮记 `null` 并继续；each 级 `[error]` 取首个失败轮（§4.13） | 不做真实遍历调度（PH-8） |
| fake VerbRegistry：队列 + default，耗尽后取 default | 不接真实工具、文件系统或网络 |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `src/rill/value.py` | 值类型、`Bytes`/`Opaque`、truthy/falsy |
| `src/rill/result.py` | `ExecOutcome`、`ok` 通道、默认错误、`$` 投影、顶层失败轨迹 |
| `src/rill/verbs.py` | fake VerbRegistry（队列 + default） |
| `src/rill/pipe.py` | `expr`/`simple_stmt` 管道值传播、each 轮结果归约（§4.6、§4.13） |
| `tests/phase6/test_value.py` | 值类型与 `Bytes/Opaque` 单测 |
| `tests/phase6/test_result.py` | `ok` 通道、错误串、`exit_code`、顶层轨迹单测 |
| `tests/phase6/test_truthy.py` | falsy 集合与 `$` 基准单测 |
| `tests/phase6/test_verbs.py` | fake VerbRegistry 单测 |
| `tests/phase6/test_pipe.py` | `expr`/`stmt` 两条管道与 each 归约单测 |
| `docs/reviews/phase6-red.md` | 逐任务红证（baseline、命令、原始输出、退出码） |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-6-T1 | `src/rill/value.py`（值类型与 `Bytes/Opaque`） | `test(runtime): PH-6-T1 红` → `feat(runtime): PH-6-T1 值类型` | `git revert <feat-sha> <test-sha>` | `python3 tests/phase6/test_value.py` | M | E-5 |
| PH-6-T2 | `src/rill/result.py`（`ExecOutcome`、`ok`、默认错误、顶层轨迹） | `test(runtime): PH-6-T2 红` → `feat(runtime): PH-6-T2 ok 通道` | `git revert <feat-sha> <test-sha>` | `python3 tests/phase6/test_result.py` | M | E-2,E-3,E-6 |
| PH-6-T3 | `src/rill/value.py`（truthy/falsy）+ `src/rill/result.py`（`$` 投影） | `test(runtime): PH-6-T3 红` → `feat(runtime): PH-6-T3 truthy 与美元基准` | `git revert <feat-sha> <test-sha>` | `python3 tests/phase6/test_truthy.py` | M | E-1,E-4 |
| PH-6-T4 | `src/rill/verbs.py` | `test(runtime): PH-6-T4 红` → `feat(runtime): PH-6-T4 fake VerbRegistry` | `git revert <feat-sha> <test-sha>` | `python3 tests/phase6/test_verbs.py` | S | E-11 |
| PH-6-T5 | `src/rill/pipe.py`（两条管道与 each 归约） | `test(runtime): PH-6-T5 红` → `feat(runtime): PH-6-T5 管道值传播` | `git revert <feat-sha> <test-sha>` | `python3 tests/phase6/test_pipe.py` | M | E-7,E-8,E-9,E-10 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | 单测覆盖 6 个 falsy 值 + 非空值 | `test_truthy` 枚举 7 个用例全绿 |
| E-2 | `ok == true` 且 `value == ""` 时 `[ok]` 仍触发 | `test_result` 断言只看 `ok` |
| E-3 | 默认错误串稳定；顶层失败不继续下一条语句 | 错误串逐字断言 + `run_top_level` 轨迹用例 |
| E-4 | `$` 在无介宾语句中可观察，且不含 `host_meta` | `test_truthy` 的 `$` 断言 |
| E-5 | `Bytes`/`Opaque` 可构造、可透传，不被 truthy/falsy 误判 | `test_value` 断言 |
| E-6 | `ExecOutcome.exit_code` 钩子存在；Agent 可为空、Shell 可映射 | `test_result` 的接口存在性断言 |
| E-7 | 任务清单每项可独立验收（T-6） | 收口对照表逐项贴 `verify` 原始输出 |
| E-8 | `expr` 管道与 `simple_stmt` 管道各有用例，值传播规则分开断言 | `test_pipe` 两个独立用例 |
| E-9 | each 轮失败按 §4.13 记 `null` 并继续；each 级 `[error]` 取首个失败轮 | `test_pipe` 的轮结果数组与状态断言 |
| E-10 | `\|>` 只传 `value`，未处理失败短路；`[error]` 处理后继续 | `test_pipe` 的下游计数与交付值断言 |
| E-11 | fake VerbRegistry 只返回可编程结果，队列耗尽取 default | `test_verbs` 的队列/default 断言 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | PH-3 的 AST；`testdata/0.1.0/fakes/tools.json` 的 fake 工具形状；`ExecOutcome` 字段与 PH-10/PH-11 的接口约定。 |
| 风险 1 | `ok` 与 truthy 混淆：`[ok]` 只看 `ok`，`if` 才看 truthy。触发信号：空串成功被 `[ok]` 跳过。 |
| 风险 2 | `Bytes/Opaque` 后补：会在 Shell 接入时改运行时核心。触发信号：PH-10 需要新增 `Value` 变体。 |
| 风险 3 | `host_meta` 进入 `$`：破坏规范“`$` 是 value 或错误串”。触发信号：`$` 出现结构化字段。 |
| 风险 4 | 管道与尾随块边界混淆：`expr` 管道不允许尾随块，`simple_stmt` 管道每跳可带 `[ok]/[error]`；混用会把 PH-7 的调度提前塞进值模型。触发信号：`pipe.py` 出现语句执行或块遍历。 |
| 风险 5 | 把 each 轮失败读成“整体失败”：§4.13 是失败轮记 `null` 并继续，只有未处理的 each 级失败才中断。触发信号：首轮失败后结果数组长度不足。 |

## 6. 收口与 tag

- 收口时产品版本 `0.6.0`；annotated tag `v0.6.0`，message 含 `PH-6` 与收口提交 sha 前 7 位。
- 只推 tag，不推分支、不对外发布。收口对照表：`docs/reviews/closeout-6.md`（收口时新建）。

## 7. 复核记录（2026-11-15，baseline `1fde2fe`）

开工前复核 §2–§4，修正如下；§3/§4 在首个实现提交后按 §6.2 冻结。

1. **原 verify 不可失败**：`python3 -m unittest discover -s tests -p 'test_value*.py'` 在测试文件不存在时 `Ran 0 tests` 仍退出 0。改为显式 `python3 tests/phase6/test_*.py`，文件不存在即退出非 0。
2. **测试路径**：从 `tests/test_*.py` 移到 `tests/phase6/`，与 PH-3 的目录约定一致，避免全局 discover 把不同 phase 混跑。
3. **新增 T5 `src/rill/pipe.py`**：原卡把 `|>` 整体排除，但 `expr` 与 `simple_stmt` 两条管道的值传播必须分别写清并各有用例；本 phase 只做值传播模型，不做 AST 求值器与尾随块调度。
4. **扩 §0/§1**：明确 `Bytes/Opaque` 在本 phase 定最小形状；each 只做轮结果归约，不做遍历调度。
5. **新增 E-8…E-11**，并把 E-7 的 T-6 显式写进判据。
6. **规范定位更正**：§4.16–§4.18 是引号/转义、`//map`、`//fn`；值语义实际在 §4.6、§4.8、§4.10–§4.13、§4.15。本卡按后者落地。

**三个已知坑的处置：**

- **`expr` vs `simple_stmt` 的 `|>`**：传输规则同取 §4.6（只传 `value`、失败短路）；差别在每跳单位与尾随块消费 `ok` 的能力（§4.10/§4.11、§4.12）。`pipe.py` 用两套 hop 分开建模，`test_pipe` 各一个用例。
- **each 轮失败**：§4.13 已写死“轮内未处理失败 → 该元素记 `null`，循环继续；each 级 `[error]` 取第一个失败轮”。按规范实现，不登记为缺口。
- **`{value, ok}` 传输**：§4.6 已写死“只传 `value`，不传二元组；段尾 `ok` 假且无 `[error]`，或 `[error]` 内 break → 中断管道”。按规范实现；三种备选的后果记在 §8，不挑规范外的实现。

## 8. 规范缺口与实现契约

只登记，不改 `docs/RILL-0.1.0.md` 正文。

| # | 位置 | 缺口 | PH-6 落地 |
| --- | --- | --- | --- |
| 1 | §五 / roadmap §3.3 | `Bytes` / `Opaque` 的字段形状与比较语义未定义 | 最小不可变包装 `Bytes(data)`、`Opaque(handle, kind)`；两者都不进入 falsy 集合，按“其余一切 truthy”处理 |
| 2 | §4.8 / §4.12 | `$` 的 `.字段` 在键缺失时的行为未定义 | 缺失键抛 `KeyError`，不静默返回 `null`；`test_truthy` 只断言现有键 |
| 3 | §4.10 / §4.8 | `host_meta` 的归属未写；只说 `$` 是 value 或错误串 | `host_meta` 只留在 `ExecOutcome`，`$` 投影不包含它 |
| 4 | §4.6 | 顶层语句的首跳隐式输入未定义（只说“前一步输出”） | `run_pipe(start_value, hops)` 由调用方给 `start_value`；PH-6 不写死首跳来源，留给 PH-7 |
| 5 | §4.6 | 三种 `{value, ok}` 传输备选未逐一比较 | 规范已选“只传 value + 未处理失败短路”；另两种（传二元组、失败继续传 value）记为被排除路径，不实现 |
| 6 | §4.11 / §4.12 | `expr` 管道无尾随块，因此不能消费 `ok`；规范未单独说明两条管道的值语义差异 | 传输核心共用 `advance`；`expr` hop 不允许尾随块，失败即短路；`stmt` hop 允许 `[ok]/[error]` 先消费再交给 `advance` |
| 7 | §4.13 | each 块输出在 each 级 `[error]` 处理后是否仍为结果数组，未单独写 | 按 §4.11“段输出 = `[error]` 执行后 `$` 的最终值”处理；each 结果数组只在未处理失败时作为中间值保留 |
