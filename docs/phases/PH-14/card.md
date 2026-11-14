# PH-14 立项卡：CT parser/AST（P2）接管与收口

> 状态：正常开卡。CT 重写轨道第 2 层。体系见 `docs/phases/README.md`，
> 上游 `docs/planning/rill-0.1.0-ct-rewrite-roadmap.md`。语言规范 `docs/RILL-0.1.0.md`（0.1.1，只读）。
> **在途项**：`ct/rill_ct.ct` 已含 `parse --dump-ast` 路径；本卡接管验收与补差，不重复立项。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-14`，目录 `docs/phases/PH-14/` |
| 目标 | CT 版 AST 与 23 个 AST golden、10 个 parse 负例逐条一致，且与 Python 参考实现对拍 0 差异。 |
| 范围 | 做什么：AST 节点/字段顺序/序列化补齐、AST golden、parse 负例、AST 对拍、规则映射说明。不做什么：重写 lexer、loader、求值、格式化、宿主。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | PH-13 的构建与 CT SUT、token 流；`testdata/0.1.0/expected/ast/`；`negative/parse/`。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `14`（目标产品版本 `0.14.0`）。 |
| 已知风险 | AST 字段顺序与 span 归一化、`[results]` 位置、裸词 value 归约；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| `parse --dump-ast` 输出与 golden 同形；节点/字段/顺序对齐 | 不做加载期校验（PH-15） |
| 23 AST golden + 10 parse 负例的 `code/line/col` | 不做求值与段输出（PH-16/17） |
| AST 对拍（忽略 `span`）+ 规则映射到 31 条产生式 | 不改 Python AST、不改 golden |
| 尾随块、`[results]` 块级、裸词 value 归约 | 不实现格式化（PH-18） |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `ct/rill_ct.ct`（parser/AST 段） | **在途输入 + 补差**；只改本卡范围 |
| `tools/diff/diff.py`（ast 层） | AST 对拍与 span 归一化 |
| `docs/reviews/diff/PH-14.md` | AST 差异报告 |
| `ct/README.md` | 31 条产生式 → 代码位置的规则映射 |
| `docs/reviews/diff/registry.md` | 本阶段差异登记（若有） |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-14-T1 | `ct/rill_ct.ct`（AST 字段顺序与序列化补差） | `feat(ct): PH-14-T1 AST 序列化对齐` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --kind ast --bucket positive` | M | E-1 |
| PH-14-T2 | `docs/reviews/diff/PH-14.md`（AST 对拍） | `docs(diff): PH-14-T2 AST 差异报告` | `git revert <sha>` | `python3 tools/diff/diff.py --layer ast` | M | E-3,E-5 |
| PH-14-T3 | parse 负例接管清单（10 条） | `test(ct): PH-14-T3 parse 负例对齐` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --bucket negative --kind error --case negative/parse/break-verb-value --case negative/parse/duplicate-error --case negative/parse/duplicate-ok --case negative/parse/fn-def-in-body --case negative/parse/missing-block --case negative/parse/results-as-prep --case negative/parse/results-in-branch --case negative/parse/results-in-simple --case negative/parse/results-outside-parallel --case negative/parse/unknown-prep` | M | E-2,E-4 |
| PH-14-T4 | `ct/README.md`（产生式映射） | `docs(ct): PH-14-T4 产生式映射` | `git revert <sha>` | `test -s ct/README.md` | S | E-6 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | 23 个 AST golden 全部由 CT SUT 通过 | `--kind ast --bucket positive` 退出 0 |
| E-2 | 10 个 parse 负例的 `stage=parse` 与错误码/行列一致 | 逐条 JSON 比对 |
| E-3 | AST 对拍 23/23，忽略 `span` 后 0 差异或全部登记 | `docs/reviews/diff/PH-14.md` |
| E-4 | 成功 0、parse 失败 2；错误 JSON 与 Python 同形 | 退出码 + 字段比对 |
| E-5 | 每个语句形态至少 1 个 AST golden 由 CT 通过 | `--list --kind ast` 与逐例结果 |
| E-6 | 任务清单每项可独立验收（T-6） | 收口对照表逐项贴 `verify` 原始输出 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | PH-13 的 `ct/bin/rill_ct` 与 `--sut` 覆盖；token 顺序与行列；AST 信封 `testdata/0.1.0/expected/README.md`。 |
| 风险 1 | span 未归一化导致假差异：对拍必须先剔除 `span`。触发信号：差异只在 span。 |
| 风险 2 | 裸词 value 归约成 `Bare` 节点：必须与 Python 一样生成字符串值节点。触发信号：E-1 该 golden 红。 |
| 风险 3 | `[results]` 在非 parallel 未解析期报错。触发信号：负例 `code` 不符。 |
| 风险 4 | 字段顺序被“看起来一样”掩盖：必须逐键比对，不能只比 JSON 文本。触发信号：报告只贴截图。 |

## 6. 收口与 tag

- 收口附 `docs/reviews/diff/PH-14.md` 与 `docs/reviews/closeout-14.md`。
- 版本 `0.14.0`；tag 按 `docs/phases/README.md` §4，本卡不自动打 tag、不 push。
- 收口后 PH-15/PH-16/PH-18 才可开工。
