# Rill DSL 规范 v0.1 rev.1

- **状态**：`unverified` —— 本仓库没有 lexer/parser/解释器，正文中的行为均无门禁证据。
- **规范版本**：仍为 `v0.1`；本轮改动标记 `rev.1`（2026-11-12）。**不升版本号**，不新增其他版本编号。
- **依据**：D-001、D-002..D-014（B1/B2/B3 battle 判决）、D-015（错误格式）、D-020（AST 与位置），其余见各卷。
- **历史输入**：[dsl-spec-v0.1.md](../../design/dsl-spec-v0.1.md)（v0.1 原文，只归档不改写）。
- **可验收条目**：[S-001..S-024](../README.md)；工具契约见 [T-001..T-006](../tools/README.md)。每条状态 `unverified`。
- **未决项**：[PENDING.md](../PENDING.md)。

## 1. 分卷与阅读顺序

| 卷 | 内容 | 主要依据 |
| --- | --- | --- |
| [01 词法](01-lexical.md) | 源文本、token、关键字、数字、字符串、注释、NEWLINE N1–N8 | D-003、D-004 |
| [02 文法](02-grammar.md) | 程序、header、语句、完整 EBNF、emit payload | D-001、D-002、D-005、D-006 |
| [03 语义](03-semantics.md) | 值模型、名字解析、let/赋值、if/for、fn、into/$、调用 | D-002、D-005、D-009 |
| [04 管道与错误](04-pipeline-errors.md) | `\|>`、`\|?`、R1/R2/R4、失败行为表、`degraded` | D-007、D-010 |
| [05 数据与事件](05-data-metadata.md) | 截断元数据、emit、事件总线上限 | D-008、D-006、D-014 |
| [06 安全](06-security.md) | 三层白名单、默认拒绝、策略快照、审批、约束分档 | D-011..D-014 |
| [07 运行时](07-runtime.md) | 接口、ExecLimits、错误格式、版本策略 | D-010、D-013、D-014、D-015 |
| [08 示例](08-examples.md) | 五个示例及新文法下的解析说明 | D-002、D-006、D-009 |
| [09 里程碑](09-milestones.md) | M0–M10 重排、退出判据、样例门禁 | 全部决策 |
| [10 AST 与位置](10-ast-position.md) | 节点集合、稳定 S-expression、位置口径、错误阶段 | D-020 |

## 2. 规范用语

- **必须（MUST）**：实现必须满足，否则加载失败或验收不通过。
- **不得（MUST NOT）**：出现即缺陷。
- **建议（SHOULD）**：实现可偏离，但必须在 `D-*` 或 `P-*` 记录理由。
- 文中 `[D-xxx]` 指向决策记录；`[P-xxx]` 指向未决条目。未决项以 [PENDING](../PENDING.md) 为唯一登记处；正文只在必要处引用编号，不把未决项写成规则。

## 3. rev.1 变更记录

| # | 变更 | 依据 |
| --- | --- | --- |
| 1 | 调用统一空格；`arg := postfix_atom`，空格应用不递归；嵌套加括号 | D-001、D-002 |
| 2 | 数字不带符号；`-` 只作运算符 | D-003 |
| 3 | NEWLINE 作语句终止符，N1–N8 抑制 | D-004、D-006 |
| 4 | 删除 postfix `()`；零参写裸名；禁止遮蔽工具名 | D-005 |
| 5 | emit payload 用受限 JSON 字面量；JSON 内换行忽略 | D-006 |
| 6 | `\|?` 高于 `\|>`；左操作数单 call；可捕获集显式 | D-007 |
| 7 | 截断元数据用侧车伪字段，粘性传播 | D-008 |
| 8 | 赋值限 `let mut`；for 变量不可变；break/continue；无 while | D-009 |
| 9 | R4 改为“调用级降级、无块级恢复” | D-010 |
| 10 | `# allow:` 缺省默认拒绝；`*` 显式且审计；deny-only 报错 | D-011 |
| 11 | 策略热更新用不可变快照 + 调用边界强杀 | D-012 |
| 12 | 审批在内核；DSL 零审批语法；边界一节 | D-013 |
| 13 | 参数约束按必做/不做/deferred 分档 | D-014 |
| 14 | 错误格式统一为 `path:line:col: error:` + 详情 + Hint（裁判席技术裁定，用户未参与） | D-015 |
| 15 | 文档自相矛盾处同步：§2 不再说“不引入 ()”，§3.3 不再有两套调用语法 | D-001、D-005 |
| 16 | 值层补 `string + 标量` 拼接与 `json_array.length` | D-016 |
| 17 | `into` 允许嵌套，内层 `$` 覆盖、退出恢复 | D-017 |
| 18 | `# dsl-version:` 接受 `1`，其他值加载报错 | D-018 |
| 19 | `par` 保留为关键字，出现即 `not_implemented` | D-019 |
| 20 | 运行时补 `requires_complete_input` 与 `max_input_bytes`；`max_payload_depth` 泛化为通用深度上限；`arity` 前移到加载期并覆盖工具（含 `json_build` 偶数实参）；`constraint`/`invalid_input`/`limit` 按判定者与截断归属对齐；`args_json`/`ctx_json` 两通道互斥 | 工具契约 T-001..T-006 跟进项 |
| 21 | header 只认 `allow`/`deny`/`emit`/`dsl-version` 四种前缀，其余 `#` 行（含 `# approval:`）按注释 | D-013、D-020 |
| 22 | `unknown_callee` 并入 `unknown_tool`，加载期名字解析单一失败点 | D-020 |
| 23 | 新增 10 卷：AST 节点、稳定 `sexpr`、UTF-8 字节列、错误阶段 | D-020 |

## 4. 非目标（MVP 不做）

| 不做 | 替代 | 依据 |
| --- | --- | --- |
| 类型系统、类型注解、类型推断 | 动态值 + 工具 schema 浅校验 | v0.1 §9、[03 §1](03-semantics.md) |
| 模块 / `import` | 单文件脚本；复用靠 `fn` | v0.1 §9 |
| `try/catch`、错误值、块级恢复 | 调用级 `\|?` 降级 | D-010 |
| 并行 / `par` | 全串行；`par` 保留为关键字，脚本出现即 `not_implemented` | D-019 |
| 链式方法调用、尾随 lambda | `\|>` 管道是唯一数据流语法 | D-001、v0.1 §9 |
| 通用对象字面量、正则字面量 | emit payload 的受限 JSON；字符串 + `grep` | D-006、v0.1 §9 |
| 递归 `fn` | 加载期调用图报环 | [03 §5](03-semantics.md) |
| `while` | `for` + 工具级 timeout/interval | D-009 |
| DSL 级审批语法 | 内核审批 | D-013 |
| 触发器 / 调度 | 内核配置 | v0.1 §9 |
| 截断控制语法（`limit N`） | 工具参数 | D-008 |
| 交互式终端 / REPL、子命令体系 | **暂缓，不是砍掉**：本规范只覆盖脚本层，但演进目标是 rillShell（完整 CLI，可被 shell 与内核调用）；不得因当前范围小做出排除终态的设计 | [D-021](../../decisions/D-021.md) |

## 5. 技术裁定与未决项

rev.1 **没有 `provisional` 条目**。原先的三处临时文本已收口：

| 原临时项 | 结论 | 记录 |
| --- | --- | --- |
| `par` 保留字 | 保留；脚本出现即加载错误 `not_implemented` | [D-019](../../decisions/D-019.md) |
| `# dsl-version:` | 接受 `1`；其他值 `E_VERSION` | [D-018](../../decisions/D-018.md) |
| 嵌套 `into` | 允许；内层 `$` 覆盖、退出恢复 | [D-017](../../decisions/D-017.md) |

值层的两条补充（`string + 标量`、`json_array.length`）同为技术裁定，见 [D-016](../../decisions/D-016.md)。这些都不是用户选择，正文内均挂相应 D 锚点。

仍未决的 P-013（Did-you-mean）、P-014（事件因果链）、P-017（并行语法）、P-020/P-021（主体与 taint）登记在 PENDING，正文不把未决项写成规则。

## 6. 与历史输入的关系

- `docs/design/dsl-spec-v0.1.md` 是 v0.1 原文，作为历史输入保留，不覆盖、不删除、不逐段改写。
- 本目录是 rev.1 的规范正文；两者冲突时以实现本目录为准，差异逐条记在 §3 与各卷的 `[D-xxx]` 标记。
- 旧文 §10 的 CT 映射不再作为规范内容：`ct-json`/`json_get` 在 ct-lang 中不存在（`grep` 计数 0），且 CT 禁止嵌套 `into`；实现必须自建值层与作用域。
- 本目录不声明“已验收”；所有 S-* 条目在 M1 之前保持 `unverified`。
