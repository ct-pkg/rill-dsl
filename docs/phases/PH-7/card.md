# PH-7 立项卡：简单语句、尾随块与段输出（Runtime 轨）

> 状态：正常开卡。体系见 `docs/phases/README.md`。
> 对齐：`docs/planning/rill-0.1.0-phase-plan.md` phase 7；roadmap phase 7「简单语句、尾随块、段输出」。
> 规范版本快照：`1.9.0`。语言规范：`docs/RILL-0.1.0.md`（0.1.1，只读）。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-7`，目录 `docs/phases/PH-7/` |
| 目标 | 实现 `simple_stmt` 的完整执行顺序：`[into]` → `[ok]/[error]` → 段输出 → 管道下游。 |
| 范围 | 做什么：`[into]` 顺序与失败、`[ok]/[error]` 触发与 `$`、4 种段输出、`[into]` 三种形式、`->$x` 顺序。不做什么：`if`/`each`/`parallel` 控制流、真实宿主。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | PH-6 的 `Value`/`ExecOutcome`；PH-3 的 AST；PH-4 的表只读接口。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `7`（收口目标产品版本 `0.7.0`）。 |
| 已知风险 | `[into]` 失败是否走用户 `[error]`；后续 `[into]` 是否执行；`[ok]` 的 `$` 取值；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| `[into]` 按书写顺序执行并修改 `$`；后续 `[into]` 看到前一个结果 | 不做 `if`/`each`/`parallel` 的场域 |
| `[into]` 失败视为段失败，走用户 `[error]`；无 `[error]` 默认 break | 不做多语句组合与管道分段（PH-8） |
| `[ok]/[error]` 在 `[into]` 之后按 `ok` 触发 | 不做 parallel 汇合 |
| 4 种段输出：成功无/有 `[ok]`、失败无/有 `[error]` | 不做格式化 |
| `[into]` 尾随/普通介词/独立 `prep_block_stmt`；`->$x` 按 AST 顺序 | 不改 parser 的归约结果 |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `src/rill/eval_simple.py` | 单语句执行、段输出、尾随块 |
| `src/rill/fakes.py` | 把 `--fakes` 的 `tools.json` 装成 `FakeVerbRegistry` |
| `src/rill/cli.py` | `rill run --profile shell --fakes <path>` 的最小入口 |
| `tests/phase7/` | 每条任务一个显式脚本断言（`python3 tests/phase7/test_*.py`） |
| `testdata/0.1.0/positive/run/` | 4 种段输出、`[into]` 顺序与失败、管道下游用例 |
| `testdata/0.1.0/expected/run/` | 轨迹 golden（输出顺序与 `$` 观察值） |
| `docs/reviews/phase7-red.md` | 红证存档（baseline / 命令 / 退出码 / 原始输出） |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-7-T1 | `src/rill/eval_simple.py`（`[into]` 顺序与失败） | `feat(runtime): PH-7-T1 into 语义` | `git revert <sha>` | `python3 tests/phase7/test_into.py` | M | E-2,E-3 |
| PH-7-T2 | `src/rill/eval_simple.py`（`[ok]/[error]` 与 `$`） | `feat(runtime): PH-7-T2 ok 与 error 块` | `git revert <sha>` | `python3 tests/phase7/test_ok_error.py` | M | E-4 |
| PH-7-T3 | `src/rill/eval_simple.py`（4 种段输出与管道下游） | `feat(runtime): PH-7-T3 段输出` | `git revert <sha>` | `python3 tests/phase7/test_segment.py` | M | E-1,E-5 |
| PH-7-T4 | `src/rill/fakes.py` + `src/rill/cli.py`（run 入口） | `feat(runtime): PH-7-T4 run 子命令` | `git revert <sha>` | `python3 tests/phase7/test_run_cli.py` | S | E-6 |
| PH-7-T5 | `src/rill/eval_simple.py`（独立 `[into]` 与 `->$x` 顺序） | `feat(runtime): PH-7-T5 into 三形式与赋值顺序` | `git revert <sha>` | `python3 tests/phase7/test_forms.py` | M | E-2,E-6 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | 4 种段输出各 1 个 golden | `expected/run/` 四个文件全绿 |
| E-2 | `[into]` 失败 + 用户 `[error]` 的执行轨迹唯一 | 轨迹 golden 与源码顺序一致 |
| E-3 | 多 `[into]` 失败时后续不执行 | 轨迹里后续 `[into]` 无输出 |
| E-4 | `[ok]` 的 `$` 是最终值，`[error]` 的 `$` 是错误串 | 两条断言逐字比对 |
| E-5 | 管道下游只收到 value，`ok` 不向下传 | 段间 golden 断言下游输入 |
| E-6 | 任务清单每项可独立验收（T-6） | T1–T5 各自的 verify 命令能单独失败、单独转绿；收口对照表逐项贴原始输出 |

## 4.1 验证口径

- verify 必须是**能真失败**的断言命令；`--show` 只打印，不得作为 verify。
- `tests/phase7/test_*.py` 以退出码 0 表示通过，缺失实现时必须以非 0 退出。
- run 类用例的最终事实以 `bash tools/check-0.1.0.sh --kind run --bucket positive` 为准；T3 的 verify 先跑脚本断言，收口时再跑整桶。

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | PH-6 的 `ExecOutcome` 与 truthy；PH-3 的 `trailing_block` 数量约束；PH-4 的表接口。T4 的 run 入口依赖 T1–T3；段输出是 PH-8 管道/控制流的前置，PH-8 不得绕过这里另立一套。 |
| 风险 1 | `[into]` 失败是否走用户 `[error]`：两条路会改变轨迹。触发信号：E-2 出现两种输出顺序。 |
| 风险 2 | 后续 `[into]` 执行：失败后仍执行会让副作用翻倍。触发信号：E-3 出现第二个 `[into]` 输出。 |
| 风险 3 | `[ok]` 的 `$` 取初始值而非最终值。触发信号：E-4 的 `$` 与 `[into]` 结果不一致。 |

## 6. 收口与 tag

- 收口时产品版本 `0.7.0`；annotated tag `v0.7.0`，message 含 `PH-7` 与收口提交 sha 前 7 位。
- 只推 tag，不推分支、不对外发布。收口对照表：`docs/reviews/closeout-7.md`（收口时新建）。

## 8. 规范缺口与实现裁定（不改变规范正文）

下列各条在规范里没有唯一表述。实现取一种可验证的做法，但**不把裁定写成规范**；后续 CR 需要逐条收口。

| # | 位置 | 缺口 | 本 phase 的实现裁定 |
| --- | --- | --- | --- |
| 1 | §4.11 段输出 | “有介宾时为 `$` 当前值”的“介宾”没有界定：是普通介词短语（`[to]` 等），还是包括尾随 `[into]` | 只有执行过 `[into]` 才把段输出改为 `$` 当前值；普通介词短语不改变输出 |
| 2 | §4.11 多 `[into]` | “后续 `[into]` 看到前一个结果”未说“结果”是块最终 `$` 还是块段输出 | 取块执行后的最终 `$` |
| 3 | §4.11 + 评审 R-25 | `->$x` 与 `[ok]/[error]` 的书写顺序冲突：§4.11 固定 into 先于 ok/error，R-25 要求按 AST 顺序 | `Assign` 与 `[into]` 按 AST 顺序执行；`[ok]/[error]` 延后到所有 `[into]` 之后 |
| 4 | §4.9 独立形式 | `[into] $cfg { ... }` 执行后是否把块内最终 `$` 写回 `$cfg` 未写 | 写回 `$cfg` |
| 5 | §三 `prep_block_stmt` | 独立 `[ok]` / `[error]` 块没有前置 `{value, ok}`，触发条件未定义 | 本 phase 不执行；遇到时报 `E-RUN-UNSUPPORTED`，留给后续 CR |
| 6 | §4.6 / §4.11 | `[error]` 处理且未 break 后，顶层 `run` 的 `ok` 取什么没有写死 | 取 handled：`ok=true`，`value` 为 `[error]` 块最终 `$` |
| 7 | §六 示例 1 | `.database [into] { ... }` 用 `.字段` 直接作语句头，不在 §三 `statement` 产生式内 | 登记，不实现；parser 目前也不接受该形态 |
| 8 | §4.15 `break` | `break` 穿出顶层后 `run` 的返回形状（ok / value / `->$x`）未定义 | 顶层捕获 break：`ok=true`，`value` 为 break 值，有 `->$x` 时写入变量 |
