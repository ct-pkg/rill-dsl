# PH-12 立项卡：CLI、全样例与 golden 集成（集成轨）

> 状态：正常开卡。体系见 `docs/phases/README.md`。
> 对齐：`docs/planning/rill-0.1.0-phase-plan.md` phase 12；roadmap phase 12「双宿主集成」。
> 规范版本快照：`1.9.0`。语言规范：`docs/RILL-0.1.0.md`（0.1.1，只读）。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-12`，目录 `docs/phases/PH-12/` |
| 目标 | 把 Parser/Runtime/Formatter/Host 串成可运行 CLI，在 shell/agent 两 profile 上跑全样例并给出四类清单。 |
| 范围 | 做什么：CLI 统一参数与退出码、全样例端到端、round-trip 门禁、双 profile 对照、验收报告与已知限制。不做什么：生产工具/权限、真实并发调度、旧 `v0.1 rev.1` 兼容。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | PH-4、PH-5、PH-9、PH-11 全部收口；PH-1 的 harness 与 `tools/check-0.1.0.sh`。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `12`（收口目标产品版本 `0.12.0`）。 |
| 已知风险 | 把 pending 剔除冒充通过；旧样例混入；host-specific 差异未记录；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| CLI 统一：`parse`/`check`/`run --profile`/`fmt` 的参数、退出码、错误分层 | 不新增语法、不改 0.1.1 正文 |
| 正例端到端；负例只跑解析/加载；pending 显式计数 | 不把 pending 从通过率里静默剔除 |
| 压缩↔展示 round-trip 纳入门禁 | 不宣称两个宿主能力等价 |
| 同源 fixture 的 AST 逐节点相等；host-specific 差异入表 | 不验证生产安全策略 |
| 验收报告四类清单 + 已知限制 | 不实现旧 DSL 兼容 |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `src/rill/cli.py` | 四个子命令的统一入口与退出码 |
| `tools/check-0.1.0.sh` | 全量门禁入口 `--all` |
| `docs/planning/rill-0.1.0-acceptance.md` | 通过/失败/pending/host-specific 四类清单 |
| `docs/planning/rill-0.1.0-host-matrix.md` | 双 profile 验收结果 |
| `docs/planning/rill-0.1.0-known-limits.md` | 已知限制（生产工具/权限未接、并发未调度、pending 计数） |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-12-T1 | `src/rill/cli.py`（统一参数/退出码/错误分层） | `feat(cli): PH-12-T1 CLI 统一` | `git revert <sha>` | `bash tools/check-0.1.0.sh --list` | M | E-1 |
| PH-12-T2 | `tools/check-0.1.0.sh --all` 全样例接线 | `feat(cli): PH-12-T2 全样例门禁` | `git revert <sha>` | `bash tools/check-0.1.0.sh --all` | M | E-2,E-5 |
| PH-12-T3 | round-trip 门禁接入 | `feat(fmt): PH-12-T3 round-trip 门禁` | `git revert <sha>` | `bash tools/check-fmt.sh --roundtrip` | S | E-3 |
| PH-12-T4 | `docs/planning/rill-0.1.0-host-matrix.md` | `feat(host): PH-12-T4 双 profile 对照` | `git revert <sha>` | `bash tools/check-0.1.0.sh --bucket host` | M | E-4 |
| PH-12-T5 | `docs/planning/rill-0.1.0-acceptance.md` | `docs(acceptance): PH-12-T5 验收报告` | `git revert <sha>` | `test -s docs/planning/rill-0.1.0-acceptance.md` | S | E-6 |
| PH-12-T6 | `docs/planning/rill-0.1.0-known-limits.md` | `docs(acceptance): PH-12-T6 已知限制` | `git revert <sha>` | `test -s docs/planning/rill-0.1.0-known-limits.md` | S | E-7 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | 全部正例通过；负例全部按预期错误码失败 | `--all` 的逐例状态与错误码 |
| E-2 | `xfail-pending` 数量为 0（A2/B1 已裁定） | 报告显式写出 pending 计数 |
| E-3 | round-trip 全绿 | `bash tools/check-fmt.sh --roundtrip` 退出 0 |
| E-4 | 同 fixture 在 shell/agent 的 AST 相等；host-specific 差异全部有记录 | `--bucket host` + 差异表 |
| E-5 | `bash tools/check-0.1.0.sh --all` 退出 0 | 原始输出贴收口对照表 |
| E-6 | 不修改 0.1.1 正文；任何规范改动有 CR 记录 | `git diff --quiet HEAD -- docs/RILL-0.1.0.md` + CR 清单 |
| E-7 | 任务清单每项可独立验收（T-6） | 收口对照表逐项贴 `verify` 原始输出 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | PH-4、PH-5、PH-9、PH-11 收口；`tools/rill_harness` 的用例发现；`sut.json` 指向稳定。 |
| 风险 1 | pending 被静默剔除：报告必须同时给通过数与 pending 数。触发信号：`--all` 通过但 pending > 0。 |
| 风险 2 | 旧样例混入：`docs/examples/` 不是 0.1.1 验收输入。触发信号：fixture 出现 `let`/`\|?`。 |
| 风险 3 | host-specific 差异漏记：能力差异必须入表，不得改语法迁就。触发信号：同一 fixture 两边 AST 不等却无记录。 |

## 6. 收口与 tag

- 收口时产品版本 `0.12.0`；annotated tag `v0.12.0`，message 含 `PH-12` 与收口提交 sha 前 7 位。
- 只推 tag，不推分支、不对外发布；对外发布另有独立判据（API 稳定、迁移说明、CHANGELOG）。
- 收口对照表：`docs/reviews/closeout-12.md`（收口时新建）。
