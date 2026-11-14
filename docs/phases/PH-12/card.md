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
| `src/rill/formatter.py` | `fmt` 的最小实现（PH-5 未交付，见 §7 #1） |
| `tools/check-0.1.0.sh` | 全量门禁入口 `--all` |
| `tools/check-fmt.sh` | round-trip 门禁入口 `--roundtrip` |
| `tests/phase12/` | 可失败单测与共用夹具（CLI、`--all`、round-trip、双 profile、文档） |
| `docs/planning/rill-0.1.0-acceptance.md` | 通过/失败/pending/host-specific 四类清单 |
| `docs/planning/rill-0.1.0-host-matrix.md` | 双 profile 验收结果 |
| `docs/planning/rill-0.1.0-known-limits.md` | 已知限制（生产工具/权限未接、并发未调度、pending 计数） |
| `docs/reviews/phase12-red.md` | 逐任务红证与转绿记录 |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-12-T1 | `src/rill/cli.py`（统一参数/退出码/错误分层）+ `src/rill/formatter.py`（`fmt` 最小实现） | `feat(cli): PH-12-T1 CLI 统一` | `git revert <sha>` | `python3 tests/phase12/test_cli_contract.py` | M | E-1 |
| PH-12-T2 | `tools/check-0.1.0.sh --all` 全样例接线 | `feat(cli): PH-12-T2 全样例门禁` | `git revert <sha>` | `python3 tests/phase12/test_all_gate.py` | M | E-2,E-5 |
| PH-12-T3 | round-trip 门禁接入 | `feat(fmt): PH-12-T3 round-trip 门禁` | `git revert <sha>` | `bash tools/check-fmt.sh --roundtrip` | S | E-3 |
| PH-12-T4 | `docs/planning/rill-0.1.0-host-matrix.md` | `feat(host): PH-12-T4 双 profile 对照` | `git revert <sha>` | `python3 tests/phase12/test_host_matrix.py` | M | E-4 |
| PH-12-T5 | `docs/planning/rill-0.1.0-acceptance.md` | `docs(acceptance): PH-12-T5 验收报告` | `git revert <sha>` | `python3 tests/phase12/test_acceptance_doc.py` | S | E-6 |
| PH-12-T6 | `docs/planning/rill-0.1.0-known-limits.md` | `docs(acceptance): PH-12-T6 已知限制` | `git revert <sha>` | `python3 tests/phase12/test_known_limits_doc.py` | S | E-7 |

依赖顺序：T1 → T2 → T3 → T4 → T5 → T6。T1 的 `fmt` 是 T3 round-trip
门禁的前提；T4/T5/T6 只消费前面已经跑出的原始输出。`verify` 一律是可失败
的测试或门禁命令；`--list` / `--bucket host` 只作为 §4 的补充证据，不作为
任务验收依据（与 PH-11 卡 §3 口径一致，见 §7 #2、#3）。

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

## 7. 规范缺口与实现裁定（不改变规范正文）

下列各条在规范或既有卡片里没有唯一表述。裁定只写进本表，不写进
`docs/RILL-0.1.0.md`；红证与实现位置见 `docs/reviews/phase12-red.md`。

| # | 位置 | 缺口 | 本 phase 的实测与裁定 |
| --- | --- | --- | --- |
| 1 | PH-12 依赖 / PH-5 §2 | 卡片声明依赖 PH-5，但 PH-5 只有卡、`src/rill/formatter.py` 与 `tools/check-fmt.sh` 均不存在；T3 的 round-trip 无被测对象 | **裁定：T1 提供最小 `fmt`（token 级空白归一 + map 引用展开/回收），T3 提供 `--roundtrip` 门禁**。本 phase 只保证 E-3 的 AST 等价；PH-5 的 `expected/fmt` golden、完整反向映射与二进制值规则仍留给 PH-5，不在此冒充完成 |
| 2 | §6.6 T-7 / §3 T1 | 原 verify `bash tools/check-0.1.0.sh --list` 在开工前已退出 0，无法产出“实现前真实失败”的红证 | **复核时改为 `python3 tests/phase12/test_cli_contract.py`**；`--list` 仍作为 §4 的补充证据 |
| 3 | §6.6 T-7 / §3 T4 | 原 verify `bash tools/check-0.1.0.sh --bucket host` 在开工前已全绿，不能证明双 profile 文档被更新 | **复核时改为 `python3 tests/phase12/test_host_matrix.py`**，断言文档新增的验收章节与 host-specific 表 |
| 4 | §6.6 T-7 / §3 T5、T6 | 原 verify `test -s <doc>` 只检查文件非空，文件一旦存在就无法继续失败 | **复核时改为 `python3 tests/phase12/test_acceptance_doc.py` / `test_known_limits_doc.py`**，断言四类清单、pending 计数与已知限制条款 |
| 5 | §3 T2 / `tools/rill_harness/cli.py` | 卡片假定 `--all` 已存在，但 harness 的 argparse 没有该选项；直接运行以“unrecognized arguments”退出 2 | **裁定：在 harness 增加 `--all`**，要求 pending=0 且所有桶（positive/negative/host/smoke）无 FAIL/BLOCK/DRAFT；退出码沿用 0/1/3 |
| 6 | §4 E-2 | `testdata/0.1.0/pending/` 仍有 5 个 `{"retired": true}` 目录，harness 不发现、不统计；只看目录会误报 pending>0 | **裁定：报告同时写“发现到的 pending 数”与“retired 目录数”**；E-2 以 harness 的 pending 计数 0 为准，退役痕迹不删除、不冒充通过 |
| 7 | §4.16 / §三 | 规范只写“加空格、缩进、展开映射表”，未规定 `fmt` 的 CLI 退出码与错误形状 | **裁定：`fmt` 沿用 harness 协议**，成功 0（stdout 文本），词法/语法/加载诊断 2（stdout JSON error），参数错误 2（stage=cli） |
| 8 | §4.16 | 展示态展开映射时，值类长词“无特殊字符则原文”；但 parser 对裸词与 `MAP_REF` 的节点类型不同（`Bare` vs `String`），直接输出原文会让回读 AST 不等 | **裁定：展开后的值类长词一律加引号**；若与相邻词元拼接，则把整个相邻片段引成一个 `STRING`。压缩时再按长词前缀拆回短词引用，保证 AST 等价 |
| 9 | §3 T4 / §4 E-4 | “host-specific 差异全部有记录”没有可机械判定的清单形状 | **裁定：`host-matrix.md` 必须有一节同时给出 shell/agent 两列与“差异”列，并附 `run` 能否真实跑脚本的对照表**；由 `test_host_matrix.py` 逐项断言 |
