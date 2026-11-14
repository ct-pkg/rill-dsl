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
| `src/rill/eval_control.py` | `if` / `each` / `break` 场域与 expr 求值（统一回落到 `eval_simple`） |
| `src/rill/eval_simple.py` | 抽取 `_apply_tail` 供 each 复用；补管道场域；`E-RUN-UNSUPPORTED` 清单收缩 |
| `tests/phase8/` | `support.py`、`test_if.py`、`test_each.py`、`test_break.py`、`test_cases.py` |
| `testdata/0.1.0/positive/run/control/` | 管道/if/each/break 运行用例（`ok=false` 的脚本也放这里） |
| `testdata/0.1.0/expected/run/` | 轨迹 golden（由 `tests/phase8/test_cases.py` 读取） |
| `docs/reviews/phase8-red.md` | 各任务红证与转绿记录 |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-8-T1 | `src/rill/eval_control.py`（`if`：条件四形态、truthy） | `feat(runtime): PH-8-T1 if 条件求值` | `git revert <sha>` | `python3 tests/phase8/test_if.py` | M | E-2 |
| PH-8-T2 | `src/rill/eval_control.py`（`each`）+ `eval_simple._apply_tail` 抽取 | `feat(runtime): PH-8-T2 each 遍历与每轮成败` | `git revert <sha>` | `python3 tests/phase8/test_each.py` | M | E-3,E-4 |
| PH-8-T3 | `src/rill/eval_control.py`（`break` 场域）+ `eval_simple` 管道场域 | `feat(runtime): PH-8-T3 break 场域` | `git revert <sha>` | `python3 tests/phase8/test_break.py` | M | E-5 |
| PH-8-T4 | `tests/phase8/test_cases.py` + `testdata/0.1.0/positive/run/control/` + `expected/run/control-*.json` | `test(runtime): PH-8-T4 轨迹 golden 与 run 用例` | `git revert <sha>` | `python3 tests/phase8/test_cases.py` | S | E-1,E-6 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | 管道 3 段以上，每段 `[error]` 只覆盖本段 | 轨迹 golden 的段边界与错误归属；`control/pipe-three` |
| E-2 | `if` 的 truthy/falsy 与 `[ok]` 的 `ok` 分离；条件四形态（裸值 / 动词调用 / 带主语 / 管道）运行期可归约 | `test_if.py`：空串成功仍走 `[ok]`、`if` 走 falsy；带主语条件断言 `subject` 已求值 |
| E-3 | each null 走 error 且 0 轮、空数组 0 轮、非数组 1 轮 | `test_each.py` 三个轮数断言 |
| E-4 | 某轮失败后循环继续，结果数组对应位为 null；each 级 `[ok]/[error]` 的触发与 `$` | `test_each.py` 逐位比对 + 触发断言 |
| E-5 | `break` 三场域；each 内 break、失败轮后 break、裸词 break 三组合 | `test_break.py` 场域轨迹 + 捕捉断言 |
| E-6 | 任务清单每项可独立验收（T-6） | 收口对照表逐项贴 `verify` 原始输出；`bash tools/check-0.1.0.sh --kind run --bucket positive` |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | PH-7 的段输出、`[into]` 顺序与 `_finish`（管道本体已在 PH-7 落地，PH-8 不重写）；PH-6 的 truthy 与 `$`；PH-3 的 AST。 |
| 显式顺序 | 管道无独立任务：PH-8 只补「expr 位的管道」（`if` 条件、`each` 源）与「管道场域（break 止于管道）」。这两项都压在本卡 T1–T3 上，不能先做。 |
| 风险 1 | each 每轮作用域未固定：会留下“每轮共享 `$`”的二义。触发信号：两轮之间变量可见。 |
| 风险 2 | `$` 被 `[in]` 宾语覆盖：each 体内 `$` 必须是当前项。触发信号：体内 `$` 等于整个数组。 |
| 风险 3 | `break` 跨场域：块内 break 中断整个 program。触发信号：E-5 轨迹越界。 |
| 风险 4 | 管道另立求值路径：expr 位与语句位各写一套。触发信号：`if` 条件里的管道与语句级管道对同一脚本给出不同段边界。 |

## 6. 收口与 tag

- 收口时产品版本 `0.8.0`；annotated tag `v0.8.0`，message 含 `PH-8` 与收口提交 sha 前 7 位。
- 只推 tag，不推分支、不对外发布。收口对照表：`docs/reviews/closeout-8.md`（收口时新建）。

## 8. 规范缺口与实现裁定（不改变规范正文）

下列各条在规范里没有唯一表述。**先实测、再裁定**：裁定只写进本表，不写进
`docs/RILL-0.1.0.md`；后续 CR 需要逐条收口。

| # | 位置 | 缺口 | 本 phase 的实测与裁定 |
| --- | --- | --- | --- |
| 1 | §4.13 + §4.15 | `each` 体内 `break`（非 `[error]` 块）是结束本轮还是结束整个 each | 待 T3 实测后补 |
| 2 | §4.13 | 「某轮失败后 `[error]` 内 `break`」之后：该轮元素算 `null` 还是省略，each 级 `[error]` 是否触发 | 待 T3 实测后补 |
| 3 | §4.13/§4.15 | `break` 的值作为 each 错误串时，裸词按 `STRING` 进入哪一层（each 级 `$` 还是捕捉变量） | 待 T3 实测后补 |
| 4 | §4.12 | `if` 的段输出是什么（无动作的纯判断） | 取命中的分支块输出；块输出 = 进入 if 时的 `$`。无分支命中且无 `else` → 原样返回输入 `$`。实测：`case_falsy_body_uses_dollar`、`case_truthy_falsy_table` |
| 5 | §4.12/§4.10 | `if` 条件求值为失败（动词 `ok=false`、条件管道中断）时的语义 | 条件失败原样返回该失败：不执行任何分支，`ok=false` 且保留宿主错误串（不换成 `RILL DSL ERROR`）。实测：`case_condition_failure_stops_if` |
| 6 | §4.12 | `if` 体内 `$` 指代什么、体内 `break` 是否只中断 `if` | 体内 `$` = 进入 if 时的当前 `$`（顶层为 `null`）。体内 `break` 不在 T1 裁定，见 #1/#10 与 T3 实测 |
| 7 | §4.13 | `each` 源为 `null` 时的错误串；源为失败动词/中断管道时的语义 | `null` 源按默认失败处理，错误串 `RILL DSL ERROR`，0 轮；源 expr 失败（含管道中断）时把该失败交给 each 级 tail（`[error]` 的 `$` = 宿主错误串），0 轮。实测：`case_three_input_shapes` |
| 8 | §4.13 | each 每轮作用域：`$变量` 与外层同名变量的读写关系 | 每轮新建子作用域，`$变量` 与 `$` 都是当前项；轮内 `->$x` 建在轮作用域，不泄漏到块外。实测：`case_round_dollar_and_var_are_item`、`case_round_scope_is_fresh` |
| 9 | §4.13 | each 级 `[into]` 是否存在、收到什么值 | 解析器允许，执行按 §4.11 尾随块处理：收到结果数组。实测：`case_each_into_gets_result_array` |
| 10 | §4.6/§4.15 | 管道段内 `break` 之后，管道场域的段输出与 program 的 `ok` | 待 T3 实测后补 |
