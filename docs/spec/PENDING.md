# 待定条目（Pending）

> 状态：**全部 pending，未定稿**。
> 当前唯一已拍板项是 [D-001](../decisions/D-001.md)（调用统一空格）。
> 下表的 Q1–Q10 与 P0/P1 问题**没有** accepted 决策，也没有验收判据；不得作为已生效规则引用。
> 各方意见与倾向见 [dsl-discussion.md](../design/dsl-discussion.md)。

## 1. 与用户问题清单的对应

| 用户问题 | 待定 ID | 主题 |
| --- | --- | --- |
| Q1 | P-001 | 是否采纳 P0-1..P0-10 的文法修复 |
| Q2 | P-002 | `postfix ()` 是否彻底删除 |
| Q3 | P-003 | 是否允许 `IDENT = expr` 赋值语句 |
| Q4 | P-004 | 截断结果元数据的暴露方式 |
| Q5 | P-005 | `# allow:` 缺省是否改为默认拒绝 |
| Q6 | P-006 | 审批节点放内核还是 DSL |
| Q7 | P-007 | `par` 是否进入保留字 |
| Q8 | P-008 | 错误格式是否统一为 CT 的 `path:line:col: error:` |
| Q9 | P-009 | `# dsl-version:` 是否 MVP 直接报错 |
| Q10 | P-010 | 是否保留嵌套 `into` 与 `$` 覆盖规则 |

## 2. 待定清单

| ID | 待定问题 | 现状 | 影响 | 关联 |
| --- | --- | --- | --- | --- |
| P-001 | 负数词法、NEWLINE、实参歧义、emit 对象字面量、`()` 矛盾、示例 3、字段实参、关键字保留等 P0 修复是否整体采纳 | 未拍板；评审给出反例与修法方向 | 决定 M1 能否稳定解析；不采纳则 M1 无确定文法 | [讨论稿 P0-1..P0-10](../design/dsl-discussion.md#L82-L217) |
| P-002 | `postfix ()`（`f()()`、`a.b()`）是否删除 | 用户已定调用统一空格；删除属技术推论，未单独拍板 | 影响表达式文法、链式调用边界、M1 AST | [讨论稿 P0-5](../design/dsl-discussion.md#L153-L167) |
| P-003 | 是否允许 `IDENT = expr` 赋值 | 未拍板；v0.1 只有 `let`，while 无法改变条件 | 决定 while 是否可用、M4 范围 | [讨论稿 P1-1](../design/dsl-discussion.md#L238-L247) |
| P-004 | 截断元数据 `{ value, truncated, original_size }` 如何暴露 | 用户已定“截断不进 DSL 语法、字段访问可读 truncated”；A/B/C/D 四种暴露方式未定 | 影响所有工具返回值、管道传值、JSON 字段冲突 | [讨论稿 §2.2](../design/dsl-discussion.md#L52-L69)、[P1-2](../design/dsl-discussion.md#L248-L260) |
| P-005 | `# allow:` 缺省是否默认拒绝 | 未拍板；v0.1 是“继承注册表级” | 安全默认值；改则改变已写脚本行为 | [讨论稿 P1-8](../design/dsl-discussion.md#L307-L316) |
| P-006 | 审批节点放内核还是 DSL | 未拍板；倾向内核 | 决定 DSL 是否需要 `approve` 类语法 | [讨论稿 P1-9](../design/dsl-discussion.md#L317-L324) |
| P-007 | `par` 是否进入保留字 | 未拍板；评审建议预留 | 影响词法保留字表与错误信息 | [讨论稿 P1-5](../design/dsl-discussion.md#L277-L284) |
| P-008 | 错误格式统一为 CT `path:line:col: error:` 还是保留 v0.1 `Error at line N, col M` | 未拍板；倾向对齐 CT | 影响所有解析/加载/运行错误与 M1 测试基线 | [讨论稿 P0-10](../design/dsl-discussion.md#L208-L217) |
| P-009 | `# dsl-version:` 是否 MVP 直接报错 | 未拍板；倾向报错而非静默 | 影响 header 文法与版本策略 | [讨论稿 P0-8](../design/dsl-discussion.md#L188-L197) |
| P-010 | 是否保留嵌套 `into` 与内层 `$` 覆盖 | 未拍板；v0.1 要求嵌套，CT 禁止嵌套 | 影响 M5 作用域实现与“复用 CT”表述 | [讨论稿 P0/P1、§5](../design/dsl-discussion.md#L236-L347) |
| P-011 | `while` / `break` / `continue` 是否进 M4，循环语义如何定义 | 未拍板；评审建议进 M4 | 决定控制流能力与 M4 排期 | [讨论稿 P1-1](../design/dsl-discussion.md#L238-L247) |
| P-012 | `|?` 的优先级、失败单元、右侧形态、与 `$` 的先后 | 用户已定“`|?` 唯一降级形态、重试次数走工具参数”；语义细节未定 | 影响 M3 求值顺序与错误传播 | [讨论稿 §2.3](../design/dsl-discussion.md#L70-L80)、[P0-11](../design/dsl-discussion.md#L218-L235) |
| P-013 | 错误信息升级：Did-you-mean、源码片段、插入符、相似写法示例 | 未拍板；评审建议采纳 | 影响 M1/M9 错误输出与 LLM 自纠错 | [讨论稿 P1-3](../design/dsl-discussion.md#L261-L268) |
| P-014 | 事件因果链 `event_trace` 接口（trace_id 生成/传播/查询/保留） | 未拍板；有提案 | 影响事件总线接口与跨脚本追踪 | [讨论稿 P1-6](../design/dsl-discussion.md#L285-L298) |
| P-015 | 白名单热更新的策略快照语义 | 未拍板；有提案（执行中用加载快照） | 影响加载/执行一致性与撤销延迟 | [讨论稿 P1-7](../design/dsl-discussion.md#L299-L306) |
| P-016 | 「Rill 在 agent 运行时中的位置」一节是否写入规范 | 未拍板；有提案 | 明确内核职责与单次执行边界 | [讨论稿 P1-4](../design/dsl-discussion.md#L269-L276) |
| P-017 | MVP 不做并行的取舍是否写成规范条款；`par` 后续能力 | 未拍板；评审建议明写 | 影响任务能力边界与用户预期 | [讨论稿 P1-10](../design/dsl-discussion.md#L325-L332) |
| P-018 | 工具/函数同名解析、零参调用、嵌套实参与括号单原子 | 未拍板；只有倾向（空格应用不递归、括号分组） | 决定 S-001 的完整边界与 M1/M6 实现 | [讨论稿 §2.1](../design/dsl-discussion.md#L44-L50)、[P0-3](../design/dsl-discussion.md#L120-L137) |
| P-019 | 截断与重试的用户更正如何落成正式规格 | 用户已给方向：截断走工具参数、重试走 `|?`；尚无对应 `S-*` 与验收判据 | 决定是否新增 S-002/S-003，以及 M2/M3 范围 | [讨论稿 §2.2/§2.3](../design/dsl-discussion.md#L52-L80) |

## 3. 状态规则

- 本文件所有条目 `status = pending`，不写 `verdict`，不写 `judge`。
- 拍板后：新增 `docs/decisions/D-<n>.md`，把对应行改为指向该决策；需要对外行为的再新增 `docs/spec/S-<n>.md`。
- 在拍板前，任何实现、测试或门禁都不得把这里的条目当作已生效规则。
- 与本文件相关的候选偏离（DOC-S2/G0/G4/T-7）见 [主张层 §6](../requirements/README.md)。
