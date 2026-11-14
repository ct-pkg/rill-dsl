# PH-13 立项卡：CT 词法层（P1）接管与收口

> 状态：**已收口（2026-11-15，closeout-13 GO）**。CT 重写轨道第 1 层。体系见 `docs/phases/README.md`，上游见
> `docs/planning/rill-0.1.0-ct-rewrite-roadmap.md`。语言规范 `docs/RILL-0.1.0.md`（0.1.1，只读）。
> 收口证据：token golden 12/12、82 个源 token 对拍 0 差异；见 `docs/reviews/closeout-13.md`
> 与 `docs/reviews/diff/PH-13.md`。本卡不重写 lexer，只做构建、协议、golden 接管、对拍与收口。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-13`，目录 `docs/phases/PH-13/` |
| 目标 | 让 CT 版 `tokenize` 可重复构建，并与 Python 参考实现在 12 个 token golden、9 个词法负例上逐条一致。 |
| 范围 | 做什么：CT 构建脚本、SUT 协议、token golden/负例接管、对拍脚本与差异报告、构建说明。不做什么：重写 lexer、parser/loader/求值/宿主；不改 Python 与 golden。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | 在途 `ct/rill_ct.ct`（只读引用）；`testdata/0.1.0/expected/tokens/`；`tools/rill_harness` 的 `--sut` 覆盖。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `13`（目标产品版本 `0.13.0`）。 |
| 已知风险 | 在途文件归属另一会话；CT 头/实现拆分状态未复核；token 信封必须与 Python 完全同形；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| `ctc` → `cc -std=c99` 的可重复构建，产物落 `ct/bin/` | 不改 `ct/rill_ct.ct` 的语义；改动由在途会话负责 |
| 用 harness `--sut` 把被测命令指到 CT 二进制 | 不改 `testdata/0.1.0/sut.json`（Python 参考实现的 SUT） |
| token 序列、错误 `stage/code/line/col`、退出码 0/2 对齐 | 不碰 parser/AST、loader、求值、宿主 |
| 首次建立 `tools/diff/` 与差异报告/登记表 | 不修改任何 golden；差异只登记与归因 |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `ct/build.sh` | `ctc` + `cc -std=c99` 构建，输出 `ct/bin/rill_ct` |
| `ct/README.md` | 构建命令、CLI 形态、与 Python 的协议契约 |
| `tools/diff/diff.py` | 对拍入口（本 phase 只实现 token 层） |
| `tools/diff/sut.ct.json` | CT SUT 命令与构建产物路径 |
| `docs/reviews/diff/PH-13.md` | 本阶段差异报告（逐用例） |
| `docs/reviews/diff/registry.md` | 已裁定差异登记（本 phase 建空表） |
| `ct/rill_ct.ct` | **在途输入**：另一会话所有，本卡只读引用，不计为本卡产出 |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-13-T1 | `ct/build.sh` | `feat(ct): PH-13-T1 CT 构建脚本` | `git revert <sha>` | `bash ct/build.sh && test -x ct/bin/rill_ct` | M | E-1 |
| PH-13-T2 | `ct/README.md` 与 `tools/diff/sut.ct.json` | `docs(ct): PH-13-T2 CT 协议说明` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --kind tokens` | S | E-2 |
| PH-13-T3 | `tools/diff/diff.py`（token 层） | `feat(diff): PH-13-T3 token 对拍入口` | `git revert <sha>` | `python3 tools/diff/diff.py --layer token` | M | E-4,E-5 |
| PH-13-T4 | `docs/reviews/diff/PH-13.md` 与 `registry.md` | `docs(diff): PH-13-T4 token 差异报告` | `git revert <sha>` | `test -s docs/reviews/diff/PH-13.md` | S | E-4,E-6 |
| PH-13-T5 | 词法负例接管清单（9 条） | `test(ct): PH-13-T5 词法负例对齐` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --bucket negative --kind error` | S | E-3 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | 构建可重复：干净检出上 `bash ct/build.sh` 退出 0，产物存在 | `test -x ct/bin/rill_ct` |
| E-2 | 12 个 token golden 全部由 CT SUT 通过 | `--sut './ct/bin/rill_ct' --kind tokens` 退出 0 |
| E-3 | 9 个词法负例的 `stage/code/line/col` 与 Python 一致 | 逐条 JSON 比对 |
| E-4 | token 对拍 12/12，差异 0 或全部登记 | `docs/reviews/diff/PH-13.md` 贴命令与逐项结果 |
| E-5 | 成功退出 0、词法失败退出 2，stdout 信封同形 | 两条命令的退出码与 JSON 字段 |
| E-6 | 任务清单每项可独立验收（T-6） | 收口对照表逐项贴 `verify` 原始输出 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | 在途 `ct/rill_ct.ct` 的 CLI 形态：`tokenize <file>`、`parse <file> --dump-ast`；`--sut` 覆盖只影响被测命令，不改用例。 |
| 风险 1 | 在途文件被另一会话继续改：本卡只读，冲突时等其落定，不提交 `ct/`。触发信号：`git status` 出现 `ct/` 未跟踪改动。 |
| 风险 2 | 头/实现拆分前提（A-1）未复核：先保持单文件构建。触发信号：`.m.ct` import `.h.ct` 构建失败。 |
| 风险 3 | token 信封字段顺序/键名与 Python 不同：golden 会全红。触发信号：`--kind tokens` 报结构差异。 |
| 风险 4 | 为过 golden 改 golden：禁止。触发信号：提交里出现 `testdata/0.1.0/expected/tokens/` 改动。 |

## 6. 收口与 tag

- 收口必须附 `docs/reviews/diff/PH-13.md` 与 `docs/reviews/closeout-13.md`；差异有未解释项不得收口。
- 版本 `0.13.0`；tag 按 `docs/phases/README.md` §4，本卡不自动打 tag、不 push。
- 收口后 PH-14 才可开工；PH-14 依赖本卡的构建与 SUT 协议。
