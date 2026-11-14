# PH-4 立项卡：加载期校验与诊断（Parser 轨）

> 状态：正常开卡。体系见 `docs/phases/README.md`。
> 对齐：`docs/planning/rill-0.1.0-phase-plan.md` phase 4；roadmap phase 4「加载期校验与诊断」。
> 规范版本快照：`1.9.0`。语言规范：`docs/RILL-0.1.0.md`（0.1.1，只读）。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-4`，目录 `docs/phases/PH-4/` |
| 目标 | 在 AST 之后、执行之前完成 map/fn/verb 表与名字校验，按 profile 选择 principal，不执行。 |
| 范围 | 做什么：`MapTable`/`FnTable`/`VerbTable`、`check` 入口、`E-LOAD-*`、`W-01`、错误行列。不做什么：运行期 `{value, ok}`、段输出、真实工具调用、函数绑定求值、类型/角色校验（无注册表载体，见 §8）。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | PH-3 的 AST 与错误位置；PH-1 的 `HostProfile` 形状与 `profiles/*.json`。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `4`（收口目标产品版本 `0.4.0`）。 |
| 已知风险 | 调用绑定不得塞进 parser；`principal` 不得把 role 设成必填；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| `//map`：同块重复短词报错；短词字符集与标记符已由词法守 | 不做展示态格式化（PH-5）；可见链最近绑定/反向映射留给 PH-5 |
| `//fn`：名字精确匹配、未声明函数报错 | 不做默认值/arity 校验（parser 未归约 `?`，见 §8）；不做函数调用求值（PH-9） |
| `arg := value` 只作为调用实参参与名字校验 | 不把调用绑定塞进 parser |
| 按 `--profile` 选 principal：shell → OS 用户、agent → 角色表；role 非必填 | 不校验 TypeRegistry/RoleRegistry（无载体，见 §8） |
| `[results]` / `[ok]` / `[error]` 已由 parser 守；`W-01` 在解析期记录、`check` 输出 | 不执行任何工具 |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `src/rill/loader.py` | MapTable/FnTable/VerbTable、名字校验、profile 选择、`LoadError` |
| `src/rill/cli.py` | `rill check <file> --profile shell\|agent`；`parse --dump-ast` 输出不变 |
| `src/rill/parser.py` | `parse_with_warnings`：保留 `[in]` 裸词来源，供 `W-01` |
| `testdata/0.1.0/negative/load/` | 3 条加载期负例（`code/line/col` 断言） |
| `testdata/0.1.0/positive/check/` | 双 profile 正例与 `W-01` 警告用例 |
| `tools/rill_harness/` | `--case` 过滤与 `check` kind（双 profile 正例断言） |
| `tests/phase4/test_no_exec.py` | 加载期不执行工具的结构断言 |
| `docs/reviews/phase4-red.md` | 逐任务红证（baseline、命令、原始输出、退出码） |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-4-T1 | `src/rill/loader.py`（加载期入口、MapTable、`LoadError`）+ `src/rill/cli.py`（`check`） | `test(loader): PH-4-T1 红` → `feat(loader): PH-4-T1 加载期入口与 MapTable` | `git revert <feat-sha> <test-sha>` | `bash tools/check-0.1.0.sh --case negative/load/map-duplicate-short` | M | E-1,E-2,E-5 |
| PH-4-T2 | `src/rill/loader.py`（FnTable 与调用绑定） | `test(loader): PH-4-T2 红` → `feat(loader): PH-4-T2 未声明函数校验` | `git revert <feat-sha> <test-sha>` | `bash tools/check-0.1.0.sh --case negative/load/unknown-function` | M | E-1,E-2 |
| PH-4-T3 | `src/rill/loader.py`（VerbTable 与 profile 选择）+ `testdata/0.1.0/positive/check/host-profiles` | `test(loader): PH-4-T3 红` → `feat(loader): PH-4-T3 未知动词与 profile` | `git revert <feat-sha> <test-sha>` | `bash tools/check-0.1.0.sh --case negative/load/unknown-verb --case positive/check/host-profiles` | M | E-1,E-2,E-4 |
| PH-4-T4 | `src/rill/parser.py`（`parse_with_warnings`）+ `src/rill/cli.py`（`check` 输出 warnings） | `test(loader): PH-4-T4 红` → `feat(loader): PH-4-T4 W-01 提示` | `git revert <feat-sha> <test-sha>` | `bash tools/check-0.1.0.sh --case positive/check/each-bareword-w01` | S | E-1,E-3,E-6 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | 4 条 PH-4 用例全部 PASS（3 条 load 负例 + `W-01` 正例） | `bash tools/check-0.1.0.sh --phase p4` 退出 0 |
| E-2 | 3 条 load 负例有稳定错误码，行列指向具体成分 | `bash tools/check-0.1.0.sh --phase p4 --kind error --bucket negative` 退出 0，逐条断言 `code/line/col` |
| E-3 | `W-01` 在 `each $f [in] xs` 上触发且不阻断 | `bash tools/check-0.1.0.sh --case positive/check/each-bareword-w01` 退出 0，`warnings[]` 含 `W-01` |
| E-4 | 同一正例在 shell / agent 下 `check` 均通过，role 非必填 | `bash tools/check-0.1.0.sh --case positive/check/host-profiles` 退出 0 |
| E-5 | 加载期不执行任何工具 | `python3 tests/phase4/test_no_exec.py` 退出 0（结构断言：loader 无执行类 API，`check` 无 fakes 入口） |
| E-6 | 任务清单每项可独立验收（T-6） | 收口对照表逐项贴 `verify` 原始输出 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | PH-3 的 AST 与 span；`profiles/shell.json`、`profiles/agent.json` 同形；`testdata/0.1.0/negative/load/` 现有 3 个负例。 |
| 风险 1 | 把调用绑定塞进 parser：会让 PH-3 提前承担 PH-9 的语义。触发信号：PH-3 的 AST 出现实参绑定结果。 |
| 风险 2 | role 设成必填：Shell profile 无角色，`check` 会全红。触发信号：`--profile shell` 报缺 role。 |
| 风险 3 | 无 TypeRegistry/RoleRegistry 载体：PH-4 不做类型/角色校验，`.env` 字段歧义不在本阶段触发；触发信号：有人把类型拆分写进 loader 或 AST。 |
| 风险 4 | `W-01` 阻断：警告不得改变退出码。触发信号：`--kind warning` 退出非 0。 |
| 风险 5 | 错误行列取自 AST `span`（调用/语句起始），不是原始 token：改 AST 需同步 §8 的位置约定。 |

## 6. 收口与 tag

- 收口时产品版本 `0.4.0`；annotated tag `v0.4.0`，message 含 `PH-4` 与收口提交 sha 前 7 位。
- 只推 tag，不推分支、不对外发布。收口对照表：`docs/reviews/closeout-4.md`（收口时新建）。

## 7. 复核记录（2026-11-15，baseline `19d5cc7`）

开工前复核 §2–§4，修正如下；§3/§4 在首个实现提交后按 §6.2 冻结。

1. **删去 T5（docs/planning/rill-0.1.0-host-contract.md）**：该文件既有，且本阶段明确“只消费、不改形状”；原 verify `test -s` 只判文件存在、不判行为，不满足“能真失败”的要求。profile 消费并入 T3。
2. **verify 从整桶/`--show` 改为 `--case` 精确用例**：`--show` 只打印不判定；整桶会迫使后续任务等前面任务。harness 增加可重复的 `--case` 过滤（T1 红提交），每条 verify 只覆盖本任务用例。
3. **重写 E-1…E-6**：原 E-1 只比 AST，证明不了 `check` 通过；原 E-4 的“只读表接口”没有 fixture，属于为接口造需求；原 E-5 的“fake 计数”没有计数设施。改为可执行命令，并新增 `check` kind + `positive/check/host-profiles` 断言双 profile 正例（T3 红提交）。
4. **删去 `testdata/0.1.0/expected/errors/` 交付物**：错误断言按 `testdata/0.1.0/README.md` §3 写在 `case.json`，该目录没有实际产物。
5. **范围收窄**：默认值/arity、类型/角色前缀拆分不在本阶段落地；原因与去向见 §8，不当实现选择消化。

**`W-01` 裁定：采用 (a)**，在解析期对“出现在 `each … [in]` 右值位的裸词”出提示，语义为“这里按字符串处理，若意图是变量请写 `$xs`”。理由：`W-01` 是 §4.20 冻结的提示，删掉或并入 `E` 级等于擅自改规范判据；裸词的来源只在 token 流里可判，parser 归约为 `STRING` 后无法恢复。落地方式：parser 内部 `parse_with_warnings(tokens)` 在归约前记录，`check` 消费；`parse --dump-ast` 的信封保持不变。不保留 (b)。

## 8. 规范缺口与实现契约

只登记，不改 `docs/RILL-0.1.0.md` 正文。错误码为 PH-4 自定，后续 phase 只能新增，不得改号或改位置语义。

| 编号 | 触发 | 位置 |
| --- | --- | --- |
| `E-LOAD-MAP-DUP-SHORT` | 同一 `//map{}` 内第二个相同短词 | 第二个 `MapEntry` 的短词 |
| `E-LOAD-FN-UNDECLARED` | `@ STRING` 调用的名字不在 `//fn{}` 的 `FnDef` 集合内 | `CallStmt` 的 `@` |
| `E-LOAD-VERB-UNKNOWN` | `VerbCall.verb` 不在 0.1.0 动词集内 | `VerbCall` 的起始（主语或动词） |

| # | 位置 | 缺口 | PH-4 落地 |
| --- | --- | --- | --- |
| 1 | §4.17 重复短词 | 只写“报错”，无错误码与位置 | `E-LOAD-MAP-DUP-SHORT`；位置=第二个短词 |
| 2 | §五.8 未知动词 | 只写加载期报错，未定义 VerbRegistry 的载体/形状；`profiles/*.json` 不声明动词 | 内置 0.1.0 动词集（§六 示例与 `fakes/tools.json` 的 8 个：`read`/`write`/`parse`/`send`/`search`/`replace`/`contains`/`review`）；`E-LOAD-VERB-UNKNOWN` |
| 3 | §4.18 未声明函数 | 无错误码，只要求错误串含函数名 | `E-LOAD-FN-UNDECLARED`；位置=`@`；错误串含函数名 |
| 4 | §4.18 默认值/arity | `$变量?默认值` 的 `?` 在 PH-3 未归约，PH-4 无输入；多余实参行为未定义 | 不校验，登记到 PH-5 或 CR |
| 5 | §4.18 重复函数名 | 未规定同块重名行为 | 不报错也不静默覆盖；表保留按定义顺序的全部名字，登记缺口 |
| 6 | §4.1 / §五 类型与角色 | TypeRegistry/RoleRegistry 无载体；profile 形状不含类型/角色表 | 只按 `--profile` 选 principal 形态（shell → OS 用户，agent → 角色表，role 非必填）；不校验类型/角色 |
| 7 | §4.17 可见链与反向映射 | “同一长词仅保留最近绑定”“反向取首个命中”是展示语义 | 留给 PH-5；PH-4 只查同块重复短词 |
| 8 | §4.20 `W-01` | 未规定 line/col | 位置=`[in]` 右值首个裸词 token；源以 `BARE` 开头且不是 `verb_call` 主语时触发 |
| 9 | PH-3 卡 §8 #9 | 裸词归约成 `STRING` 后来源丢失 | `parse_with_warnings` 在归约前记录；`parse --dump-ast` 输出不变 |
