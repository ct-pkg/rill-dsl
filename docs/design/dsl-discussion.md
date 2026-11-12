# DSL 规范讨论稿（未定稿）

> 状态：**草案 / 讨论中 / 未定稿**。
> 本文件不引入新版本号，不替代 `docs/design/dsl-spec-v0.1.md`；v0.1 只是原文基线，**不是定稿**。
> 文中所有语法细节均为「待定项 / 提案 / 倾向」，在用户拍板前**不构成已生效规则**。

---

## 0. 基线与文件约定

- `docs/design/dsl-spec-v0.1.md`：用户提供的 v0.1 原文，作为讨论基线原样保留；不做“定稿”声明。
- 定稿前不创建 v0.2，也不创建任何带版本号的新规范文件。
- 定稿前的所有讨论只维护本文件：待定问题清单 + 各方意见 + 倾向与理由。
- 只有用户明确拍板后，才把结论写回带版本号的规范文件。

---

## 1. 来源标记

为避免把评审意见误写成用户决定，本文件用以下标记：

| 标记 | 含义 | 当前条目 |
| --- | --- | --- |
| **[用户决定]** | 用户本人已经拍板的语法决定 | 仅「空格替代括号」 |
| **[用户更正]** | 用户对上一轮草案的明确更正；不属于“语法决定”清单，但必须执行 | 截断不进 DSL 语法；重试不新增语句形态；来源标注规则 |
| **[评审意见]** | DeepSeek 两份评审提出的 P0/P1/P2 清单，供讨论，不等于已采纳 | 文法硬缺陷、while/break/continue、错误信息升级、边界一节、par 预留、事件因果链、白名单快照等 |
| **[我方技术裁定]** | 为让提案自洽而做的临时判断，可被用户或评审推翻 | 具体产生式、消歧规则、接口字段等 |

说明：用户明确说过“用户决定目前只有空格替代括号这一条”。因此截断与重试这两条虽然有“按本条规定执行”的效力，本文把它们单列为 **[用户更正]**，不混入 [评审意见]，也不冒充第二条语法决定。

---

## 2. 已经拍板或已经更正的事项

### 2.1 空格替代括号 [用户决定]

已定口径：

- 工具调用与用户函数调用统一为空格形态：`name arg1 arg2`。
- 括号 `()` 只作为“复杂表达式需要分组”的手段，以及 `fn` 定义时包参数列表；**不再作为调用的标志**。
- 不保留“工具用空格 / 函数用括号”两套并列写法。
- v0.1 中的 `analyze_file("a.c")` 这类写法在后续规范中改为 `analyze_file "a.c"`；复杂实参写 `write "issues.txt" (a + b)`。

仍待定的技术后果（见 §3、§4）：

- 工具与用户函数同名时如何解析；
- 零参数调用怎么写；
- `name (expr)` 与 `name expr` 是否完全等价；
- 嵌套调用如何区分（`f g "x"` vs `f (g "x")`）；
- postfix `()`（`f()()`、`a.b()`）是否彻底删除。

### 2.2 截断不进 DSL 语法 [用户更正]

已定口径：

- 不采用 `limit N lines` / `head N chars` 这类 DSL 语法后缀。
- 截断是**工具侧语义**：由各工具的 schema 自己声明 `limit` / `head` 之类的参数。
- DSL 层只规定通用结果元数据 `{ value, truncated, original_size }`。
- DSL 的字段访问必须能读到 `truncated` 标志。

理由（用户给出）：语法关键字会逼每个工具都实现一遍后缀式参数，并与工具自己的参数名冲突。

仍待定：

- 元数据挂在“调用结果记录”上，还是挂在绑定变量上；
- 普通值/JSON 对象本身有 `truncated` 字段时如何避免冲突；
- 管道左值如果是记录，传给右侧工具的是记录还是 `.value`；
- `original_size` 的单位（字节 / 字符 / 行）。

### 2.3 重试/降级不新增语句形态 [用户更正]

已定口径：

- 不采用 `retry n { fallback: ... }` 这种花括号形态。
- 降级统一走 `|?`（左侧的一次工具调用失败则尝试右侧）。
- 需要重试次数时，用工具参数表达，不新增语句形态。

仍待定：`|?` 的优先级、失败单元、右侧是否允许整条管道、与 `$` 隐式参数的先后顺序（见 §3 P0-11、§4 P1-2）。

---

## 3. 待定问题清单：P0 文法硬缺陷

以下均为 [评审意见]（DeepSeek 两份评审），状态都是**待定**；每条附我方倾向，但不作为规则。

### P0-1 负数词法吞掉减号

现象：v0.1 的 `NUMBER := -?[0-9]+(\.[0-9]+)?` 会贪婪匹配负号，导致：

- `a -1` 变成 `a(-1)`（工具调用），不是减法；
- `x-1` 变成 `x(-1)`；
- `1-2` 变成两个相邻的 primary，既不是减法也不是合法调用。

评审意见：`NUMBER` 不再吞负号，`-` 只作一元运算符，保证 `a - 1`、`x-1`、`1-2` 语义一致。

我方倾向：采纳。代价是 `read -1` 需要写成 `read (-1)`；这是可接受的、可被错误信息纠正的写法。

状态：待定。

### P0-2 换行没有进入文法

现象：v0.1 词法表没有 NEWLINE，§3.2 的 `statement*` 无法切分。若换行只是空白：

- `read "a"` 换行 `"b"` 会被当成两个实参；
- `let a = b` 换行 `let c = d` 会让 `b` 尝试把 `let` 吃成实参；
- `if x` 换行 `{` 是否合法无定义。

评审意见：引入 NEWLINE 作为语句终止符，并明确 `{}` 内外、`(`/`[` 内、管道续行的规则。

我方倾向：采纳，并给出以下细则（仍属提案）：

1. 语句以 NEWLINE、`}` 或 EOF 终止；连续空行折叠。
2. `(` / `[` 内部的 NEWLINE 忽略；`{}` 内部的 NEWLINE 仍是语句终止符。
3. NEWLINE 紧跟在 `|>` 或 `|?` 之后时忽略（管道续行）；连续多个 NEWLINE 一并忽略。
4. 工具调用的实参必须与工具名在同一逻辑行；跨行只能在分组内或管道续行后。
5. `}` 与 `else` 之间允许 NEWLINE。

状态：待定。

### P0-3 实参文法歧义

现象：v0.1 的 `arg := primary`，而 `primary := IDENT (" " arg)*`，`f a b c` 至少有四种分析树：`f(a,b,c)`、`f(a(b),c)`、`f(a,b(c))`、`f(a(b(c)))`。

评审意见：不要把 `arg := primary` 原样留着；给出确定的消歧规则（例如实参为 postfix 原子、应用左结合、需要嵌套时加括号），并说明为什么这样写仍然省 token。

我方倾向（提案，不是规则）：

- `arg := postfix_expr`，其中 `postfix_expr` 的原子是 `IDENT | STRING | NUMBER | BOOL | NULL | "$" | "(" expr ")"`；
- 空格应用不递归：`f g "x"` = `f(g, "x")`；
- 要嵌套写 `f (g "x")`；
- 实参里的字段访问直接写 `read path.field`（因为 `path.field` 是 postfix_expr）；
- 复杂表达式必须分组：`write "issues.txt" (a + b)`。

省 token 的理由：最常见形态 `read "path"`、`grep "foo" "file"` 不变；只有嵌套调用和复杂表达式多一对括号，而这本来就是 LLM 最容易写错、最需要明确边界的地方。

状态：待定。

### P0-4 emit 的 `{ "key": value }` 没有产生式

现象：§3.3 的 `expr` 不能以 `{` 开头，`emit_stmt := "emit" STRING expr` 无法解析 §8 示例 4。

评审意见：补对象字面量产生式，明确键、值类型、能否嵌套、如何与块界定 `{` 消歧。

我方倾向（提案）：

- 只在 `emit` 的 payload 位置允许 `json_object` / `json_array`；
- 键必须是字符串字面量；值允许字符串/数字/布尔/null/对象/数组/分组表达式；
- 允许嵌套；不允许尾随逗号；重复键视为加载错误；
- `if expr {` 的 `{` 是块，因为表达式文法不接受裸 `{`；payload 位置的 `{` 才是对象。

状态：待定。

### P0-5 §2「不引入 ()」与 postfix `()` 的矛盾

现象：§2 说“刻意不引入 ()”，§3.3 的 `postfix_expr` 又允许 `("(" arg_list? ")")*`，还能产生 `f()()`、`a.b()` 这类链式调用，与 §2 的“不引入链式方法调用”冲突。

评审意见：消除矛盾；postfix 调用要不要保留、保留到什么程度要写死。

用户已决定：调用统一空格形态，括号只作分组。由此推得：

- 用户函数调用不再用 `f(a, b)`；
- `()` 只保留“分组”和 `fn` 参数列表两种用途。

仍待定：是否彻底删除 postfix `()`（我方倾向：删除；MVP 没有一等函数/方法调用，保留它只会制造 `f()()` 这类歧义）。

状态：调用形态已由用户拍板；postfix 调用的删除属待定技术细节。

### P0-6 工具实参里的字段访问

现象：`arg := primary` 且 `primary` 没有 postfix，`read path.field` 会解析成 `(read path).field`，不是 `read(path.field)`。

评审意见：消歧规则要覆盖这一点。

我方倾向：随 P0-3 一并解决，`arg := postfix_expr` 后 `read path.field` 就是 `read(path.field)`。

状态：待定。

### P0-7 关键字与工具名/字段名冲突

现象：v0.1 没有声明保留字；`and`、`or`、`not`、`let`、`fn`、`emit`、`into`、`in`、`return`、`if`、`else`、`for`、`null`、`true`、`false` 作为工具名/字段名/函数名时行为未定义；`obj.in` 这类字段访问会撞词法。

评审意见：明确保留字与上下文关键字。

我方倾向：保留字表显式列出；`into` 继续作上下文关键字（只在一个表达式后跟 `{` 时特殊）；`limit` / `head` 不进入保留字（因为截断不进 DSL 语法）；`par` 是否保留见 P1-6。

状态：待定。

### P0-8 `# dsl-version` 没有文法位置

现象：§3.1 的 header 只有 allow/deny/emit；§13 又说脚本可声明 `# dsl-version: 2`。

评审意见：给出版法位置，或明确 MVP 不支持并说明。

我方倾向（提案）：MVP 不支持版本选择；`# dsl-version:` 出现在文件开头时按加载错误处理，并给出 hint “v0.2 只有一套文法，删除该行”。理由：只留语法位置、不实现行为，会让脚本作者误以为版本生效；静默忽略更糟。

状态：待定。

### P0-9 §8 示例 3 在新文法下解析错误

现象：`write "issues.txt" a + b` 按 `arg := primary` 会解析成 `(write "issues.txt" a) + b`，不是 `write("issues.txt", a + b)`。

评审意见：改示例或改文法，二选一，说明理由。

我方倾向：改示例为 `write "issues.txt" (a + b)`。理由：保留空格调用的紧凑性，复杂表达式用括号分组是用户已定的方向；改文法（让 `+` 进入实参）会重新引入优先级与实参边界歧义。

状态：待定。

### P0-10 错误格式不统一

现象：§11 用 `Error at line 5, col 10:`，§6.2 的 `DslResult` 拆分 `error_line` / `error_col`，CT 既有格式是 `path:line:col: error: msg`。

评审意见：选一个并说明。

我方倾向：与 CT 对齐为 `path:line:col: error: msg`，后接缩进 detail 行（allowed tools / hint / did you mean / 源码片段 + 插入符）。理由：实现语言是 CT，复用既有诊断习惯可以降低工具链分叉；LLM 对 `file:line:col` 也更容易定位。列号按 1 基字节列（与 CT 一致）。

状态：待定。

### P0-11 `|?` 的优先级与失败单元

现象：用户已定“`|?` 左侧一次工具调用失败则尝试右侧”，但没定义：`|?` 与 `|>` 的优先级、左结合的链、右侧是否可整条管道、与 `$` 隐式参数的顺序。

评审意见：`|?` 优先级低于 `|>`；失败单元是一次工具调用，不是整个左表达式。

我方倾向（提案）：

- `expr := fallback_expr`；`fallback_expr := pipe_expr ("|?" pipe_expr)*`，左结合；
- `pipe_expr` 内部才是 `|>`；
- 失败单元 = 左侧管道**最后执行的那次工具调用**；左侧更早的调用失败不触发右侧；
- 右侧独立求值，不接收左侧的管道值；
- 与 `$` 同时出现时的追加顺序仍待定（见 P1-2）。

状态：待定。

---

## 4. 待定问题清单：P1 语义与运行时

### P1-1 while / break / continue

[评审意见]：新增 `while` / `break` / `continue`，进 M4，不推到以后。

我方补充观察：v0.1 没有**赋值语句**（只有 `let`），所以只加 `while` 仍然无法改变循环条件；必须先决定是否允许 `IDENT = expr` 赋值，或引入 `let` 重新绑定同一名字。

倾向：允许对已声明的局部变量赋值（`x = expr`），仍不允许隐式创建变量；`break` / `continue` 只能在 `for` / `while` 内，否则加载错误。

状态：待定。

### P1-2 截断元数据的暴露方式

[用户更正]：截断走工具参数；DSL 只规定 `{ value, truncated, original_size }`；字段访问能读 `truncated`。

待定选项：

- **A. 调用结果始终是记录**：`let r = read ...` 绑记录，取原值写 `r.value`；所有现有示例都要改，且把记录塞进工具时要显式 `.value`。
- **B. 只有声明返回元数据的工具才返回记录**：其余工具仍返回值；字段访问 `r.truncated` 只在记录上合法。
- **C. 绑定值，另设内置元数据读取**（如 `meta r` / `r.truncated` 为保留伪字段），避免改现有示例。
- **D. 记录只在发生截断时产生**，未截断返回值；行为随数据变化，不推荐。

倾向：B 或 C。B 的规则局部、可静态校验；C 的 token 成本更低，但要解决“JSON 自带 truncated 字段”的冲突（可规定元数据优先，或要求用专用操作符）。暂不拍板。

### P1-3 错误信息升级

[评审意见]：加「Did you mean」相似工具名建议、附近源码片段与插入符标注、相似的正确写法示例。

倾向：全部采纳，但分两级落地：解析/加载错误先有 `path:line:col` + 片段 + 插入符；Did-you-mean 先覆盖工具名/事件名/字段名，再覆盖关键字拼写。相似度阈值与候选排序待定。

状态：待定。

### P1-4 Rill 在 agent 运行时中的位置

[评审意见]：新增一节，画清内核职责（主循环、上下文压缩、自修复回路、记忆/跨脚本状态）与规范范围（单次执行：工具调用+管道+条件+作用域+事件）的边界，明确 Rill 脚本是循环中的一个步骤。

倾向：采纳为规范的一节。规范只描述单次执行；主循环、审批、跨脚本状态、上下文压缩、模型调用都不进 DSL。需要用户确认边界措辞。

状态：待定。

### P1-5 `par` 预留

[评审意见]：明确“MVP 不做并行，`par` 关键字预留”，作为已知取舍写出来。

倾向：采纳。`par` 进入保留字，但文法没有产生式；出现时报“reserved for a future milestone”，而不是普通 unknown。是否保留字与 P0-7 一起定。

状态：待定。

### P1-6 事件因果链

[评审意见]：给出 `event_trace` 接口设计（trace_id 怎么生成、怎么随 emit 传递、订阅方怎么查询）。

倾向（提案）：

- 每次 `dsl_exec` 由内核生成 32 位十六进制 `trace_id`（128 bit CSPRNG）；脚本不能设置。
- 每次 `emit` 生成 `event_id`，信封携带 `trace_id`、`parent_event_id`；根脚本的 `parent_event_id` 为 NULL。
- 订阅方启动子脚本时把 `parent_event_id` 设为触发事件的 `event_id`，形成因果链。
- 事件总线保存有界环形缓冲；`event_bus_trace_query(trace_id, out, max)` 按时间序返回，被淘汰的 trace 返回 0 条并记日志。
- `DslResult` 增加 `trace_id`，调用方无需解析日志即可关联。

状态：待定。

### P1-7 白名单热更新竞态

[评审意见]：明确执行中的脚本使用加载时的策略快照，新策略只对下一次加载生效；写出理由。

倾向：采纳。加载时把 allow/deny/emit/registry generation/constraint version 绑定成 `PolicySnapshot`；`dsl_exec` 使用绑定快照；热更新原子替换，进行中的脚本不受影响；新加载使用新快照。理由：加载期 AST 校验与运行期参数校验必须看到同一份策略，否则会出现“加载时允许、运行时拒绝”或相反的竞态；也避免脚本执行中途权限被扩大。需要说明撤销策略对长脚本的延迟生效风险，并保留内核强杀开关。

状态：待定。

### P1-8 默认 allow 的安全性

[评审意见]：`# allow:` 缺省继承注册表级 = 默认对注册表内所有工具开放，建议默认拒绝。

我方观察：v0.1 §5.2 明确“缺省时继承注册表级白名单”。改成默认拒绝会改变已写脚本的行为，属于语义变更。

倾向：新增“无 header 时加载告警 + 审计日志”作为低风险过渡；是否默认拒绝留给用户拍板。不把评审意见直接写成规范规则。

状态：待定。

### P1-9 审批节点

[评审意见]：真实 agent 需要危险操作前的人工确认；三层白名单是静态权限，不是逐动作审批。

倾向：审批属于内核职责，不进 Rill 单次执行语法；DSL 只提供工具级 `requires_approval` 元数据与失败返回，具体暂停/恢复由内核实现。是否在 DSL 里增加 `approve` 语句，待用户决定。

状态：待定。

### P1-10 并行与扇出

[评审意见]：全串行无法承担多文件并行调研；`par` 只预留不够。

倾向：MVP 明确不做并行，承认代价；并行属于内核调度器职责，DSL 后续再议。是否允许 `par` 在 v0.3 进入语法，待定。

状态：待定。

### P1-11 上下文、状态、可观测性、工具契约、预算

[评审意见]：跨轮状态放哪、大输出如何截断/摘要回注、执行轨迹如何回给模型、schema 如何进入提示词、`ExecLimits` 超限如何返回部分结果。

倾向：

- 跨轮状态与记忆：内核职责，DSL 不保存；
- 大输出：工具侧截断 + 元数据（见 P1-2）；
- 执行轨迹：`emit` 事件 + `trace_id` + `DslResult`，由内核回注；
- 工具契约：`ToolDef.description` + `params_schema` 进入提示词，DSL 不重复描述；
- 预算：`ExecLimits` 明确计数口径；超限返回 `ok=0` + `error_kind=limit` + 最近一次成功语句的值作为部分结果。

状态：待定。

---

## 5. 与 CT 现状的事实核对

这一节只记录只读核对结果，用于判断“复用 CT”能复用多少。

| 说法 | CT 现状 | 证据 |
| --- | --- | --- |
| `|>` 管道 | 不存在。CT 表达式运算符表只有 C 运算符；全仓 grep 无 `|>` token | [language-spec.md](file:///Users/samxx/trae-ws/ct-lang/docs/language-spec.md#L2273-L2293) |
| `let` / `fn` / `emit` 关键字 | 不存在。词法只有 `T_EOF/T_ID/T_NUM/T_STR/T_PUNCT/T_PP`；CT 是 C 风格语句 | [Lexer.h.ct](file:///Users/samxx/trae-ws/ct-lang/selfhost/ct-ast/frontend/lex/Lexer.h.ct#L18-L24) |
| `for x in xs` → CT `foreach` | 不直接对应。`foreach` 只迭代一维数组，循环变量固定叫 `item` | [language-spec.md](file:///Users/samxx/trae-ws/ct-lang/docs/language-spec.md#L1985-L2024) |
| 复用 CT `into` / `$` | 只能借鉴形态。CT 的 `into` 是编译期脱糖、要求静态类型、禁止嵌套；块外 `$` 是 range 下标或 `unexpected token` | [language-spec.md §4.52](file:///Users/samxx/trae-ws/ct-lang/docs/language-spec.md#L2220-L2247)、[Expr.h.ct](file:///Users/samxx/trae-ws/ct-lang/selfhost/ct-ast/frontend/parse/Expr.h.ct#L2892-L2905)、[Expr.h.ct](file:///Users/samxx/trae-ws/ct-lang/selfhost/ct-ast/frontend/parse/Expr.h.ct#L4710-L4719) |
| `x.a.b` → `ct-json` 的 `json_get` | `ct-json` 不存在；仓库无 `json_get` / `json_parse`；`lib/std/` 只有 `Vec.h.ct`；`emit_json_str` 只是 `--emit-map` 输出格式化 | [Emitter.h.ct](file:///Users/samxx/trae-ws/ct-lang/selfhost/ct-ast/backend/emit/Emitter.h.ct#L4456) |
| 动态值 `null/bool/number/string/json_object/json_array` | CT 没有动态类型；Vec/Map 是静态类型容器 | `lib/std/Vec.h.ct` |
| 运行期错误传播 | CT 没有运行时错误类型；只有编译期 `path:line:col: error:` 诊断 | [Diag.h.ct](file:///Users/samxx/trae-ws/ct-lang/selfhost/ct-ast/tool/diag/Diag.h.ct#L78-L88) |
| ToolRegistry / EventBus / 白名单 / ExecLimits | 全仓 grep 零命中，均不存在 | 全仓 grep |

结论（待定，不写成规范规则）：CT 适合作为**实现语言**，不适合作为 DSL 的**运行时语义宿主**；v0.1 §10 的“复用”需要降级为“语法形态借鉴 + 自建运行时”。

---

## 6. 文法提案（明确标注：非规则）

以下仅用于讨论消歧效果，不构成 v0.2 内容。

### 6.1 词法提案

```
NEWLINE    换行（LF / CRLF）              语句终止符
标识符     [a-zA-Z_][a-zA-Z0-9_]*
数字       [0-9]+(\.[0-9]+)?               非负；负数由一元 - 表达
字符串     "..." 或 '...'                  转义 \n \t \" \' \\ \$
管道       |>
降级       |?
赋值       =
当前对象   $
比较       == != < > <= >=
算术       + - * / %
逻辑       and or not
字段       .
索引       [ ]
注释       # 到行尾
块界定     { }
括号       ( )                             仅分组与 fn 参数表
```

### 6.2 语法提案

```
program       := header? stmt_list EOF
stmt_list     := (NEWLINE | statement)*
statement     := let_stmt | assign_stmt | if_stmt | for_stmt | while_stmt
               | into_stmt | fn_def | return_stmt | emit_stmt
               | break_stmt | continue_stmt | expr_stmt

let_stmt      := "let" IDENT "=" expr
assign_stmt   := IDENT "=" expr
if_stmt       := "if" expr block ("else" block)?
for_stmt      := "for" IDENT "in" expr block
while_stmt    := "while" expr block
into_stmt     := expr "into" block
fn_def        := "fn" IDENT "(" param_list? ")" block
return_stmt   := "return" expr?
emit_stmt     := "emit" STRING emit_payload
break_stmt    := "break"
continue_stmt := "continue"
expr_stmt     := expr
block         := "{" stmt_list "}"

expr          := fallback_expr
fallback_expr := pipe_expr ("|?" pipe_expr)*
pipe_expr     := or_expr ("|>" call_expr)*
call_expr     := tool_call | IDENT
or_expr       := and_expr ("or" and_expr)*
and_expr      := cmp_expr ("and" cmp_expr)*
cmp_expr      := add_expr (("=="|"!="|"<"|">"|"<="|">=") add_expr)?
add_expr      := mul_expr (("+"|"-") mul_expr)*
mul_expr      := unary_expr (("*"|"/"|"%") unary_expr)*
unary_expr    := ("not"|"-") unary_expr | postfix_expr
postfix_expr  := atom suffix*
suffix        := "." IDENT | "[" expr "]"
atom          := IDENT | STRING | NUMBER | BOOL | NULL | "$"
               | "(" expr ")"
tool_call     := IDENT arg+

arg           := postfix_expr

emit_payload  := json_value
json_value    := STRING | NUMBER | BOOL | NULL
               | json_object | json_array | postfix_expr
json_object   := "{" (STRING ":" json_value ("," json_value)*)? "}"
json_array    := "[" (json_value ("," json_value)*)? "]"
```

### 6.3 消歧示例（按提案走一遍）

| 输入 | 提案下的解析 | 说明 |
| --- | --- | --- |
| `a - 1` / `x-1` / `1-2` | 全部是减法 | NUMBER 不吞负号 |
| `read -1` | 非法实参；写 `read (-1)` | 实参是 postfix 原子 |
| `f g "x"` | `f(g, "x")` | 空格应用不递归 |
| `f (g "x")` | `f(g("x"))` | 括号分组后是嵌套调用 |
| `read path.field` | `read(path.field)` | 实参是 postfix_expr |
| `write "issues.txt" (a + b)` | `write("issues.txt", a + b)` | 复杂表达式分组 |
| `content |> grep "malloc"` | pipe 左值追加到 `grep` 参数末尾 | 与 v0.1 一致 |
| `x |> f b |? g c` | `(x |> f b) |? (g c)`，`|?` 更低 | 失败单元是 `f b` |
| `if x {` | 块；`{` 不是表达式 | emit payload 的 `{` 仅在 emit 位置 |
| `emit "x" { "k": 1 }` | 对象 payload | 需要 §P0-4 的产生式 |

---

## 7. 里程碑草案（待拍板）

| 阶段 | 草案内容 | 对应讨论项 |
| --- | --- | --- |
| M1 | Lexer + Parser + AST 骨架 + header 解析 + 加载期静态检查（工具/事件/break/continue/$ 位置）+ 行列号错误 + golden 测试 | P0-1..P0-10；M1 验收见下 |
| M2 | 解释器核心：动态值、变量、工具注册、ExecLimits、错误传播、结果元数据 | P1-2、P1-11 |
| M3 | `|>` 管道 + 隐式 await + 隐式传参；`|?` 降级 | P0-11、P1-2 |
| M4 | `{}` 块、if/else、for、while、break/continue、赋值 | P1-1 |
| M5 | into + `$` + 隐式上下文参数 | v0.1 R3 |
| M6 | fn 定义/调用（空格形态） | 2.1 |
| M7 | emit + 对象字面量 + 事件总线 + 因果链 | P0-4、P1-6 |
| M8 | 三层白名单 + 策略快照 + 热更新 | P1-7、P1-8 |
| M9 | 错误信息升级（Did-you-mean、片段、插入符） | P1-3、P0-10 |

### M1 验收步骤（草案）

1. 用真实 LLM 生成 ≥20 条本规范风格的脚本，覆盖 `read`/`grep`/`write`/`fn`/`if`/`pipe`。
2. 默认按**路径 A（空格替代括号）**解析；记录首次解析成功率、`()` 误用次数、实参边界错误。
3. 同一模型、同一提示下，调用形态写错 **≥3 次**，则切**路径 B（括号调用）**作为退路；必须附原始输出与统计，不能凭印象切换。
4. 路径 B 只是验证失败时的退路，不作为与路径 A 并列的默认方案。
5. 若 §8 的示例在新文法下解析失败，先改文档，不带着失败示例进入实现。

---

## 8. 需要用户拍板的问题

| 编号 | 问题 | 我的建议 |
| --- | --- | --- |
| Q1 | 是否采纳 P0-1..P0-10 的文法修复作为下一版规范的基础？ | 采纳；否则 M1 无法稳定实现 |
| Q2 | `postfix ()` 是否彻底删除？ | 删除；MVP 无一等函数/方法调用 |
| Q3 | 是否允许 `IDENT = expr` 赋值语句（while 的前提）？ | 允许，仅限已声明局部变量 |
| Q4 | 截断元数据用哪种暴露方式（A/B/C/D，见 P1-2）？ | B，规则局部且可静态校验 |
| Q5 | `# allow:` 缺省是否改为默认拒绝？ | 先加告警/审计，默认拒绝再议 |
| Q6 | 审批节点放内核还是 DSL？ | 内核；DSL 只给 `requires_approval` 元数据 |
| Q7 | `par` 是否进入保留字？ | 是，但无产生式，报 reserved |
| Q8 | 错误格式是否统一为 CT 的 `path:line:col: error:`？ | 是 |
| Q9 | `# dsl-version:` 是否 MVP 直接报错？ | 是 |
| Q10 | 是否保留 v0.1 的嵌套 into 与 `$` 覆盖规则？ | 保留，但需写清作用域；不要声称复用 CT |

---

## 9. 决策记录（草案）

| # | 事项 | 处理 | 依据 | 状态 |
| --- | --- | --- | --- | --- |
| 1 | v0.1 原文落库 | 逐字保存为 `docs/design/dsl-spec-v0.1.md` | 用户指示 | 已完成，未定稿 |
| 2 | 不出 v0.2 | 不创建任何带版本号的新规范文件 | 用户更正 | 已执行 |
| 3 | 空格替代括号 | 统一调用形态；括号只分组与 fn 参数表 | 用户决定 | 已拍板（细节待定） |
| 4 | 截断不进 DSL 语法 | 工具参数负责；DSL 只规定结果元数据 | 用户更正 | 已拍板（暴露方式待定） |
| 5 | 不采用 `retry n { fallback: }` | 统一走 `|?`；重试次数由工具参数表达 | 用户更正 | 已拍板（语义待定） |
| 6 | 来源标注 | 区分用户决定/用户更正/评审意见/我方技术裁定 | 用户更正 | 已执行 |
| 7 | 负数词法、NEWLINE、实参歧义、emit 对象字面量、`()` 矛盾、`# dsl-version`、示例 3、错误格式 | 列入 P0 待定；附倾向 | DeepSeek 评审意见 | 待定 |
| 8 | while/break/continue、`|?` 优先级、错误信息升级、边界一节、par 预留、事件因果链、白名单快照 | 列入 P1 待定；附倾向 | DeepSeek 评审意见 | 待定 |
| 9 | 默认拒绝、审批节点、并行能力、状态/可观测性/工具契约/预算 | 列入 P1 待定 | DeepSeek 评审意见 | 待定 |
| 10 | 零参调用、工具/函数同名、嵌套实参、postfix 删除 | 列入待定；倾向写提案 | 我方技术裁定 | 待定 |
| 11 | CT 复用边界 | 只复用实现语言，不复用运行时语义 | 源码核对事实 | 待定 |

---

## 10. 下一步

1. 用户逐条回应 §8 的 Q1–Q10（或直接给出不同裁决）。
2. 拍板后，才把结论写回带版本号的规范文件；在此之前只改本讨论稿。
3. 任何一条与评审意见不同的裁决，都要在决策记录里注明“与评审不同”及理由，不藏争议。
