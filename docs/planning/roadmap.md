# Phase 1–5 粗排期（draft）

> 状态：`draft`，只作排期草案，不是 G1 意义上的路线图。依据：[09 里程碑](../spec/dsl/09-milestones.md)、[PH-1 卡](../phases/PH-1/card.md)、S-001..S-024 与 D-001..D-019。
> 说明：仓库尚无 `docs/planning/requirements-pool.md` 与 `AN-<id>.md`；按 AGENTS 6.1 R-1/R-2，本表在 Phase 0 补齐需求池前**不得**作为 G1 证据。本表不新增需求、不改 09 正文、不移动 DSL 规范版本。

## 1. 总览

| Phase | 对应 09 | 主题 | 依赖 | 退出判据锚点 | 可运行样例 |
| --- | --- | --- | --- | --- | --- |
| PH-1 | M1 + M2 + M5/M7 静态子集 | 完整文法、AST、加载期校验、行列号错误 | Phase 0 门禁与构建骨架 | PH-1 卡 §9 E-1..E-9 | `rill parse --dump-ast` + 五例 golden |
| PH-2 | M3 | 执行器核心：值模型、绑定/赋值、if/for、ExecLimits、DslResult | PH-1 收口 | 赋值 4 类、循环 2 类、条件 1 类、`limit` 全有负例 | `examples/phase2/` + fake 工具 |
| PH-3 | M4 | 管道与降级：`\|>`、`\|?`、R4 失败行为表、`degraded` | PH-2 收口 | 求值轨迹 4 例、可捕获/不可捕获各 2 例、`pipe_rhs`/`fallback_lhs` | `examples/phase3/` |
| PH-4 | M5 | `into` + `$` + `fn`：注入、闭包只读、无环、`arity` | PH-2 收口；PH-3 可并行 | 注入矩阵 3 例、递归/遮蔽工具名负例 | `examples/phase4/` |
| PH-5 | M6 | 截断 + emit + 事件总线：侧车、粘性、`max_emit_bytes`/`max_payload_depth` | PH-2/P3 收口 | 伪字段/逃逸/粘性/字节口径 6 例；emit 无订阅方/队列满、字节与深度超限各 1 例（schema 由内核配置，不在脚本 golden 内） | `examples/phase5/` |

Phase 1 把 09 的 M1（lexer）与 M2（parser + 静态检查）合并为一个可运行切片；理由是“只有 lexer 无法交付可运行样例”，而 09 §1 原则 3 要求每个里程碑至少一个可运行样例。09 正文不改，映射关系在本表与 PH-1 卡 A-1 中记明。

## 2. 分阶段说明

### Phase 1：完整文法切片（09 M1+M2）

- **范围**：词法、header、全部语句与表达式、emit payload、AST、加载期名字/头部/arity 校验、统一错误格式。不含任何执行语义。
- **依赖**：Phase 0 的 `tools/check.sh`/`tools/check-all.sh` 基线（g3/g5/g7/g8 当前 DISABLED，本 phase 收口启用）；CT 工具链；构建骨架由 PH-1 T01 建立；T-001..T-006 的静态元数据。Phase 0 未交付则不开工。
- **退出条件**：PH-1 卡 §9 全绿；`tools/check-phase1.sh --all` 与 `tools/check-all.sh` 退出 0；S-001..S-024 每条至少 1 个 case；五个 08 示例 AST golden 相等；每个任务有红证。
- **与 09 的关系**：覆盖 M1+M2，并提前落地 M5/M7 的静态子集（arity/注入/递归/遮蔽/header 默认拒绝）；M1 的 token golden 与 M2 的 AST/加载负例都在 Phase 1 门禁内，运行期部分仍留在 M5/M7。

### Phase 2：执行器核心（09 M3）

- **范围**：六类值、`let`/`let mut`/赋值、`if`/`for`/`break`/`continue`、`ExecLimits`、`DslResult`、错误格式的运行期半边。工具调用用 fake 工具，不接真实文件系统。
- **依赖**：PH-1 收口；值模型与 `DslResult` 接口在 PH-2 卡中写死；PH-1 的 AST 与诊断不反复改。
- **退出条件**：赋值 4 类错误、循环 2 类、条件 1 类、步数/调用数超限 `limit` 全部有负例并转绿；`let mut` 成功用例可观察值；`for` 空数组 0 次；`continue` 不重置步数。
- **与 09 的关系**：对应 M3；09 §4 的“M3 起统一错误格式”在本 phase 兑现运行期部分。

### Phase 3：管道与降级（09 M4）

- **范围**：R1 隐式 await、R2 管道追加、`\|?` 优先级与失败单元、R4 失败行为表、`degraded` 回显。仍用 fake 工具，可控返回 `error_kind`。
- **依赖**：PH-2 收口；PH-1 的 `pipe_rhs`/`fallback_lhs` 静态检查已绿；D-007/D-010 不改。
- **退出条件**：`a \|> f b \|? g c`、`read p \|? read f \|> json_parse`、`a \|? b \|? c`、`f (a \|> b) \|? c` 四条求值轨迹 golden；可捕获/不可捕获各 2 例；`degraded` 与实际接管一致；副作用不回滚有 1 例。
- **与 09 的关系**：对应 M4；09 §2 的 M4 退出判据逐条落到本 phase 门禁。

### Phase 4：`into` + `$` + `fn`（09 M5）

- **范围**：`into` 的词法绑定、嵌套覆盖/恢复、`$` 只读与块外错误、`fn` 定义/调用/return、闭包只读、调用图无环、注入矩阵与 `arity`。
- **依赖**：PH-2 收口；PH-3 的管道求值可用于 `fn` 返回值；PH-1 已做静态注入计数与调用图，本 phase 只补运行期绑定。
- **退出条件**：注入矩阵 3 例（`n<m`、不接受 context、变长）全绿；嵌套 `into` 覆盖/恢复 1 例；`$` 只读负例 1 例；递归与遮蔽工具名负例各 1 例；`fn` 参数值拷贝可观察。
- **与 09 的关系**：对应 M5；D-017 的嵌套 `into` 与 D-007 的注入规则在本 phase 首次可运行。

### Phase 5：截断 + emit + 事件总线（09 M6）

- **范围**：截断侧车 `(payload, meta)`、伪字段优先、`get` 逃逸、粘性传播、`original_size` 两种字节口径；emit fire-and-forget、事件声明、`max_emit_bytes`/`max_payload_depth`；脚本侧不做 schema 校验（schema 由内核配置）。
- **依赖**：PH-2/P3 收口；PH-1 已解析 emit payload 与加载期 `dup_key`（emit 字面量重复键）；PH-4 的 `$` 可用于 payload 值。
- **退出条件**：伪字段/逃逸/粘性/字节口径 6 例；emit 无订阅方/队列满、字节与深度超限各 1 例；`external_egress` 1 例；meta 不泄漏进 `args_json`；超限不得静默丢弃。
- **与 09 的关系**：对应 M6；09 §2 的 M6 退出判据全部在本 phase 门禁内。

## 3. 跨阶段硬约束

| # | 约束 | 判据 |
| --- | --- | --- |
| R-1 | 不移动 DSL 规范版本 `v0.1 rev.1`；不改 `docs/spec/dsl/` 正文与 `docs/decisions/` | 每 phase 收口 `git diff --name-only` 不含这些路径；改则先开 CR/D-* |
| R-2 | 每个 phase 至少一个可运行样例，纳入真实门禁 | `tools/check-phase<n>.sh --all` 与 `tools/check-all.sh` 退出 0；样例在 `examples/phase<n>/` |
| R-3 | 先红后绿；纯文档任务写 `no-test: <理由>` | 每个实现任务有 `test` 父提交与 `red: rc=…`；无红证的断言不计覆盖 |
| R-4 | 小步提交：一项任务一个交付物、一次提交、可单独回滚 | 实现 diff 目标 ≤300 行；超限先拆任务；仓库随时可构建 |
| R-5 | 文法未冻结不写解释器；安全在语义闭环之后 | PH-1 只做解析/加载；PH-2 起才有执行器；M7 安全排在 PH-5 之后 |
| R-6 | Phase 3/4 可并行，默认串行 | 若并行，两 phase 不得同时改 `src/loader.ct` 的共享接口；冲突由 EDITOR 重排 |

## 4. 依赖与风险

| 项 | 内容 | 触发信号 / 处置 |
| --- | --- | --- |
| Phase 0 | `tools/check.sh`/`tools/check-all.sh` 门禁基线、`docs/session-map.md`、版本落点；构建骨架由 PH-1 建立；g3/g5/g7/g8 由 Phase 1 启用 | 缺任一：PH-1 不开工；由 G0/G1 拦 |
| CT 工具链 | 编译器版本固定；无网络依赖 | 构建失败即 P0，先修 Phase 0 |
| registry 元数据 | T-001..T-006 的 arity/`accepts_context`/变长 | 元数据变更 → PH-1 的 arity golden 同步；不得只改实现 |
| 规范演进 | AST/位置已由 10 卷/D-020 冻结；`# approval:` 按注释、`unknown_callee` 已合并入 `unknown_tool` | 10 卷变更时 PH-1 golden 同步；不得在卡内另立 AST 形态 |
| 排期压缩 | Phase 1 合并 M1+M2，工作量大于 09 的单 M | 任务清单已按 12 片切分；任一片超一轮则先拆，不延长 phase 判据 |
| 真实 LLM 验证 | M10 不在 Phase 1–5 | 不得用“解析 golden 全绿”宣称 LLM 可用性；M10 另立 phase |

## 5. 未纳入本排期的里程碑

09 的 M7（三层白名单/快照/审批）、M8（参数约束）、M9（诊断全覆盖）、M10（真实 LLM 验证）不在 Phase 1–5。它们的前置是 Phase 5 收口；其中 M7 必须等语义闭环与样例稳定后再开工（09 §1 原则 2）。M9 的一部分由 Phase 1 的 `ER-*` 与 Phase 2 的运行期错误格式提前覆盖，但“每种 `error_kind` 至少 1 个 golden”的完整判据仍留在 M9。
