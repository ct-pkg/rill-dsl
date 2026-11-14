# PH-3 立项卡：语法与 AST（Parser 轨）

> 状态：正常开卡（判据在开工前写死，首个实现提交后冻结）。体系见 `docs/phases/README.md`。
> 对齐：`docs/planning/rill-0.1.0-phase-plan.md` phase 3；roadmap phase 3「完整 §三 产生式与 AST」。
> 规范版本快照：`1.9.0`。语言规范：`docs/RILL-0.1.0.md`（0.1.1，只读）。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-3`，目录 `docs/phases/PH-3/` |
| 目标 | 按 §三 产生式把 token 流归约为完整 AST，只解析，不校验注册表、不执行。 |
| 范围 | 做什么：`program`/`header`/全部 `statement`、`verb_call` 可选主语、`arg := value`、`prep_block_stmt`、`prep_phrase*`、`parallel`/`[results]`、尾随块数量、AST 序列化与解析错误。不做什么：加载期校验、执行、格式化、宿主判断。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | PH-2 的 token 流与关键字；token 信封 `rill-tokens-golden/0`；harness `--kind ast` 通道。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `3`（收口目标产品版本 `0.3.0`）。 |
| 已知风险 | `verb_call` 可选主语、`[into]` 的 `]` 归约三分、裸词 value、`->$x` 顺序；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| `program := header* statement*`；`header := map_block \| fn_block` | 不建 map/fn 表、不查重（PH-4） |
| `statement` 全部分支：simple/prep_block/if/each/parallel/break/call | 不求值、不做段输出（PH-7/PH-8） |
| `verb_call := [subject] <动词> 宾语 [(状语)] prep_phrase*` | 不把角色/工具/权限写进 AST 语义 |
| `call_stmt` 的 `arg := value`；裸词在 value 位按 STRING 归约 | 不校验实参个数与默认值（PH-4） |
| 重复 `[ok]`/`[error]` 解析期拒绝；`[results]` 只允许 parallel 块级 | 不实现表面格式化（PH-5） |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `src/rill/ast.py` | AST 节点、字段顺序、`--dump-ast` 序列化 |
| `src/rill/parser.py` | §三 产生式与尾随块归约 |
| `src/rill/cli.py` | `parse --dump-ast` 子命令 |
| `testdata/0.1.0/positive/` | 每条语句形态至少 1 个正例 |
| `testdata/0.1.0/negative/parse/` | 解析期负例与稳定错误码 |
| `testdata/0.1.0/expected/ast/` | AST golden（信封见 `expected/README.md`） |

## 3. 任务清单

每行“提交”指实现提交；其父提交是同 task-id 的 `test(...) 红`（T-7），两者只含本任务路径。

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-3-T1 | `src/rill/ast.py` | `feat(parser): PH-3-T1 AST 节点与序列化` | `git revert <sha>` | `PYTHONPATH=src python3 -m rill parse --dump-ast testdata/0.1.0/positive/block/trailing/source.rill --profile shell` | M | E-1 |
| PH-3-T2 | `src/rill/parser.py`（header 与 simple/prep_block） | `feat(parser): PH-3-T2 program 与语句归约` | `git revert <sha>` | `bash tools/check-0.1.0.sh --kind ast --bucket positive` | M | E-2,E-5 |
| PH-3-T3 | `src/rill/parser.py`（verb_call/call_stmt/prep_phrase） | `feat(parser): PH-3-T3 调用与介宾短语` | `git revert <sha>` | `bash tools/check-0.1.0.sh --show positive/simple/prep-phrases` | M | E-3 |
| PH-3-T4 | `src/rill/parser.py`（if/each/parallel/break/尾随块） | `feat(parser): PH-3-T4 控制流与尾随块` | `git revert <sha>` | `bash tools/check-0.1.0.sh --show positive/parallel/results` | M | E-5 |
| PH-3-T5 | `testdata/0.1.0/negative/parse/` 与解析错误码 | `feat(parser): PH-3-T5 解析错误码` | `git revert <sha>` | `bash tools/check-0.1.0.sh --bucket negative --kind error` | S | E-4,E-6 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结；变更只能关闭当前 phase 另开（§6.2）。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | 全部正例 AST golden 通过 | `bash tools/check-0.1.0.sh --kind ast --bucket positive` 退出 0，diff 为空 |
| E-2 | `each $f [in] xs`、`break done`、`@ "f" bare` 可归约，裸词在 AST 中为字符串值节点 | golden 节点断言 |
| E-3 | `if $cfg <contains> debug=true`、`@ "f" "a"`、`[into] $cfg {}`、`parallel { … } [results]{} \|> …` 可归约 | 四条 golden 均存在且通过 |
| E-4 | `[results]` 出现在非 parallel、`@` 定义出现在正文、重复 `[ok]`、缺 block 全部有稳定解析错误 | 负例逐条断言 `code/line/col` |
| E-5 | 每个语句形态至少 1 个 AST golden | `--list --kind ast --bucket positive` 可枚举 |
| E-6 | 任务清单每项可独立验收（T-6） | 收口对照表逐项贴 `verify` 原始输出 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | PH-2 的 token 流；`src/rill/cli.py` 的 SUT 退出码协议（0/2/3）；harness 的 `kind: ast` 与 golden 信封。 |
| 风险 1 | `verb_call` 可选主语：写成必选会让 `if $cfg <contains> debug=true` 不可归约。触发信号：E-3 第一条解析失败。 |
| 风险 2 | `[into]` 的 `]` 三分：尾随形式 / 普通介词 / 独立 `prep_block_stmt`。触发信号：`[into] $cfg {}` 被当普通介词。 |
| 风险 3 | 裸词 value：词法给 `BARE`，AST 必须在 value 位生成 STRING 节点。触发信号：AST 保留 `Bare` 节点。 |
| 风险 4 | `->$x` 与尾随块顺序：AST 必须保留书写顺序，不得解析期重排。触发信号：golden 子节点顺序与源码相反。 |

## 6. 收口与 tag

- 收口时产品版本 `0.3.0`；annotated tag `v0.3.0`，message 含 `PH-3` 与收口提交 sha 前 7 位。
- 只推 tag，不推分支、不对外发布；分支推送与发布须用户显式指令。
- 收口对照表：`docs/reviews/closeout-3.md`（模板已建）。
