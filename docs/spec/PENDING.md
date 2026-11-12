# 待定条目（Pending）

> 状态：**大部分仍 pending**。已拍板项为 [D-001](../decisions/D-001.md)、[D-002..D-020](../decisions/README.md)；规范正文 [docs/spec/dsl/](dsl/README.md) 为 `v0.1 rev.1`（unverified）。
> 下表逐行标注状态；标 `decided → D-xxx` 的条目可被引用，标 `partial` 的只对已列子项生效，其余仍 pending。
> `undecidable` 项（P-020、P-021）没有决策记录，重开条件写在对应行。

## 1. 与用户问题清单的对应

| 用户问题 | 待定 ID | 主题 | 状态 |
| --- | --- | --- | --- |
| Q1 | P-001 | 是否采纳 P0-1..P0-10 的文法修复 | partial：P0-1/2/3/4/5/6/9 已定（D-002..D-006）；P0-7/8/10 仍 pending |
| Q2 | P-002 | `postfix ()` 是否彻底删除 | decided → D-005 |
| Q3 | P-003 | 是否允许 `IDENT = expr` 赋值语句 | decided → D-009 |
| Q4 | P-004 | 截断结果元数据的暴露方式 | decided → D-008（C 方案） |
| Q5 | P-005 | `# allow:` 缺省是否改为默认拒绝 | decided → D-011（默认拒绝） |
| Q6 | P-006 | 审批节点放内核还是 DSL | decided → D-013（内核） |
| Q7 | P-007 | `par` 是否进入保留字 | decided → D-019 |
| Q8 | P-008 | 错误格式是否统一为 CT 的 `path:line:col: error:` | decided → D-015 |
| Q9 | P-009 | `# dsl-version:` 是否 MVP 直接报错 | decided → D-018 |
| Q10 | P-010 | 是否保留嵌套 `into` 与 `$` 覆盖规则 | decided → D-017 |

## 2. 待定清单

| ID | 待定问题 | 现状 | 影响 | 关联 |
| --- | --- | --- | --- | --- |
| P-001 | P0-1..P0-10 的文法修复是否整体采纳 | **partial**：P0-1 负数 → D-003；P0-2 NEWLINE → D-004；P0-3 实参 → D-002；P0-4 emit → D-006；P0-5 `()` → D-005；P0-6 字段实参 → D-002；P0-9 示例 3 → D-002/D-004。P0-7（关键字/字段名冲突）只定了“禁止遮蔽工具名”；P0-8、P0-10 未定 | M1 文法主体已可落地，保留字与错误格式仍缺 | [讨论稿 P0-1..P0-10](../design/dsl-discussion.md#L82-L217) |
| P-002 | `postfix ()`（`f()()`、`a.b()`）是否删除 | **decided → D-005**：删除；零参写裸名；禁止局部绑定遮蔽工具名 | 表达式文法、M1 AST | [讨论稿 P0-5](../design/dsl-discussion.md#L153-L167) |
| P-003 | 是否允许 `IDENT = expr` 赋值 | **decided → D-009**：允许，限 `let mut` 局部；赋值只存不建名 | M4 | [讨论稿 P1-1](../design/dsl-discussion.md#L238-L247) |
| P-004 | 截断元数据如何暴露 | **decided → D-008**：C 方案（侧车伪字段 + 粘性传播） | 工具边界、管道、JSON 冲突 | [讨论稿 §2.2](../design/dsl-discussion.md#L52-L69) |
| P-005 | `# allow:` 缺省是否默认拒绝 | **decided → D-011**：默认拒绝；`*` 显式逃生并审计；deny-only 报错 | 安全默认值 | [讨论稿 P1-8](../design/dsl-discussion.md#L307-L316) |
| P-006 | 审批节点放内核还是 DSL | **decided → D-013**：内核；DSL 零审批语法 | DSL 语法面 | [讨论稿 P1-9](../design/dsl-discussion.md#L317-L324) |
| P-007 | `par` 是否进入保留字 | **decided → D-019**：保留；脚本出现即 `not_implemented`，Hint 指向内核调度 | 词法保留字表 | [D-019](../decisions/D-019.md) |
| P-008 | 错误格式统一为 CT `path:line:col: error:` 还是 v0.1 格式 | **decided → D-015**：统一 `path:line:col: error:` + 详情 + Hint；只报第一个错误 | 全部错误输出与 M1 基线 | [D-015](../decisions/D-015.md) |
| P-009 | `# dsl-version:` 是否 MVP 直接报错 | **decided → D-018**：接受 `1`；其他值 `E_VERSION` | header 文法 | [D-018](../decisions/D-018.md) |
| P-010 | 是否保留嵌套 `into` 与内层 `$` 覆盖 | **decided → D-017**：允许；内层 `$` 覆盖、退出恢复；理由是不做编译期脱糖 | M5 作用域 | [D-017](../decisions/D-017.md) |
| P-011 | `while` / `break` / `continue` 是否进 M4 | **decided → D-009**：`for` + `break`/`continue` 进 M4；`while` 不进 MVP；重开条件见 D-009 | M4 | [讨论稿 P1-1](../design/dsl-discussion.md#L238-L247) |
| P-012 | `\|?` 的优先级、失败单元、右侧形态、与 `$` 的先后 | **decided → D-007**：`\|?` 高于 `\|>`；左侧单 call；可捕获集显式；`$` 按形参位注入 | M3 | [讨论稿 §2.3](../design/dsl-discussion.md#L70-L80) |
| P-013 | 错误信息升级（Did-you-mean、片段、插入符） | pending | M1/M9 | [讨论稿 P1-3](../design/dsl-discussion.md#L261-L268) |
| P-014 | 事件因果链 `event_trace` 接口 | pending；与 D-012 的订阅方快照取点相邻 | 事件总线 | [讨论稿 P1-6](../design/dsl-discussion.md#L285-L298) |
| P-015 | 白名单热更新的策略快照语义 | **decided → D-012**：不可变快照 + 下一次工具调用边界强杀 | 加载/执行一致性 | [讨论稿 P1-7](../design/dsl-discussion.md#L299-L306) |
| P-016 | 「Rill 在 agent 运行时中的位置」一节是否写入规范 | **decided → D-013**（第 8 条）：写入，附一条归属规则 | 内核职责边界 | [讨论稿 P1-4](../design/dsl-discussion.md#L269-L276) |
| P-017 | MVP 不做并行是否写成规范条款 | pending | 能力边界 | [讨论稿 P1-10](../design/dsl-discussion.md#L325-L332) |
| P-018 | 工具/函数同名解析、零参调用、嵌套实参 | **partial**：嵌套实参与括号单原子 → D-002；零参与工具名遮蔽 → D-005；关键字/字段名冲突仍 pending | S-001 边界、M1/M6 | [讨论稿 §2.1](../design/dsl-discussion.md#L44-L50) |
| P-019 | 截断与重试如何落成正式规格 | **partial**：方向已被 D-007/D-008 固定；尚未新增对应 `S-*` 与验收判据 | M2/M3 | [讨论稿 §2.2/§2.3](../design/dsl-discussion.md#L52-L80) |
| P-020 | 外部授权主体（`principal_id` + `grant_set`）能否约束 `# allow:` 自授权 | **undecidable**：需改 `dsl_exec` 签名与主体模型，无用户拍板。重开条件：首次多租户部署，或内核接口 CR 明确主体字段；届时按“header 是能力请求、外部集是授予”重建 B3-1 | 默认拒绝的诚实边界 | [D-011](../decisions/D-011.md)、[D-013](../decisions/D-013.md)、[B3 反证席 §2](../../battle/B3/seats/challenger.md) |
| P-021 | 跨 exec payload 的污点/能力标签（taint） | **undecidable**：规范无主体、无标签模型。重开条件：启用外部 webhook 订阅方，或发生“低权脚本经事件把数据送入特权工具”的事件 | emit `external_egress` 的后续 | [D-014](../decisions/D-014.md)、[B3 反证席 §5](../../battle/B3/seats/challenger.md) |
| P-022 | `# emit:` 是否在脚本里声明 payload schema | **decided（本轮裁定）**：不进脚本 header；schema 由内核配置按事件名提供，未声明不校验。理由：MVP 不为 schema 造语法，且与 emit payload 字面量重复 | M6 的 schema 用例 | [05 §2.2](dsl/05-data-metadata.md)、[D-014](../decisions/D-014.md) |

## 3. 状态规则

- 行内标 `decided → D-xxx` 的条目可被实现、测试与门禁引用；标 `partial` 的只对行内列出的子项生效。
- 标 `undecidable` 的条目**没有**决策记录，不得写成规则；只有重开条件满足后才可另立决策。
- 拍板后新增 `docs/decisions/D-<n>.md`；需要对外行为的再新增 `docs/spec/S-<n>.md`（P-019 尚未建 S）。
- 与本文件相关的候选偏离（DOC-S2/G0/G4/T-7）见 [主张层 §6](../requirements/README.md)。
