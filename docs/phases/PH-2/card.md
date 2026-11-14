# PH-2 对照卡：词法（Parser 轨）

> 状态：**对照卡（事后补记）**。词法器与 token golden 已产出，但开卡、判据冻结与红证均未成立；见 §7。
> 对齐：`docs/planning/rill-0.1.0-phase-plan.md` phase 2；roadmap phase 2「词法」。
> 规范版本快照：`1.9.0`。语言规范：`docs/RILL-0.1.0.md`（0.1.1，只读）。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-2`，目录 `docs/phases/PH-2/` |
| 目标 | 把 0.1.1 源文本切成稳定 token，只做词法，不建 AST、不执行、不感知宿主。 |
| 范围 | 做什么：符号/关键字/引号/`//` 头/map 行模式/行列号/token golden/词法错误码。不做什么：语句结构、map/fn 表、求值、任何宿主模块。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | PH-1 的 harness、token 信封、SUT 协议；`docs/planning/rill-0.1.0-lexer.md` 的 token 词汇。 |
| 规范版本 | `1.9.0`（事后补记快照）。 |
| version-minor | `2`（收口目标产品版本 `0.2.0`）。 |
| 已知风险 | `//map` 标记符与注释分流、零空格切分、数字与 `.字段` 无规范定义；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| 符号扫描：`<> () [] -> {} $ @ ? ,`、`//`、引号、反斜杠 | 不解析语句结构与块归属 |
| 关键字：`if` / `else` / `else-if` / `each` / `parallel` / `break` | 不检查关键字是否在语句起始位 |
| `//map{`、`//map {`、`// map {`、`//fn {` 头；`//map` 无 `{` 为注释 | 不建 map/fn 表（PH-4） |
| map 行模式：短词 + 标记符 + 行长词；标记符仅 `'` / `` ` `` / `<` | 不解释长词语义 |
| 错误码 + 1 基行/列（`col` 按 Unicode 码点） | 不做 AST、不做加载期校验、不做 run |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `src/rill/lexer.py` | 切分实现与 map 行模式 |
| `src/rill/tokens.py` | token kind 词汇与序列化（`kind,text,line,col`） |
| `src/rill/errors.py` | `LexError` 与词法错误码 |
| `src/rill/cli.py` | `rill tokenize <file>` 子命令 |
| `src/rill/__main__.py` | `python3 -m rill` 入口 |
| `testdata/0.1.0/expected/tokens/` | 12 份 token golden |
| `testdata/0.1.0/negative/tokenize/` | 9 个词法负例 |
| `docs/planning/rill-0.1.0-lexer.md` | token 词汇、切分规则、错误码表与暂定事项 |

## 3. 任务清单

“提交”为事后补记标识；实际文件在 git 中未跟踪，没有 sha（见 §7）。

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-2-T1 | `src/rill/lexer.py` | `feat(p1): PH-2-T1 词法切分`（未提交，见 §7） | `git revert <sha>`（无 sha） | `bash tools/check-0.1.0.sh --kind tokens` | M | E-1,E-3 |
| PH-2-T2 | `src/rill/tokens.py` | `feat(p1): PH-2-T2 token 序列化`（未提交，见 §7） | `git revert <sha>`（无 sha） | `bash tools/check-0.1.0.sh --show positive/tokens/compact` | S | E-1,E-6 |
| PH-2-T3 | `src/rill/lexer.py`（`//` 头与 map 行模式） | `feat(p1): PH-2-T3 map 行模式`（未提交，见 §7） | `git revert <sha>`（无 sha） | `bash tools/check-0.1.0.sh --show positive/tokens/map-entries` | M | E-2,E-3 |
| PH-2-T4 | `src/rill/errors.py` | `feat(p1): PH-2-T4 词法错误码`（未提交，见 §7） | `git revert <sha>`（无 sha） | `bash tools/check-0.1.0.sh --bucket negative --kind error` | M | E-4,E-5 |
| PH-2-T5 | `docs/planning/rill-0.1.0-lexer.md` | `docs(p1): PH-2-T5 词法约定`（未提交，见 §7） | `git revert <sha>`（无 sha） | `test -s docs/planning/rill-0.1.0-lexer.md` | S | E-4 |

## 4. 退出判据（exit-criteria）

判据为事后补记，未冻结；“现况”为 2026-11-14 实测。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | 全部 token golden 通过 | `bash tools/check-0.1.0.sh --kind tokens` 退出 0；现况：前置 `--list` 因 2 个 fixture 缺 `case.json` 失败，无法整体复跑 |
| E-2 | `//map {` 不当注释；`//map` 无 `{` 当注释 | golden `space-header`、`comments-and-headers` |
| E-3 | `p'a"b`、`s'my application`、短词后紧跟反引号、`r<read` 的切分符合 §3.2 | golden `map-entries`、`map-verb-marker` |
| E-4 | `E-01` 与 `E-02` 各 1 个负例 | `negative/tokenize/map-bad-marker`、`negative/tokenize/unclosed-verb` |
| E-5 | 非法输入有稳定错误码与行列号 | `negative/tokenize/*` 逐条断言 `stage/code/line/col` |
| E-6 | 任务清单每项可独立验收（T-6） | 本表逐项贴 verify 原始输出；现况只能复跑 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | PH-1 的 `tools/check-0.1.0.sh`、token golden 信封、`sut.json`（`python3 -m rill` + `PYTHONPATH=src`）；`docs/planning/rill-0.1.0-lexer.md` §3 的 token 词汇。 |
| 风险 1 | `//map` 分流：`//map` 后无 `{` 必须整行注释且不产生 token。触发信号：golden 多出 `MAP_HEADER`。 |
| 风险 2 | map 行模式与 `<` 动词冲突：块内 `<` 是标记符，块外是 `VERB`。触发信号：`r<read` 被切成 `VERB`。 |
| 风险 3 | 数字与 `.字段` 无规范定义：`1.5`、`42abc`、`.env` 的归类靠实现约定。触发信号：lexer.md §6 的暂定项被实现悄悄改动。 |
| 风险 4 | pending 未清零：A2/B1 已裁定，但 `pending/` 仍有 4 个用例。触发信号：`--list` 的 pending 计数不为 0。 |

## 6. 收口与 tag

- 本阶段**没有收口**：无收口对照表、无 tag；仓库 tag 数为 0。
- 是否回补 `v0.2.0` 由用户单独裁定，本卡不代决；回补条件同 PH-1 §6。

## 7. 对照说明（事后补记，非合规收口）

**结论：不满足 §6.2 立项与 §6.6 红证要求；词法产出可按现况复跑，但不可宣称合规收口。**

- 未成立：① 开卡与判据冻结在实现之后；② 无逐任务 `test(...) 红` 与 `baseline`；③ 无收口对照表与 tag。
- 可还原：① `src/rill/` 6 个模块与 `rill tokenize`；② 12 份 token golden、9 个词法负例；③ `docs/planning/rill-0.1.0-lexer.md` 的 token 词汇与错误码表；④ 当前 `--show`/`--kind tokens` 的可复跑输出。
- 永久缺失：开卡提交、判据冻结时点、实现提交 sha、修复前失败基线、VERIFY 签字。
- 偏差：计划写 `src/lexer`，实际为 Python 包 `src/rill/lexer.py`（PH-1 §1 已记录选型）；`pending/` 4 个用例未按 A2/B1 转正，登记为遗留项。
