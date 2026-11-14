# PH-21 立项卡：CT 集成、全样例与双实现对拍总账（P9）

> 状态：正常开卡。CT 重写轨道第 9 层，汇合点。体系见 `docs/phases/README.md`，
> 上游 `docs/planning/rill-0.1.0-ct-rewrite-roadmap.md`。语言规范 `docs/RILL-0.1.0.md`（0.1.1，只读）。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-21`，目录 `docs/phases/PH-21/` |
| 目标 | CT 版 CLI 串起全链路，85 个 fixture、71 个 round-trip、24 个 host fixture 全通过，并与 Python 参考实现全层对拍 0 未解释差异。 |
| 范围 | 做什么：CLI 统一、全样例、round-trip、双 profile、全层对拍、parity 报告、Python 参考实现冻结登记。不做什么：规范改动、下掉 Python、生产工具/权限、性能优化。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | PH-17、PH-18、PH-19、PH-20 全部收口；PH-13 的构建与对拍脚本。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `21`（目标产品版本 `0.21.0`）。 |
| 已知风险 | 把 pending 剔除冒充通过；golden 被顺手改动；两版长期漂移；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| CLI 统一：`tokenize`/`parse`/`check`/`run`/`fmt` 的参数、退出码、错误分层 | 不新增语法、不改规范正文 |
| 85 fixture + 71 round-trip + 24 host fixture 全量 | 不把 pending 从通过率里静默剔除 |
| 全层对拍：token/AST/error/eval/host，差异归因到 phase | 不宣称两宿主能力等价 |
| parity 报告与 Python 参考实现冻结登记 | 不删除 Python、不改 `src/rill/` |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `tools/diff/diff.py`（全层 + `--all`） | 双实现总对拍 |
| `tools/diff/sut.ct.json` | 最终 CT SUT 配置 |
| `docs/reviews/diff/PH-21.md` | 全层差异总报告 |
| `docs/planning/rill-0.1.0-ct-parity.md` | 双实现 parity 矩阵与已知差异 |
| `docs/reviews/closeout-21.md` | 本阶段收口对照表 |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-21-T1 | `tools/diff/sut.ct.json` 与 CLI 统一 | `feat(ct): PH-21-T1 CT CLI 统一` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --all` | M | E-1 |
| PH-21-T2 | 71 个 round-trip 全量接线 | `feat(ct): PH-21-T2 round-trip 全量` | `git revert <sha>` | `python3 tools/diff/diff.py --layer fmt --mode roundtrip` | M | E-2 |
| PH-21-T3 | 24 个 host fixture 双 profile | `feat(ct): PH-21-T3 host 双 profile` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --bucket host` | M | E-3 |
| PH-21-T4 | `docs/reviews/diff/PH-21.md` 全层对拍 | `docs(diff): PH-21-T4 全层差异报告` | `git revert <sha>` | `python3 tools/diff/diff.py --all` | M | E-4,E-6,E-7 |
| PH-21-T5 | `docs/planning/rill-0.1.0-ct-parity.md` | `docs(ct): PH-21-T5 parity 报告` | `git revert <sha>` | `test -s docs/planning/rill-0.1.0-ct-parity.md` | S | E-5,E-8 |
| PH-21-T6 | `docs/reviews/closeout-21.md` | `docs(review): PH-21-T6 收口对照表` | `git revert <sha>` | `test -s docs/reviews/closeout-21.md` | S | E-8 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | 85 个 fixture 全通过；pending 计数为 0 或显式列为 xfail | `--all` 逐例状态 + pending 计数 |
| E-2 | 71 个 round-trip 全绿 | `--mode roundtrip` 退出 0 |
| E-3 | 24 个 host fixture 在 shell/agent 两 profile 全绿 | `--bucket host` 退出 0 |
| E-4 | 全层对拍 0 未解释差异；每条差异有 `first_seen_phase` 与归属 | `docs/reviews/diff/PH-21.md` |
| E-5 | `tools/check.sh all` 退出 0 | 原始输出贴收口对照表 |
| E-6 | Python 参考实现未被改动 | `git diff --quiet 4dd303d -- src/rill` 退出 0 |
| E-7 | fixture 与 golden 未被改动 | `git diff --quiet 4dd303d -- testdata/0.1.0` 退出 0 |
| E-8 | 任务清单每项可独立验收（T-6） | 收口对照表逐项贴 `verify` 原始输出 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | 前四层收口；`tools/diff` 全层；`testdata/0.1.0` 的 85 fixture / 71 round-trip / 24 host；`tools/check.sh`。 |
| 风险 1 | pending 静默剔除：报告必须同列通过数与 pending 数。触发信号：`--all` 通过但 pending > 0。 |
| 风险 2 | 为让 CT 过而改 golden：E-7 硬闸，且提交需 `golden-change:` 记录。触发信号：`testdata` 有 diff。 |
| 风险 3 | 两版长期漂移：对拍只做一次。触发信号：PH-21 后无 `registry.md` 更新。 |
| 风险 4 | 把 Python 当“待删除”顺手改：违反双实现长期定位。触发信号：`src/rill` 有 diff。 |

## 6. 收口与 tag

- 收口附 `docs/reviews/diff/PH-21.md`、`docs/reviews/closeout-21.md` 与 parity 报告。
- 版本 `0.21.0`；tag 按 `docs/phases/README.md` §4，本卡不自动打 tag、不 push。
- 本卡收口后 CT 版为正式实现；Python 参考实现保持冻结，双实现长期并存。
