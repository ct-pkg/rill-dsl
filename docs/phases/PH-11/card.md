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
| 进程：`run`/`exec` 映射为工具，工具本体是真实子进程（JSON stdin/stdout），返回 `{value, ok}` | 不做真实进程池/限流 |
| 文件：映射为 `read`/`write` 工具，workspace root + path constraint；工具可做真实文件 I/O | 不越过工具做 OS 文件访问 |
| env：映射为内核配置/上下文注入，不暴露任意 env | 不做生产密钥注入 |
| stdio：工具返回值、`send`/emit 通道 | 不提供 OS stdin/stdout |
| 角色/limits：Role/Verb/Type 表与 ExecLimits；Shell 的 role 可为空 | 不把 agent role 带回 parser/AST |

**工具传输的硬边界**：工具注册表里的 `queue/default` 只是单测用的确定性桩；canonical
manifest 的工具必须是 `command` 形态，由宿主 spawn 一个真实子进程，请求/响应走
JSON stdin/stdout。`rill run --profile agent` 的验收证据必须能看到子进程 pid 与
工具侧副作用，不能只用队列桩证明“用例通过”。

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `src/rill/host/agent.py` | 工具注册表→能力适配、角色/limits、`command` 工具的进程传输 |
| `src/rill/cli.py` | `rill run --profile agent`；`payload.host.profile/principal` |
| `src/rill/loader.py` | agent profile 的 `run` / `env` 动词集（parser 不感知宿主） |
| `testdata/0.1.0/host/agent/` | 与 Shell 同源 fixture + agent 专属能力 |
| `testdata/0.1.0/host/agent/tools/tool_server.py` | canonical 工具的真实子进程实现（JSON stdin/stdout） |
| `tests/phase11/` | 可失败单测 8 个 + 共用夹具 |
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
| PH-11-T6 | `src/rill/host/agent.py`（`command` 工具）+ `testdata/0.1.0/host/agent/tools/tool_server.py` + canonical `profiles/tools.json` | `feat(host): PH-11-T6 工具真实传输` | `git revert <sha>` | `python3 tests/phase11/test_tool_transport.py` | M | E-1,E-8 |
| PH-11-T7 | `src/rill/cli.py`（fakes 失败退出码、`E-RUN-HOST-UNAVAILABLE` 退役、`payload.host`）+ `tools/rill_harness/sut.py` | `feat(host): PH-11-T7 宿主契约收口` | `git revert <sha>` | `python3 tests/phase11/test_host_contract.py` | M | E-9,E-10 |
| PH-11-T8 | `docs/planning/rill-0.1.0-host-matrix.md`（真实传输与 principal 结论）+ `docs/planning/rill-0.1.0-known-limits.md` | `docs(host): PH-11-T8 能力矩阵与陈账` | `git revert <sha>` | `python3 tests/phase11/test_matrix_doc.py` | S | E-2,E-8,E-9 |

> 复核补记（用户 PH-11 收口要求）：T1–T5 只证明了映射层，工具仍是队列桩；
> T6 补真实子进程传输，T7 收口退出码与已退役错误码，T8 把结论写进矩阵。
> 三张任务卡同样先红后绿，红证追加到 `docs/reviews/phase11-red.md`。

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
| E-8 | canonical Agent 宿主的工具调用真的走出进程：子进程 pid、工具侧日志、真实文件内容三者可观察 | `tests/phase11/test_tool_transport.py` + 收口报告贴 `rill run` 原始输出/退出码 |
| E-9 | `--fakes` 未处理失败退出码与真实宿主一致（1）；正常路径不再出现 `E-RUN-HOST-UNAVAILABLE` | 单测断言退出码 + `src/` 全文检索无该错误码 |
| E-10 | 两个宿主共用 parser/lexer/Interpreter；调用方能从 `payload.host.profile` 判断自己在哪套能力体系 | AST 逐节点相等 + 单测断言 `host.profile` / `host.principal` |

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
| 10 | §4.1 / §4.2 | agent 下 `send` 的文本槽与 `write` 的内容槽怎么取未定义 | **裁定：`send` 优先取 object（主语是角色），object 缺省才取 subject/input；`write` 的内容只取管道输入，subject 不是角色时才作为兼容内容**。fixture 里 `engineer <send> "ok"` 的输出是 `"ok"`，不是 `"engineer"` |
| 11 | §五 | 工具调用是否允许宿主直接碰 OS，未定义 | **裁定（取代 T1 的“不直接 spawn”表述）：工具是外部进程**。`command` 工具由宿主 spawn，请求 `{"tool", "args"}` 走 stdin JSON，响应 `{"ok", "value", "error"}` 走 stdout JSON；`queue/default` 只保留给单测。工具失败/超时/坏 JSON 一律 `ok=false`，错误码 `E-HOST-TOOL-TRANSPORT` / `E-HOST-TOOL-TIMEOUT` / `E-HOST-TOOL-SPAWN`，不冒充 DSL 诊断 |
| 12 | PH-10 卡 §8 #12 | `--fakes` 未处理失败退出 0，与真实宿主不一致 | **裁定：收掉缺口**。`--fakes` 与真实 Shell 宿主的默认约定一致：`ok=true` → 0，`ok=false` → 1；harness 的 SUT 协议接受“退出 1 + `{"ok": false}`”为运行结果，不再当内部错误。Agent 真实宿主仍按 #5 固定 0，`--fakes` 是测试传输，不继承 agent 策略 |
| 13 | PH-7 卡 §8 #5 / PH-10 卡 #1 | 独立 `[ok] $x {}` / `[error] $x {}` 语义未定义 | **裁定：本版仍不支持，继续报 `E-RUN-UNSUPPORTED`；不阻塞 Agent 脚本**。绕法：把块挂到产生 `$` 的那条语句上，用尾随块（如 `<read> x [ok] $v { ... }` / `<read> x [error] { ... }`）；独立形式留给后续 CR，不在 PH-11 自定语义 |
| 14 | PH-10 卡 §8 #11 | `E-RUN-HOST-UNAVAILABLE` 是占位错误 | **裁定：退役**。Agent profile 永远有宿主（manifest 或 builtin），CLI 不再产生该错误码；缺失/坏 manifest 报 `E-RUN-HOST-PROFILE`（退出 2）。`src/rill/` 不再出现 `E-RUN-HOST-UNAVAILABLE` |
| 15 | §五.1 / §五.2 | 能力清单与 principal 是不是同一套 `HostCapabilities` | **裁定：槽位接口是同一套，授权维度不同**。process/fs/env/stdio/exit 五槽两宿主同签名；ShellPolicy 是“能做什么”（operation grant，principal 为 OS 用户，不建模）；AgentPolicy 是“谁 + 能做什么”（role 是动词级 principal，types/context/limits/tools 是五槽的实现参数）。调用方用 `--profile` 选择，并从 `payload.host.profile` / `payload.host.principal` 读取身份；不需要第二套执行路径 |
| 16 | §4.16 / canonical manifest | 工具注册表 schema 名 `rill-fakes-tools/0` 是否继续用于真实工具 | **裁定：保留 schema 名，只扩展工具描述**。同一份注册表可混用 `queue/default`（确定性桩）与 `command`（真实子进程）；canonical manifest 一律 `command`，并在矩阵文档里标明哪些 fixture 仍用桩 |
