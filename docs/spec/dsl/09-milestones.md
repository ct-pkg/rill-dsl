# 09 里程碑

> 规范版本 `v0.1 rev.1`；状态 `unverified`。里程碑是排期与验收顺序，不是已实现事实。

## 1. 重排原则

1. 先词法/文法，再执行器；文法未冻结前不写解释器。
2. 安全（三层 + 快照 + 审批 + 约束）放在语义闭环之后、真实 LLM 验证之前；没有安全的样例不得进真实任务。
3. 每个里程碑必须交付**至少一个可运行样例**，并纳入真实门禁（golden 或 `tools/check.sh` 子命令）；只写代码不留样例的里程碑不算完成。
4. 数字是估算，不是承诺；不得用估算行数代替退出判据。

## 2. 里程碑

| M | 交付 | 退出判据 | 样例 | 估算 |
| --- | --- | --- | --- | --- |
| M0 | 文档基线：链接门禁、规范 pin、snippet 管线、`docs/session-map.md` | `tools/check-docs.sh` 与 `tools/check.sh g1` 存在且全绿；本目录 10 份文档链接无断链 | 无代码 | 300 行脚本 |
| M1 | Lexer：token、NEWLINE N1–N8、注释、数字、字符串、错误位置 | token golden 全绿（[02 §6](02-grammar.md) 判定表 + 数字/换行/注释夹具）；未闭合定界符报 `syntax` | `examples/m1-tokens/`（源码 + 期望 token 流） | 900 |
| M2 | Parser：header、全部语句、完整表达式、emit payload、静态检查骨架 | AST golden 全绿；五个示例全部解析成功；`E_DUP_KEY`/`E_DUP_HEADER`/`E_VERSION` 有负例 | `examples/m2-parse/`（五个示例 + 判定表） | 1500 |
| M3 | 执行器核心：值模型、`let`/`let mut`/赋值、`if`/`for`/`break`/`continue`、`ExecLimits`、`DslResult`、错误格式 | 赋值 4 类错误、循环 2 类错误、条件 1 类错误全部有负例；步数/调用数超限返回 `limit` | `examples/m3-control/` + fake 工具 | 1400 |
| M4 | 管道与降级：`\|>`、`\|?`、R4 失败行为表、`degraded` | 求值轨迹 golden 4 例；可捕获/不可捕获各 2 例；`E_PIPE_RHS`/`E_FALLBACK_LHS` 负例 | `examples/m4-pipeline/` | 700 |
| M5 | `into` + `$` + `fn`：注入规则、闭包只读、调用图无环、`E_ARITY` | 注入矩阵（n<m/不接受 context/变长）3 例；递归与遮蔽工具名负例 | `examples/m5-into-fn/` | 800 |
| M6 | 截断 + emit + 事件总线：侧车元数据、粘性、`max_emit_bytes`/`max_payload_depth` | 伪字段/逃逸/粘性/字节口径 6 例；emit 无订阅方/队列满、字节与深度超限各 1 例（schema 校验由内核配置，不在脚本 golden 内） | `examples/m6-events/` | 700 |
| M7 | 三层白名单 + 策略快照 + 审批 | 默认拒绝/deny-only/`*` 审计/快照跨代/强杀/审批 4 类错误全部有负例 | `examples/m7-security/` | 1000 |
| M8 | 参数约束：路径五件套、argv、域名八例、双通道、重复键 | 夹具逐条通过；`E_CONSTRAINT`/`E_UNCONSTRAINED_ARG`/`E_DUP_KEY` 负例 | `examples/m8-constraints/` | 800 |
| M9 | 诊断：统一格式、Hint、`error_kind` 全覆盖 | 每条 `error_kind` 至少 1 个 golden；格式字段齐全 | `examples/m9-errors/` | 500 |
| M10 | 示例与真实 LLM 验证：五个示例 + 10 个真实任务 | 五个示例全部可运行；token 比裸 JS 低 ≥60%；语法错误率 <20% | `examples/` 全量 + 统计报告 | 400 |

## 3. 真实 LLM 验证

- 任务集：读文件、搜索、条件写、多文件处理、配置解析（同旧文 §12）。
- 每个任务固定模型、温度、提示；原始输出与统计必须落盘，不得只写结论。
- 判定只看两项：token 消耗与首次解析失败率；两项任一未达标，回到对应里程碑的夹具修文法，不得调低阈值。

## 4. 与旧文的差异

| 旧 | 新 | 原因 |
| --- | --- | --- |
| M1 含工具调用 + let + 字段访问 | M1 只做 lexer，M2 做 parser | 词法/文法分开，NEWLINE 与 emit payload 需要独立 golden |
| M4 `if/for` 无赋值与循环控制 | M3 含 `let mut`、赋值、break/continue | D-009 把赋值与循环控制纳入 MVP |
| M8 只做三层白名单 | M7 快照 + 审批，M8 参数约束 | D-012/D-013/D-014 把快照、审批、约束分档拆开 |
| M9 错误报告最后做 | M3 起统一格式，M9 补全覆盖 | 错误格式是执行器接口，不能最后补 |

## 5. 验收锚点

- 样例路径：S 条目覆盖 M1–M9；M0 与 M10 的产物直接写在里程碑表，不强制映射到 S 条目。
- 在 `tools/check.sh` 落地前，所有验收命令写 `尚未落盘`，不得标 `accepted`。
