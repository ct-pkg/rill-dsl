# PH-1 对照卡：基线、样例与门禁骨架

> 状态：**对照卡（事后补记）**。本阶段实物已产出，但开卡、判据冻结与红证均未在开工前成立；
> 本卡不构成一次合规立项，见 §7。体系与口径见 `docs/phases/README.md`。
> 对齐：`docs/planning/rill-0.1.0-phase-plan.md` phase 1；roadmap phase 1「基线」。
> 规范版本快照：`1.9.0`（`AGENTS.md` 生成块头）。语言规范：`docs/RILL-0.1.0.md`（0.1.1，只读）。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-1`，目录 `docs/phases/PH-1/` |
| 目标 | 把规范文本变成可重复执行的验证输入：先有 fixture、AST/token 形态、双宿主接口与失败门禁，再写 parser。 |
| 范围 | 做什么：fixture 集、harness、token/AST golden 空壳、双 profile 与 fake 资产、host contract。不做什么：词法/语法/求值实现、真实工具、CLI parse/check/run/fmt。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | 无前置 phase；roadmap 与 phase-plan 已定稿；`docs/RILL-0.1.0.md` 只读。 |
| 规范版本 | `1.9.0`（开卡快照；本卡为事后补记，快照取自当前块头）。 |
| version-minor | `1`（收口目标产品版本 `0.1.0`；语言规范 `0.1.1` 是另一套版本号）。 |
| 已知风险 | 样例不能用旧 `docs/examples/` 冒充；host AST 相等在 parse 未实现时不可达；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| 从 0.1.1 正文抽 fixture：header、simple_stmt、if、each、parallel、break、call、map、fn、quotes、display | 不实现 lexer/parser/loader/runtime |
| 固定 token 信封与 AST golden 信封（`testdata/0.1.0/expected/README.md`） | 不冻结 AST 节点词汇表（留给 PH-3） |
| 冻结 `HostCapabilities` / `HostProfile` / `CapabilityBinding` 形状 | 不定义五类能力的语义（PH-10/PH-11） |
| 建 harness：用例发现、SUT 子进程协议、双 profile 比对、fake 资产校验 | 不接真实工具、文件系统或网络 |
| 门禁在实现缺失时以退出码 3 明确失败 | 不允许静默通过或用旧样例冒充 |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `tools/rill_harness/` | harness：`cli.py`、`cases.py`、`runner.py`、`sut.py`、`host.py`、`fakes.py` |
| `tools/check-0.1.0.sh` | 门禁入口，转发到 harness CLI |
| `tools/rill_stub/rill.py` | 占位 SUT，仅用于 smoke 链路自证 |
| `testdata/0.1.0/positive/` | 正例 fixture（35 个 `source.rill`） |
| `testdata/0.1.0/negative/` | 负例 fixture（19 个） |
| `testdata/0.1.0/pending/` | 阻塞用例（4 个；A2/B1 裁定后待转正） |
| `testdata/0.1.0/host/` | 同源双 profile fixture（1 个） |
| `testdata/0.1.0/profiles/` | `shell.json`、`agent.json` 两个 profile |
| `testdata/0.1.0/fakes/` | `tools.json`、`host.json` 五个能力桩 |
| `testdata/0.1.0/expected/README.md` | token/AST golden 信封与归一化规则 |
| `docs/planning/rill-0.1.0-host-contract.md` | 双宿主形状契约；能力语义归 PH-10/PH-11 |
| `docs/planning/rill-0.1.0-lexer.md` | §1 记录实现选型（替代计划中的 implementation-decisions） |

## 3. 任务清单

每行“提交”是事后补记的提交标识；实际全部产出在 git 中**未跟踪**，没有 sha 可引（见 §7）。

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-1-T1 | `tools/rill_harness/` | `feat(p0): PH-1-T1 harness 基座`（未提交，见 §7） | `git revert <sha>`（无 sha，不可执行） | `bash tools/check-0.1.0.sh --list` | M | E-1,E-4 |
| PH-1-T2 | `testdata/0.1.0/positive/`、`negative/`、`pending/`、`host/` | `feat(p0): PH-1-T2 fixture 集`（未提交，见 §7） | `git revert <sha>`（无 sha，不可执行） | `find testdata/0.1.0 -name case.json \| wc -l`（≥12） | M | E-2,E-5 |
| PH-1-T3 | `testdata/0.1.0/profiles/`、`fakes/` | `feat(p0): PH-1-T3 双 profile 与 fake 资产`（未提交，见 §7） | `git revert <sha>`（无 sha，不可执行） | `bash tools/check-0.1.0.sh --check-fakes` | S | E-3 |
| PH-1-T4 | `docs/planning/rill-0.1.0-host-contract.md` | `docs(p0): PH-1-T4 宿主形状契约`（未提交，见 §7） | `git revert <sha>`（无 sha，不可执行） | `test -s docs/planning/rill-0.1.0-host-contract.md` | S | E-3 |

## 4. 退出判据（exit-criteria）

本阶段判据为**事后补记**，未在开工前冻结，因此不具备 §6.2 的冻结效力；“现况”列为 2026-11-14 实测。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | `bash tools/check-0.1.0.sh --list` 能枚举全部 fixture，正例 ≥12、负例 ≥10 | 原始输出与计数；现况 FAIL：2 个 fixture 缺 `case.json` |
| E-2 | 每个 fixture 的 `case.json` 含 `kind`/`phase`/`expect`，无空说明 | `--list` 不报“缺少 case.json”；现况 2 个缺失 |
| E-3 | 同源 host fixture 在 shell/agent 两 profile 下 AST 相等 | `bash tools/check-0.1.0.sh --show host/shared/read-send`；现况 BLOCKED（parse 未实现） |
| E-4 | parse 未实现时门禁以 `not implemented`（退出码 3）失败，不静默通过 | `bash tools/check-0.1.0.sh --kind ast` 退出码 3 |
| E-5 | 任务清单每项可独立验收（T-6） | 本表逐项贴 verify 原始输出；现况只能对既有产物复跑 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | roadmap/phase-plan 定稿；harness 的 SUT 协议为“子进程 + 退出码 + stdout JSON”；`testdata/0.1.0/sut.json` 已指向 `python3 -m rill`（PYTHONPATH=src）。 |
| 风险 1 | 旧样例混入：`docs/examples/` 使用 `let`/`fn`/`\|?` 等旧语法。触发信号：fixture 里出现 `# allow:` 之外的旧头或 `let`。 |
| 风险 2 | host AST 相等无法在 PH-1 达成：parse 属 PH-3。触发信号：把 E-3 标成 PASS 但实际走 stub。 |
| 风险 3 | SUT 契约漂移：`sut.json` 指向与 harness 调用参数不一致。触发信号：`--show` 报用法错而非 not implemented。 |

## 6. 收口与 tag

- 本阶段**没有收口**：无收口对照表、无 tag。仓库 tag 数为 0。
- 按 §6.7 V-7 的生效边界，历史 phase 不自动补打 tag；是否回补 `v0.1.0` 由用户单独裁定，本卡不代决。
- 若后续决定回补，必须同时满足：产品版本落点已声明、annotated、message 含 `PH-1` 与收口提交 sha、指向收口提交、可追溯。

## 7. 对照说明（事后补记，非合规收口）

**结论：本阶段不满足 §6.2 立项与 §6.6 红证要求。** 本卡只如实记录既有产出，不倒填判据冒充合规。

- 未成立的三项：① 开卡晚于产出，`exit-criteria` 与 `tasks` 未在首个实现提交前写死；② 没有逐任务 `test(...) 红` 提交与 `baseline`；③ 没有收口对照表与 tag。
- 可从现有材料还原的证据：① 产出物存在性与路径；② `tools/check-0.1.0.sh` 的当前可复跑输出；③ 用例计数与资产形状；④ host contract 的形状条款。
- 永久缺失：① 开卡提交与判据冻结时点；② 每个任务的实现提交 sha 与父子关系；③ 修复前的失败基线（`baseline` 必须早于实现，当前实现文件未跟踪，无法构造）；④ 收口评审与 VERIFY 签字。
- 补救口径：不补造红证，不补造提交。PH-1 的验收改用本卡 §4 的“现况”记录；后续 phase 从 PH-3 起按正常卡执行红证与冻结。
- 与计划书的偏差：`docs/planning/rill-0.1.0-implementation-decisions.md` 未产出，选型记录改落在 `docs/planning/rill-0.1.0-lexer.md` §1；`pending/` 仍有 4 个用例，与计划“pending 为空”不符，登记为遗留项，交由 PH-3/PH-4 转正。
