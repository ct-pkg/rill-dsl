# 待定条目（Pending）

> 状态：P-013、P-014 仍 pending；P-020、P-021 为 undecidable；其余条目已收口。已拍板项为 [D-001](../decisions/D-001.md)、[D-002..D-020](../decisions/README.md)；规范正文 [docs/spec/dsl/](dsl/README.md) 为 `v0.1 rev.1`（unverified）。
> 下表逐行标注状态；标 `decided → D-xxx` 的条目可被引用，标 `partial` 的只对已列子项生效，其余仍 pending。
> `undecidable` 项（P-020、P-021）没有决策记录，重开条件写在对应行。

## 1. 与用户问题清单的对应

| 用户问题 | 待定 ID | 主题 | 状态 |
| --- | --- | --- | --- |
| Q1 | P-001 | 是否采纳 P0-1..P0-10 的文法修复 | decided：P0-1/2/3/4/5/6/9 → D-002..D-006；P0-7 由 01/02 的保留字与 07 的 `reserved_name` 覆盖；P0-8 → D-018；P0-10 → D-015 |
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
| P-001 | P0-1..P0-10 的文法修复是否整体采纳 | **decided**：P0-1 → D-003；P0-2 → D-004；P0-3 → D-002；P0-4 → D-006；P0-5 → D-005；P0-6 → D-002；P0-9 → D-002/D-004；P0-7 关键字/字段名冲突 → 01/02 保留字 + 07 `reserved_name`；P0-8 → D-018；P0-10 → D-015 | M1 文法主体可落地 | [讨论稿 P0-1..P0-10](../design/dsl-discussion.md#L82-L217) |
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
| P-017 | MVP 不做并行是否写成规范条款 | **decided → D-019**：`par` 保留为关键字、出现即 `not_implemented`；README §4 列为非目标 | 能力边界 | [D-019](../decisions/D-019.md) |
| P-018 | 工具/函数同名解析、零参调用、嵌套实参 | **decided**：嵌套实参与括号单原子 → D-002；零参与工具名遮蔽 → D-005；关键字/字段名冲突 → 01/02 保留字（`into` 等）+ 07 `reserved_name`；裸名命中带参 `fn` → `bare_fn_ref`。锚点：[S-005](S-005-parens-zero-arg.md)、[02 §3](dsl/02-grammar.md)、[03 §2](dsl/03-semantics.md)（无独立 D 记录） | S-001/S-005、M1/M6 | [讨论稿 §2.1](../design/dsl-discussion.md#L44-L50) |
| P-019 | 截断与重试如何落成正式规格 | **decided**：方向由 D-007/D-008 固定；验收已建 [S-009](S-009-truncation.md)（9000 字节、粘性、逃逸、分组） | M2/M3 | [S-009](S-009-truncation.md) |
| P-020 | 外部授权主体（`principal_id` + `grant_set`）能否约束 `# allow:` 自授权 | **undecidable**：需改 `dsl_exec` 签名与主体模型，无用户拍板。重开条件：首次多租户部署，或内核接口 CR 明确主体字段；届时按“header 是能力请求、外部集是授予”重建 B3-1 | 默认拒绝的诚实边界 | [D-011](../decisions/D-011.md)、[D-013](../decisions/D-013.md)、[B3 反证席 §2](../../battle/B3/seats/challenger.md) |
| P-021 | 跨 exec payload 的污点/能力标签（taint） | **undecidable**：规范无主体、无标签模型。重开条件：启用外部 webhook 订阅方，或发生“低权脚本经事件把数据送入特权工具”的事件 | emit `external_egress` 的后续 | [D-014](../decisions/D-014.md)、[B3 反证席 §5](../../battle/B3/seats/challenger.md) |
| P-022 | `# emit:` 是否在脚本里声明 payload schema | **decided（本轮裁定）**：不进脚本 header；schema 由内核配置按事件名提供，未声明不校验。理由：MVP 不为 schema 造语法，且与 emit payload 字面量重复 | M6 的 schema 用例 | [05 §2.2](dsl/05-data-metadata.md)、[D-014](../decisions/D-014.md) |
| P-023 | `# allow:` 含未注册的工具/函数名是否报错 | **decided**：不报错；白名单只收窄不校验，未注册名不授权、等同没写，不产生任何加载期 kind。内核可 lint 提示但不得拒绝脚本。依据：[06 §2](dsl/06-security.md)、[D-011](../decisions/D-011.md)（无独立 D 记录） | 加载期校验边界 | [06 §2](dsl/06-security.md) |
| P-024 | `rillShell` 与现行入口 `ct/bin/rill` 的命名关系：是否改名、是否合并为同一二进制 | **pending**（D-021 明确留作未决，不在 D-021 内拍）。缺的是：产品对外名称与二进制分发形态的取舍，属用户裁定 | 入口名与发布形态 | [D-021](../decisions/D-021.md) |
| P-025 | 值里的 `类型:值` 前缀（TypeRegistry）是否进入函数签名：常量位带类型前缀时算常量还是参数位 | **pending**（D-022 未拍）。缺的是：类型前缀在 AST 的落点与加载期拆分时机，需先定 §五 TypeRegistry 的接口 | 函数签名匹配 | [D-022](../decisions/D-022.md) |
| P-026 | 去掉函数名后的迁移：现网 `@ "name"` 脚本与测试语料如何改，语言规范版本记 0.1.2 还是 0.2.0 | **pending**（D-022 未拍）。缺的是：破坏性变更的发布口径与语料迁移排期，属发布裁定 | 版本与迁移 | [D-022](../decisions/D-022.md) |

## 3. 状态规则

- 行内标 `decided → D-xxx` 的条目可被实现、测试与门禁引用；标 `partial` 的只对行内列出的子项生效。
- 标 `undecidable` 的条目**没有**决策记录，不得写成规则；只有重开条件满足后才可另立决策。
- 拍板后新增 `docs/decisions/D-<n>.md`；需要对外行为的再新增 `docs/spec/S-<n>.md`。
- 与本文件相关的候选偏离（DOC-S2/G0/G4/T-7）见 [主张层 §6](../requirements/README.md)。
