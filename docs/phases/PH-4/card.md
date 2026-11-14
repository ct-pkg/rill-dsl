# PH-4 立项卡：加载期校验与诊断（Parser 轨）

> 状态：正常开卡。体系见 `docs/phases/README.md`。
> 对齐：`docs/planning/rill-0.1.0-phase-plan.md` phase 4；roadmap phase 4「加载期校验与诊断」。
> 规范版本快照：`1.9.0`。语言规范：`docs/RILL-0.1.0.md`（0.1.1，只读）。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-4`，目录 `docs/phases/PH-4/` |
| 目标 | 在 AST 之后、执行之前完成 map/fn 表、名字、默认值、角色/类型前缀与 HostProfile 校验，不执行。 |
| 范围 | 做什么：`MapTable`/`FnTable`/`VerbTable`/`TypeTable`/`HostProfile` 校验、`E-01`/`E-02`/`W-01`、错误行列。不做什么：运行期 `{value, ok}`、段输出、真实工具调用、函数绑定求值。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | PH-3 的 AST 与错误位置；PH-1 的 `HostProfile` 形状与 `profiles/*.json`。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `4`（收口目标产品版本 `0.4.0`）。 |
| 已知风险 | 调用绑定不得塞进 parser；`principal` 不得把 role 设成必填；`.env` 与字段歧义；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| `//map`：短词字符集、标记符、重复短词、可见链最近绑定、长词唯一/反向映射 | 不做展示态格式化（PH-5） |
| `//fn`：名字精确匹配、参数去重顺序、默认值仅尾部、未声明函数 | 不做函数调用求值（PH-9） |
| `arg := value` 实参个数与默认值展开；与 SVO 槽映射分开 | 不把调用绑定塞进 parser |
| 类型/角色前缀的加载期拆分；Shell profile 的 role 可为空 | 不接生产权限/白名单 |
| `[results]` 仅 parallel 块级；`[ok]/[error]` 数量上限；`W-01` 警告 | 不执行任何工具 |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `src/rill/loader.py` | 四张表、名字/arity/默认值、profile 校验 |
| `src/rill/cli.py` | `rill check <file> --profile shell\|agent` |
| `testdata/0.1.0/expected/errors/` | 错误断言格式说明（期望仍写在 `case.json`） |
| `testdata/0.1.0/negative/load/` | 加载期负例 |
| `testdata/0.1.0/positive/check/` | 正例与 `W-01` 警告用例 |
| `docs/planning/rill-0.1.0-host-contract.md` | profile 形状引用（本阶段只消费，不改形状） |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-4-T1 | `src/rill/loader.py`（map/fn/verb/type 四表） | `feat(loader): PH-4-T1 加载期表结构` | `git revert <sha>` | `bash tools/check-0.1.0.sh --kind error --bucket negative` | M | E-1 |
| PH-4-T2 | `src/rill/loader.py`（调用绑定与默认值） | `feat(loader): PH-4-T2 调用绑定校验` | `git revert <sha>` | `bash tools/check-0.1.0.sh --show negative/load/unknown-function` | M | E-2,E-6 |
| PH-4-T3 | `src/rill/loader.py`（HostProfile/principal） | `feat(loader): PH-4-T3 profile 与 principal` | `git revert <sha>` | `bash tools/check-0.1.0.sh --check-fakes` | M | E-3,E-4 |
| PH-4-T4 | `src/rill/loader.py`（`W-01` 与错误码接线） | `feat(loader): PH-4-T4 W-01 与错误码` | `git revert <sha>` | `bash tools/check-0.1.0.sh --kind warning` | S | E-3,E-5 |
| PH-4-T5 | `docs/planning/rill-0.1.0-host-contract.md`（消费说明） | `docs(loader): PH-4-T5 加载期契约说明` | `git revert <sha>` | `test -s docs/planning/rill-0.1.0-host-contract.md` | S | E-6 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | 正例在 `--profile shell` 与 `--profile agent` 下 `check` 均通过，共享 fixture 的 AST 相等 | 两条命令退出 0 + `--bucket host` 的 AST 比对 |
| E-2 | 负例全部有稳定错误码，行列指向具体成分 | `negative/load/*` 逐条断言 `code/line/col` |
| E-3 | `W-01` 在 `each $f [in] xs` 上触发且不阻断；`E-01`/`E-02` 有稳定错误码与行列 | `--kind warning` 与 `negative/tokenize/*` 原始输出 |
| E-4 | map/fn 表可被 PH-9 以只读接口消费 | 接口测试：只读表对象，不复制、不改写 |
| E-5 | 不执行任何工具 | `check` 路径无 run/工具调用；用 fake 计数为 0 断言 |
| E-6 | 任务清单每项可独立验收（T-6） | 收口对照表逐项贴 `verify` 原始输出 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | PH-3 的 AST 与 span；`profiles/shell.json`、`profiles/agent.json` 同形；`testdata/0.1.0/negative/load/` 现有 3 个负例。 |
| 风险 1 | 把调用绑定塞进 parser：会让 PH-3 提前承担 PH-9 的语义。触发信号：PH-3 的 AST 出现实参绑定结果。 |
| 风险 2 | role 设成必填：Shell profile 无角色，`check` 会全红。触发信号：`--profile shell` 报缺 role。 |
| 风险 3 | `.env` 作宾语被当字段：词法把 `.env` 切为 `FIELD`，加载期须按语法位置区分。触发信号：dotfile 负例被误报或漏报。 |
| 风险 4 | `W-01` 阻断：警告不得改变退出码。触发信号：`--kind warning` 退出非 0。 |

## 6. 收口与 tag

- 收口时产品版本 `0.4.0`；annotated tag `v0.4.0`，message 含 `PH-4` 与收口提交 sha 前 7 位。
- 只推 tag，不推分支、不对外发布。收口对照表：`docs/reviews/closeout-4.md`（收口时新建）。
