# PH-11 立项卡：智能体宿主能力层（Host 轨）

> 状态：正常开卡。体系见 `docs/phases/README.md`。
> 对齐：`docs/planning/rill-0.1.0-phase-plan.md` phase 11；roadmap phase 11「Agent 宿主能力层」。
> 规范版本快照：`1.9.0`。语言规范：`docs/RILL-0.1.0.md`（0.1.1，只读）。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-11`，目录 `docs/phases/PH-11/` |
| 目标 | 把工具/角色/limits 映射到同一 `HostCapabilities`，证明两个宿主只差能力层。 |
| 范围 | 做什么：工具注册表→能力适配、角色/principal、ExecLimits、`run --profile agent`、能力矩阵。不做什么：生产工具/安全策略、真实审批/白名单、真实并发调度、role 语义回灌 parser。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | PH-10 的接口与 Shell 实现；PH-4 的 HostProfile 校验；PH-9 的函数绑定。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `11`（收口目标产品版本 `0.11.0`）。 |
| 已知风险 | role 变所有宿主必选；`[error]` 字符串塞不下工具错误结构；工具绑定与函数绑定混用；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| 进程：映射为 `run`/`exec` 工具，不直接 spawn，返回 `{value, ok}` | 不做真实进程池/限流 |
| 文件：映射为 `read`/`write`，workspace root + path constraint | 不越过工具做 OS 文件访问 |
| env：映射为内核配置/上下文注入，不暴露任意 env | 不做生产密钥注入 |
| stdio：工具返回值、`send`/emit 通道 | 不提供 OS stdin/stdout |
| 角色/limits：Role/Verb/Type 表与 ExecLimits；Shell 的 role 可为空 | 不把 agent role 带回 parser/AST |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `src/rill/host/agent.py` | 工具注册表→能力适配、角色/limits |
| `src/rill/cli.py` | `rill run --profile agent` |
| `src/rill/loader.py` | agent profile 的 `run` / `env` 动词集（parser 不感知宿主） |
| `testdata/0.1.0/host/agent/` | 与 Shell 同源 fixture + agent 专属能力 |
| `tests/phase11/` | 可失败单测 5 个 + 共用夹具 |
| `docs/planning/rill-0.1.0-host-matrix.md` | 五类能力在两种宿主下的形态与差异 |
| `docs/reviews/phase11-red.md` | 逐任务红证与转绿记录 |

fixture 不叫 `source.rill` / `case.json`，避免被 harness 当成 `--fakes` run 用例：
本 phase 的 fixture 由 `tests/phase11/test_agent_fixtures.py` 在临时 cwd 里驱动
真实 Agent 宿主（工具注册表来自 fixture 自己的 manifest）。

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-11-T1 | `src/rill/host/agent.py`（工具→进程/stdio）+ `src/rill/cli.py`（agent 宿主接线）+ `src/rill/loader.py`（agent 动词集） | `feat(host): PH-11-T1 工具能力适配` | `git revert <sha>` | `python3 tests/phase11/test_tools_process_stdio.py` | M | E-1,E-3 |
| PH-11-T2 | `src/rill/host/agent.py`（fs/env） | `feat(host): PH-11-T2 工具文件与环境` | `git revert <sha>` | `python3 tests/phase11/test_fs_env.py` | M | E-1 |
| PH-11-T3 | `src/rill/host/agent.py`（role/limits） | `feat(host): PH-11-T3 角色与 limits` | `git revert <sha>` | `python3 tests/phase11/test_role_limits.py` | M | E-3 |
| PH-11-T4 | `testdata/0.1.0/host/agent/` | `feat(host): PH-11-T4 Agent fixture` | `git revert <sha>` | `python3 tests/phase11/test_agent_fixtures.py` | S | E-1 |
| PH-11-T5 | `docs/planning/rill-0.1.0-host-matrix.md` | `docs(host): PH-11-T5 能力矩阵` | `git revert <sha>` | `python3 tests/phase11/test_matrix_doc.py` | S | E-2,E-4,E-5 |

依赖顺序：T1 → T2 → T3 → T4 → T5。T1 同时接 CLI 与 agent 动词集，
否则 T4 的 fixture 没有可执行的宿主。verify 一律是可失败的单测；
`--show` / `--kind` / `--check-fakes` / `--bucket` 只作为 §4 的补充证据，
不作为任务验收依据（与 PH-10 卡 §3 的口径一致，见 §7 #8）。

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | Agent profile 能跑完与 Shell 同源 fixture，AST 相等 | `--bucket host` 全绿 + AST 逐节点比对 |
| E-2 | 能力矩阵五类各有 Shell/Agent 两列，差异有文字说明 | `host-matrix.md` 五节齐全 |
| E-3 | `[error]` 仍只拿字符串；结构化错误走 `host_meta`/工具值 | `$` 类型断言 |
| E-4 | 没有 parser/lexer 改动 | `git diff --quiet HEAD -- src/rill/lexer.py src/rill/parser.py` 退出 0 |
| E-5 | 任务清单每项可独立验收（T-6） | 收口对照表逐项贴 `verify` 原始输出 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | PH-10 的 `HostCapabilities` 槽位与方法签名；`profiles/agent.json`；`fakes/tools.json` 的 fake 工具；PH-9 的函数绑定（不重叠）。 |
| 风险 1 | role 变成所有宿主必选：Shell 无角色。触发信号：`--profile shell` 因缺 role 失败。 |
| 风险 2 | 工具错误结构塞进 `$`：`$` 只能是字符串。触发信号：`[error]` 的 `$` 是对象。 |
| 风险 3 | 工具绑定与函数绑定混用：函数绑定留在 PH-9。触发信号：agent 侧需要 FnTable 才能解析工具调用。 |

## 6. 收口与 tag

- 收口时产品版本 `0.11.0`；annotated tag `v0.11.0`，message 含 `PH-11` 与收口提交 sha 前 7 位。
- 只推 tag，不推分支、不对外发布。收口对照表：`docs/reviews/closeout-11.md`（收口时新建）。

## 7. 规范缺口与实现裁定（不改变规范正文）

下列各条在规范里没有唯一表述。裁定只写进本表，不写进 `docs/RILL-0.1.0.md`；
红证与实现位置见 `docs/reviews/phase11-red.md`。

| # | 位置 | 缺口 | 本 phase 的实测与裁定 |
| --- | --- | --- | --- |
| 1 | §4.1 / §五 | agent 的主语角色在哪一阶段校验、错误码是什么，未定义 | **裁定：AgentHost 在 parse 之后、exec 之前校验字面量主语**；未知角色 `E-HOST-ROLE-UNKNOWN`，越权 `E-HOST-ROLE-DENIED`，走 run 诊断（退出 2）。`$变量` 等动态主语按默认角色处理，登记为后续 CR |
| 2 | §4.1 / §五 | Shell 是否必须有 role，未定义 | **裁定：Shell 继续无角色**；只有 agent 宿主有 manifest 默认角色，避免把 agent role 变成所有宿主必选（风险 1） |
| 3 | §五.2 | `ExecLimits` 的字段与超限语义未定义 | **裁定：manifest `limits.{steps,time_ms,bytes}`**；`steps` 数工具调用次数，`time_ms` 是墙钟毫秒，`bytes` 是工具结果 JSON 的 UTF-8 字节数。超限返回 `ok=false` + `host_meta.limits`，不截断值。parallel 分支数/搜索深度未实现，登记后续 CR |
| 4 | §4.1 / §五 | `类型:值` 在 agent 侧如何拆分、workspace root 怎么约束，未定义 | **裁定：manifest `types` 表**（`path` / `text`）；`path` 约束下相对/绝对路径都必须落在 `workspace` 内，越界是工具错误 `E-HOST-FS-OUTSIDE`，不是 OS 错误。plain 路径同样受约束 |
| 5 | §4.10 / §五 | agent 失败是否产生 OS 退出码，未定义 | **裁定：agent 不产生 OS 退出码**；脚本执行完成即退出 0（payload 仍带 `ok=false`），只有 CLI/加载/角色诊断退出 2。与 PH-10 卡 §8 #12 的 `--fakes` 协议不同 |
| 6 | §4.2 / §五.8 | agent 加载期动词集未定义 | **裁定：两种宿主共用 `read/write/parse/send/search/replace/contains/review/run/env`**；能力差异只在实现。取代 PH-10 卡 §8 #2 中“agent 不扩 `run`/`env`”的裁定 |
| 7 | §4.2 / §4.16 | agent 的 `send` 落点未定义 | **裁定：调用 `send`/`emit` 工具**；没有 OS stdout/stderr；工具返回值即段值，`host_meta.stdio.channel = "tool"` |
| 8 | §6.6 T-7 | 本卡原 §3 的 verify 是 `--show` / `--kind` / `--check-fakes` / `--bucket`，只能打印或校验资产，无法产出“实现前真实失败”的红证 | **复核时改为 `tests/phase11/test_*.py` 可失败单测**（见 §3）；这是流程口径冲突，不是语言规范缺口。§4 的退出判据仍保留原命令作为补充证据 |
| 9 | §4.16 | agent 的 stdin 形态未定义 | **裁定：`run` 工具的 stdin 来自 `$`/管道输入，按文本传递**；没有 OS stdin，二进制不作为本 phase 的 agent 契约 |
