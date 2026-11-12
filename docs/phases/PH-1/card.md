# PH-1 立项卡：解析器与加载期校验（完整文法切片）

> 状态：`draft`（待评审冻结）。本卡只定义 Phase 1 的范围、交付与判据，不含实现代码。
> 规范版本：`1.7.0`（开卡时 `AGENTS.md` 生成块头快照）。
> 依据：用户 2026-11-12 指示；[09 里程碑](../../spec/dsl/09-milestones.md) §2 M1/M2；[10 AST 与位置契约](../../spec/dsl/10-ast-position.md)；[S-001..S-024](../../spec/README.md)；[D-001..D-020](../../decisions/README.md)。AST/位置以 10 卷与 D-020 为准，本卡不重复定义。本卡不修改 `docs/spec/dsl/` 正文、不修改决策记录、不移动 DSL 规范版本 `v0.1 rev.1`。

## 0. 开卡必填字段

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-1`，目录 `docs/phases/PH-1/` |
| 目标 | 交付一个可运行的解析器 CLI：对完整 Rill DSL 源文本产出稳定 AST，并在加载期报出全部静态错误（含行列号）。 |
| 范围 | 词法、header、全部语句与表达式、emit payload、AST、加载期名字/头部/arity 校验、错误格式；不含任何执行语义。 |
| 交付物清单 | 见 §3；每项一个路径。 |
| 任务清单 | 见 §4；每项一个交付物、一条 `verify`、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §9；每条带命令或 golden 锚点。 |
| 依赖 | Phase 0 的 `tools/check.sh` 基线（g0/g1/g4/g6/g9 已绿）与 `tools/check-all.sh` 全量入口；Phase 1 需启用 g3/g5/g7/g8；CT 工具链；T-001..T-006 的静态元数据；`src/` 与构建入口由 P1-T01 建立。 |
| 规范版本 | `1.7.0`（生成块头 `version` 快照；`v0.1 rev.1` 是 DSL 规范版本，不改）。 |
| version-minor | `1`（`PH-1` 收口目标 `0.1.0`；产品版本落点由 Phase 0/G0 声明，本卡不执行 bump）。 |
| 已知风险 | 换行与空格调用交互、emit payload 与块界定消歧、错误位置计算；见 §8。 |

## 1. 目标与范围

### 1.1 目标

一句话：**完整文法先于解释器**。Phase 1 结束时，任意符合 [02 文法](../../spec/dsl/02-grammar.md) 的脚本都能被解析为稳定 AST；不符合的脚本都在加载期得到 `path:line:col: error:` 诊断，而不是留到运行期。

### 1.2 范围（做什么）

| 域 | 内容 | 规范锚点 |
| --- | --- | --- |
| 词法 | UTF-8、无 BOM、CRLF 归一、虚拟 EOF NEWLINE；`IDENT`/`STRING`/`NUMBER`/`BOOL`/`NULL`/`KEYWORD`/`PUNCT`/`NEWLINE`/`EOF`；最长匹配；无符号数字；字符串转义与禁止裸换行；注释不吃 LF；N1–N8 抑制 | [01](../../spec/dsl/01-lexical.md) §1–§7 |
| Header | 只认 `# allow:` / `# deny:` / `# emit:` / `# dsl-version:` 四种前缀，其余 `#` 行按注释（含 `# approval:`）；整行解析；`TERM`；重复键；默认拒绝（无 allow/空列表拒绝）；`*` 与 deny 列表只记录集合，不计算有效集；版本只接受 `1` | [01](../../spec/dsl/01-lexical.md) §6、[02](../../spec/dsl/02-grammar.md) §1、[06](../../spec/dsl/06-security.md) §2、[10](../../spec/dsl/10-ast-position.md) §6、[D-011](../../decisions/D-011.md)、[D-018](../../decisions/D-018.md) |
| 文法 | 全部语句：`let`/`let mut`/赋值/`if`/`for`/`into`/`fn`/`return`/`emit`/`break`/`continue`/表达式语句；完整表达式优先级；空格实参不递归；无 postfix `()`；字段与索引；`\|>` 与 `\|?`；emit 受限 JSON；`approve` 不是文法语句（写了 → `syntax`） | [02](../../spec/dsl/02-grammar.md) §2–§4、[06](../../spec/dsl/06-security.md) §6、[S-016](../../spec/S-016-approval.md)、[D-001..D-009](../../decisions/README.md) |
| AST | 节点集合、字段顺序、`sexpr`/`sexpr-loc`、分组/注释/版本头擦除、header 保序与 `*` 表示全部以 10 卷为准；`--dump-ast` 与 `--dump-tokens` 两种 golden | [10](../../spec/dsl/10-ast-position.md) §2–§6、[D-020](../../decisions/D-020.md) |
| 加载期校验 | `unknown_tool`（名字解析失败统一用此 kind，Hint 同时提示工具名与函数名）、`tool_not_allowed`、`event_not_declared`、`undefined_name`、`bare_fn_ref`、`shadow_tool`、`dup_decl`、`assign_undefined`、`immutable_assign`、`loop_control`、`return_outside_fn`、`recursion`、`arity`（含管道与 `$` 注入）、`not_implemented`、`pipe_rhs`、`fallback_lhs`、`dollar_outside`、`reserved_name`、`dup_header`、`no_allow_header`、`deny_without_allow`、`version`、`dup_key` | [03](../../spec/dsl/03-semantics.md) §2–§7、[04](../../spec/dsl/04-pipeline-errors.md)、[06](../../spec/dsl/06-security.md)、[07](../../spec/dsl/07-runtime.md) §3.1、[T-001..T-006](../../spec/tools/README.md) |
| 错误 | 统一格式、1 基行列、`col`/span 按 10 §4、只报第一个错误、强制 `Hint:` | [07](../../spec/dsl/07-runtime.md) §4、[10](../../spec/dsl/10-ast-position.md) §4–§5、[D-015](../../decisions/D-015.md)、[S-020](../../spec/S-020-error-format.md) |
| 样例 | 五个 08 示例解析成功并产出 AST golden；解析器 CLI 是 Phase 1 唯一可运行形态 | [08](../../spec/dsl/08-examples.md)、[09](../../spec/dsl/09-milestones.md) §1 原则 3 |

### 1.3 非范围（不做什么）

| 不做 | 为什么不属于 Phase 1 |
| --- | --- |
| 值模型、算术/比较/真值、`let`/赋值/`if`/`for` 的执行 | 没有解释器；09 §1 原则 1 要求“文法未冻结前不写解释器”。 |
| 工具 handler、真实工具调用、`ToolRegistry` 运行时 | Phase 1 只读工具的**静态元数据**（名字、arity、`accepts_context`、是否变长），不调用 handler。 |
| 事件发布、EventBus、订阅方、`external_egress` | `emit` 只做到“解析 + 事件已声明”检查；05 §2 的 fire-and-forget 是运行期。 |
| 审批、`approval_required`/`approval_denied` | D-013 规定审批 100% 在内核；DSL 没有 `approve` 语句（写了 → `syntax`），`# approval:` 按注释处理；Phase 1 只断言这两点。 |
| 策略快照、`policy_generation`、热更新、强杀 | D-012 是执行期语义；Phase 1 只解析 header 的 allow/deny/emit。 |
| `ExecLimits` 计数、`max_steps`/`max_tool_calls`/`timeout_ms` | 07 §2 是运行期；Phase 1 无执行循环。 |
| 截断元数据、粘性、`original_size` | 05 §1 是工具边界与运行期归并；Phase 1 只解析 `(read "x").truncated` 的形状。 |
| R4 失败行为表、`degraded`、`ok`/`error_kind` 运行期回显 | 04 §3 是运行期控制信号；Phase 1 只做 `pipe_rhs`/`fallback_lhs` 静态检查。 |
| 路径/argv/域名参数约束 | 06 §1 第三层在每次调用前执行；Phase 1 只做静态 arity，不做值校验。 |
| 真实 LLM 验证、token 统计 | 09 §3 的 M10；Phase 1 只用 golden 证明解析与加载。 |
| `while`、并行 `par` 语义 | D-009 否决 `while`；D-019 只保留 `par` 关键字并报 `not_implemented`。 |

## 2. 交付契约（token / AST / CLI）

### 2.1 token dump

`rill parse --dump-tokens` 每行一个 token：`KIND<TAB>lexeme<TAB>line:col`。`KIND` ∈ `IDENT`/`STRING`/`NUMBER`/`BOOL`/`NULL`/`KEYWORD`/`PUNCT`/`NEWLINE`/`EOF`；`STRING` 的 lexeme 是 JSON 转义后的解码值；`PUNCT` 保留原文；`NEWLINE` 的 lexeme 为 `\n`；`EOF` 的 lexeme 为空。dump 前必须已执行 N1–N8 抑制。

### 2.2 AST dump

AST 的节点集合、字段顺序、`sexpr`/`sexpr-loc`、分组/注释/版本头擦除、header 保序与 `*` 表示，全部以 [10 卷](../../spec/dsl/10-ast-position.md) 与 [D-020](../../decisions/D-020.md) 为准；本卡不重复定义。golden 默认比对 10 §3 的 `sexpr`，位置用例比对 10 §4 的 `sexpr-loc`；旧卡草案中与 10 卷不一致的写法一律按 10 卷改。

### 2.3 CLI

```
rill parse --dump-tokens        [--registry R] FILE
rill parse --dump-ast [--loc]   [--registry R] FILE
rill parse --check --json       [--registry R] FILE
```

`--dump-ast` 默认输出 10 §3 的 `sexpr`；加 `--loc` 输出 10 §4 的 `sexpr-loc`。退出码：`0` 可加载；`1` 加载错误；`2` 用法/IO/内部错误。`--check --json` 成功输出 `{"ok":1}`；失败输出 `{"ok":0,"error_kind":"…","line":N,"col":M,"message":"…","hint":"…","path":"…"}`。默认 registry 为 `tests/phase1/registry.json`。

### 2.4 registry fixture

Phase 1 只消费静态元数据：`read` arity=1、`grep` arity=2、`write` arity=2、`json_parse` arity=1、`get` arity=2 且 `accepts_context=true`、`json_build` 变长（`params_schema=null`，偶数校验）。字段：`{"tools":[{"name":"read","arity":1,"accepts_context":false,"variadic":false}, …]}`。

## 3. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `src/lexer.ct` | token 化、字符串/数字、注释、N1–N8、token 位置 |
| `src/ast.ct` | AST 类型与 10 卷 `sexpr`/`sexpr-loc` 序列化 |
| `src/parser.ct` | header、语句、表达式、emit payload |
| `src/loader.ct` | 名字表、作用域、可变性、调用图、arity/注入、header 语义 |
| `src/diagnostics.ct` | `error_kind` 目录、消息、Hint、位置规则 |
| `src/main.ct` | `rill parse` CLI 与 `--check --json` |
| `tests/phase1/registry.json` | §2.4 静态 registry |
| `tests/phase1/cases/*.rill` + `.tok`/`.sexpr`/`.sexpr-loc`/`.err.json` | 每条判据的输入与 golden |
| `tools/check-phase1.sh` | 单条与全量 case 执行器；`--coverage` 校验 S 覆盖 |
| `examples/phase1/*.rill` + `*.sexpr` | 08 五个示例与 AST golden |
| `docs/phases/PH-1/card.md` | 本卡 |
| `docs/planning/roadmap.md` | Phase 1–5 粗排期 |

## 4. 任务清单

每项：一个交付物、一条 `verify`、一次实现提交（前有同 task-id 的 `test` 提交）、可单独回滚。实现提交为 `feat(phase1): <ID> …`，回滚为 `git revert <sha>`；每行不依赖其他任务的未提交改动。

| ID | 交付物 | verify | effort | 红证 |
| --- | --- | --- | --- | --- |
| P1-T01 | 工程骨架、CLI、registry fixture、`check-phase1.sh` | `tools/check-phase1.sh --self` | S | 有 |
| P1-T02 | lexer：token/关键字/数字/字符串/注释 | `tools/check-phase1.sh --case LX-01,LX-02,LX-03,LX-04` | M | 有 |
| P1-T03 | NEWLINE N1–N8 与 token 位置 | `tools/check-phase1.sh --case LX-05,LX-06,LX-07,LX-08,LX-09,LX-10` | M | 有 |
| P1-T04 | AST 类型与 10 卷 `sexpr` 序列化 | `tools/check-phase1.sh --case GR-01` | M | 有 |
| P1-T05 | header 解析与 header 错误 | `tools/check-phase1.sh --group HD` | S | 有 |
| P1-T06 | 语句与块解析 | `tools/check-phase1.sh --case GR-10,GR-11,GR-12` | M | 有 |
| P1-T07 | 表达式解析（优先级/调用/后缀/管道/降级） | `tools/check-phase1.sh --case GR-01,GR-02,GR-03,GR-04,GR-05,GR-06,GR-07,GR-08,GR-09,GR-15,GR-16,GR-17` | M | 有 |
| P1-T08 | emit payload 解析 | `tools/check-phase1.sh --group EM` | S | 有 |
| P1-T09 | 名字解析、作用域、可变性、循环/返回/递归 | `tools/check-phase1.sh --case LD-04,LD-05,LD-06,LD-07,LD-08,LD-09,LD-10,LD-11,LD-17,LD-18` | M | 有 |
| P1-T10 | 工具/allow/event、arity/注入、pipe/fallback | `tools/check-phase1.sh --case LD-01,LD-02,LD-03,LD-12,LD-13,LD-14,LD-15,LD-16,LD-19` | M | 有 |
| P1-T11 | 诊断格式与 10 卷位置/阶段接线 | `tools/check-phase1.sh --group ER` | S | 有 |
| P1-T12 | 五个示例、golden、全量门禁接入 | `tools/check-phase1.sh --all` | M | 有 |

## 5. 验收判据

### 5.0 判据执行方式与位置规则

- 每个 case 的输入是 `tests/phase1/cases/<ID>-<n>.rill`；一个 case 可含多个 fixture（表中用“；”分隔的每个片段各是一个 fixture），每个 fixture 配同名 `.tok`/`.sexpr`/`.sexpr-loc`（仅位置用例）/`.err.json`。
- 单条命令：`tools/check-phase1.sh --case <ID>`（跑该 case 的全部 fixture）；Phase 1 全量：`tools/check-phase1.sh --all`；仓库全量：`tools/check-all.sh`（g3/g5/g7/g8 在收口时启用）。
- 负例同时断言：`ok=0`、精确 `error_kind`/`line`/`col`、`message` 包含表中“文案要点”子串、`hint` 非空。
- 位置与 span 口径完全以 [10 §4/§5](../../spec/dsl/10-ast-position.md) 为准；词法/解析为 `syntax`，加载用 07 §3.1 的 kind；未闭合定界符指向最内层未匹配的开定界符（10 §5）。各负例的精确 `line`/`col` 由 `.err.json` 固定；header 语义错误、`dup_key`、`recursion` 的位置按 10 §5/§6 与 07 §3.1。

### 5.1 01 词法

| ID | S | 输入 | 期望 | 负例：error_kind@位置 + 文案要点 |
| --- | --- | --- | --- | --- |
| LX-01 | S-001 | `let s = "a\n" # c` + 换行 + `let t = 1` | `.tok` 含两条 `let`、注释不吞 `NEWLINE` | — |
| LX-02 | S-003 | 关键字全集、`true`/`false`/`null`、`par` | KEYWORD/BOOL/NULL 分类正确；`par` 为 KEYWORD | — |
| LX-03 | S-003 | `0`、`42`、`3.14`、`1.`、`.5`、`1e9`、`0x10`、`1_000`、`12abc`、`1.2.3` | 前三个合法；`1.2.3` 词法为 `1.2 . 3` | `syntax`；`12abc`/`1.` 指向数字起点；`1.2.3` 指向第二个 `.` |
| LX-04 | S-004 | `let x = 1 # c` + 换行 + `let y = 2`；`read "a"` + 换行 + `"b"`；`# allow: read # x` | 前两个 fixture 各为两条语句；第三个 header 行内 `#` 报错 | `syntax`；header 行内注释指向第二个 `#` |
| LX-05 | S-004 | `let c = (1` + 换行 + `+ 2)`；`let x = arr[` + 换行 + `0]` | N2 删除括号内 NEWLINE；两条语句各自完整 | — |
| LX-06 | S-004 | `let d = a` + 换行 + `    \|> f b`；`a \|>` + 换行 + `f b` | N4/N5 删除 NEWLINE；一条语句 | — |
| LX-07 | S-004 | `if a == 1` + 换行 + `{ … }` + 换行 + `else` + 换行 + `{ … }` | N6/N7 生效；一个 `if` 节点 | — |
| LX-08 | S-004/S-006 | `emit "e"` + 换行 + `{ "k": 1 }`；`emit "e"` + 换行 + `{}` | N8 生效；payload 分别是 `(pobj …)` 与 `(pobj)` | — |
| LX-09 | S-004 | BOM 开头；单独 `\r`；未闭合 `{`/`(`/`[`/字符串 | 全部拒绝 | `syntax`；BOM `1:1`，`\r` 指向 `\r`，未闭合指向最内层未匹配的开定界符/引号（10 §5） |
| LX-10 | S-020 | `let s = "中文" x`；CRLF 脚本 | 合法前缀后报错；CRLF 归一为 LF | `syntax`；列口径按 10 §4，指向 `x` |

### 5.2 02 header

| ID | S | 输入 | 期望 | 负例：error_kind@位置 + 文案要点 |
| --- | --- | --- | --- | --- |
| HD-01 | S-013/S-015 | `# allow: read, grep, nosuch`、`# deny: write`、`# emit: e`、`# dsl-version: 1` | header `entry*` 保序、不去重；version 擦除不进 AST；allow 中未注册 `nosuch` 不报错（A-3） | — |
| HD-02 | S-013 | 无 `# allow:`；`# allow:` 空列表；首条语句前有注释/空行 | 拒绝加载；空列表按 06 §2 与无 header 同义，AST 为 `(entry allow)`（10 §6） | `no_allow_header`；`Available:` 与 `Hint:` 必含；位置为第一条语句首 token |
| HD-03 | S-013 | 只有 `# deny: exec` | 拒绝，不得静默变空集 | `deny_without_allow`@header 行首；文案含“add '# allow:'” |
| HD-04 | S-013 | 任意 header 键重复，如两个 `# allow:` | 拒绝 | `dup_header`@第二次键行首；文案含键名 |
| HD-05 | S-021 | `# dsl-version: 2`、`1.0`、`v1`、重复版本头；`1` 与省略对比 | `1` 与省略 AST 相等（版本头擦除，10 §6） | `version`@数字 token（`2`/`1.0`）；`syntax`@值 token（`v1`）；`dup_header`（重复） |
| HD-06 | S-014 | `# allow: *` + `# deny: exec` | AST 为 `(entry allow *)` `(entry deny exec)`；审计记录不在 Phase 1 | — |
| HD-07 | S-013 | `let a = 1` + 换行 + `# allow: read` + 换行 + `read "x"` | header 模式已结束；后置行按注释处理 | `no_allow_header`；位置为 `let` token |

### 5.3 02 文法

| ID | S | 输入 | 期望 | 负例：error_kind@位置 + 文案要点 |
| --- | --- | --- | --- | --- |
| GR-01 | S-001 | `read "src/main.c"` | `(call read (str "src/main.c"))` | — |
| GR-02 | S-002 | `f g "x"` | `(call f (ident g) (str "x"))`，不得是 `f(g("x"))` | — |
| GR-03 | S-002 | `f (g "x")` | `(call f (call g (str "x")))` | — |
| GR-04 | S-005 | `f(a)(b)`；`f()`；`a.b()` | 前者 `(call f (ident a) (ident b))` | `syntax`@`(`；文案含“argument or grouped expression”/“method call” |
| GR-05 | S-002/S-005 | `read path.field`；`(read "x").y`；`arr[0]` | 前者实参为 `(field …)`；中者为 `(field (call read …) y)`；后者 `(index …)` | — |
| GR-06 | S-003 | `f 1 - 2`；`f -1`；`read -1` | 前者 `(binary - (call f (num 1)) (num 2))`；后两者先解析为减法 | `undefined_name`@工具名（A-6）；文案含“tool name cannot be used as a value”；Hint `read (-1)` |
| GR-07 | S-010 | `x = 1`；`x == 1`；`let mut y = 0` + 换行 + `y = y + 1`；`let mut x = 0` + 换行 + `if true { x = 1 }` | 赋值与比较区分；`let mut` 序列化为 `(let … true …)`（10 §3.7）；同函数外层块的可变绑定可赋值 | — |
| GR-08 | S-007/S-008/S-012 | `a \|> f b \|? g c`；`read "p" \|? read "f" \|> json_parse`；`a \|? b \|? c`；`read "p" \|? "fallback"` | `\|?` 高于 `\|>`；左结合；`\|?` 右侧可为任意值；AST 为 pipe/fallback 组合 | —（运行期求值延后） |
| GR-09 | S-009 | `(read "big").truncated`；`read "big".truncated` | 前者 field 作用于 call，后者是 call 的实参为 field | —（meta 读取延后） |
| GR-10 | S-011 | `if`/`else`；`for x in items { continue; break }`；`deps into { … }` | 全部节点形状正确；`break`/`continue` 在 for 内合法 | — |
| GR-11 | S-023 | 08 示例 5 的嵌套 `into` | 内层 `into` 节点嵌在外层块内；`$` 为 `(dollar)` | — |
| GR-12 | S-005 | `fn f(p) { return p }`；`return` 无表达式 | `(fn f p …)`；`(return)` | — |
| GR-13 | S-016 | `approve "x"`；`# approval: x` | `approve` 不是文法语句 → 拒绝；`# approval:` 按注释，不产生 `entry`、不报错（10 §6，D-013） | `syntax`@`approve`；文案含“unexpected” |
| GR-14 | S-018 | `exec "/bin/ls"` | 解析为 call；registry 无 `exec` | `unknown_tool`@`exec`；Hint 含工具名与函数名 |
| GR-15 | S-001/S-002 | `a < b < c`；`f(a, b)`；`let a = 1 let b = 2`；`if x = 1` | 全部拒绝 | `syntax`；分别指向第二个 `<`、`,`、第二个 `let`、`=` |
| GR-16 | S-024 | `let s = "count: " + n`；`let len = arr.length`；`let bad = n + true` | 三句都解析成功；`.length` 为普通 field | —（类型错误延后） |
| GR-17 | S-017 | `read "/workspace/../../etc/passwd"` | 解析为 `(call read (str "…"))`；Phase 1 不校验路径值 | —（约束在运行期） |

### 5.4 02 emit payload

| ID | S | 输入 | 期望 | 负例：error_kind@位置 + 文案要点 |
| --- | --- | --- | --- | --- |
| EM-01 | S-006 | `emit "e" {}` | `(emit "e" (pobj))` | — |
| EM-02 | S-006 | 多行 `emit "e" { "path": "src/a.c", "count": n + 1 }` | `(pobj …)`；值位为 `(binary + …)` | — |
| EM-03 | S-006 | `emit "e" { "items": [1, 2, 3] }` | `(pobj …)` 含 `(parr …)` | — |
| EM-04 | S-006 | `emit "e" { "a": 1, }`；`emit "e" { a: 1 }`；`emit "e" { "a": 1 }.x` | 全部拒绝 | `syntax`@`}`/键 token/`.`；文案含“trailing comma”/“string key”/“payload suffix” |
| EM-05 | S-006/S-019 | `emit "e" { "a": 1, "a": 2 }`；未声明事件 | 拒绝 | `dup_key`@第二个 `"a"`；`event_not_declared`@事件字符串 |

### 5.5 03/06/07 加载期校验

| ID | S | 输入 | 期望 | 负例：error_kind@位置 + 文案要点 |
| --- | --- | --- | --- | --- |
| LD-01 | S-001 | `nosuch "x"`（即使 `nosuch` 不在 allow） | 拒绝；未注册优先于未授权 | `unknown_tool`@callee；文案含工具名 |
| LD-02 | S-013 | `# allow: read` + `write "x" "y"` | 拒绝 | `tool_not_allowed`@`write`；含 `Allowed tools:` 与 Hint |
| LD-03 | S-006 | `# allow: read` + `emit "e" {}`（无 `# emit: e`） | 拒绝 | `event_not_declared`@`"e"`；含 `Declared events:` |
| LD-04 | S-005 | `let x = y`；`fn f(p) { return p }` + `let x = f` | 拒绝 | `undefined_name`@`y`；`bare_fn_ref`@`f` |
| LD-05 | S-005 | `let read = 1`；`fn grep(x) {}`；`fn f(read) {}`；`for read in xs {}` | 拒绝 | `shadow_tool`@声明名/参数名；Hint 改名 |
| LD-06 | S-010 | 同作用域 `let z` 两次；同名 `fn` 两次；内层块 `let` 遮蔽外层同名 `let` | 前两者拒绝；内层遮蔽合法 | `dup_decl`@第二个声明名 |
| LD-07 | S-010 | `n = 1` | 拒绝 | `assign_undefined`@`n`；Hint 补 `let` |
| LD-08 | S-010/S-023 | `let x = 1` + `x = 2`；参数赋值；for 变量赋值；`$ = 1`；闭包外层赋值 | 全部拒绝 | `immutable_assign`@目标；Hint 分别指向 `let mut`/参数/循环变量/`$`/闭包 |
| LD-09 | S-011 | 循环外 `break`/`continue`；for 内 fn 里的 `break` | 拒绝 | `loop_control`@关键字；文案含“inside a for block” |
| LD-10 | S-010 | 顶层 `return 1` | 拒绝 | `return_outside_fn`@`return` |
| LD-11 | S-010 | `fn a() { return b } fn b() { return a }` | 拒绝 | `recursion`@回边 callee；文案含调用环 |
| LD-12 | S-017 | 裸 `read`；`x \|> read "p"`；into 内 `grep "m"`；into 外 `get "k"`；`fn f(a, b) { return a }` + `f 1` | 全部拒绝 | `arity`@callee；文案含实际数/期望数 |
| LD-13 | S-023 | into 内 `get "k"`；`get "k" $`；into 内裸 `read`；`$ \|> write "out"` | 第一、二、四句合法；第三句 `arity`（0≠1） | `arity`@裸 `read`；文案含实际数/期望数 |
| LD-14 | S-023 | `json_build "a"`；`json_build "a" 1`；`json_build` | 奇数拒绝；偶数/零个合法 | `arity`@`json_build`；文案含“even” |
| LD-15 | S-007 | `a \|> (a + b)`；`a \|> f`（f 有参数） | 拒绝 | `pipe_rhs`@RHS 首 token；Hint 用 call |
| LD-16 | S-007 | `(a \|> b) \|? c`；`a + b \|? c`；`a \|? b`（a 为变量） | 拒绝 | `fallback_lhs`@LHS 首 token；Hint 用 `fn` 包裹 |
| LD-17 | S-023 | into 外 `$`；into 外 `$ = 1` | 拒绝 | `dollar_outside`@`$`；Hint 用 `into { … }` |
| LD-18 | S-022 | `par { … }`；`let par = 1`；裸 `par`；`x.par` | 全部拒绝 | `not_implemented`@`par`；Hint 指向内核调度 |
| LD-19 | S-022 | registry 含 `par` 或关键字名 | 注册失败 | `reserved_name`@registry 路径；文案含保留名 |

注：LD-13 的 `into` 内裸 `read` 是零参调用（0≠1），用于证明“不在 `accepts_context` 的工具不会被注入”；`into` 内 `read "p"` 是 1=1，合法，写入同组正例。

### 5.6 07 错误格式与位置

| ID | S | 输入 | 期望 | 负例：error_kind@位置 + 文案要点 |
| --- | --- | --- | --- | --- |
| ER-01 | S-020 | 任一负例 | stdout/stderr 与 `.err.json` 字段齐全；格式 `path:line:col: error: message` + 详情行 + `Hint:` | 缺 `Hint:` 或一次报多条即失败 |
| ER-02 | S-020 | `let s = "中文" x`；CRLF | `col` 按 UTF-8 字节；CRLF 不改变行号 | `syntax`；位置由 `.err.json` 固定 |
| ER-03 | S-020 | 未闭合 `{`；文件在表达式中间结束 | 指向最内层未匹配的开定界符；EOF 指向最后一字节之后 | `syntax`；位置由 `.err.json` 固定 |

### 5.7 08 示例

| ID | S | 输入 | 期望 | 负例 |
| --- | --- | --- | --- | --- |
| EX-01 | —（端到端样例，不计入逐条 S 覆盖） | 08 的五个示例逐一 | 五个 `.sexpr` golden 全部相等；每个示例的 header/语句/表达式形状按 10 卷 | 任一解析失败即失败 |

## 6. 样例计划

- `examples/phase1/` 放 08 的五个示例，文件名 `ex1-read-grep-write.rill` … `ex5-nested-into.rill`，逐字取自 [08](../../spec/dsl/08-examples.md)，不改写。
- 每个示例配 `*.sexpr` golden（`--dump-ast` 默认形态）；不配 token golden（token 细节由 `tests/phase1/cases/` 覆盖）。
- `tests/phase1/cases/` 按 `<ID>.rill` + `<ID>.tok`/`<ID>.sexpr`/`<ID>.sexpr-loc`/`<ID>.err.json` 命名；`.sexpr-loc` 仅位置用例；golden 入库，不在运行时生成。
- 真实门禁：`tools/check-phase1.sh --all` 依次跑（1）构建、（2）token golden、（3）AST golden、（4）负例断言、（5）五个示例。任一 diff 非空或任一 `--case` 非 0 即失败。收口时把 `tools/check.sh` 的 g3/g5/g7/g8 从 DISABLED 转为启用，并由 `tools/check-all.sh` 跑全量。
- `tools/check-phase1.sh --coverage` 从 `.err.json`/`.sexpr` 的 case 元数据汇总 S 覆盖，S-001..S-024 任一缺 case 即失败。
- 样例是 Phase 1 的“可运行”形态：没有解释器时，`rill parse --dump-ast` 就是唯一端到端可执行入口；不接受“只留临时探针”。

## 7. 红证与提交节奏

- 每个任务先提交 `test(phase1): P1-Txx 红`：只含 case、golden 与红证；RED 命令在 `test` 提交树上运行，必须失败。提交正文含 `red: rc=<N>, "<第一处失败文案>"` 与 `baseline: <test 提交的父 sha>`；`git merge-base --is-ancestor <baseline> HEAD` 必须为真。
- 随后提交 `feat(phase1): P1-Txx …`：实现落地，同一 case 转绿；正文含 `verify: tools/check-phase1.sh --case <ID>` 与原始输出摘要。
- 红证同时写进本卡 §4 对应任务行的“红证”列或 `issues/`；DEV 不自签，VERIFY 认定。
- 纯文档任务（本卡、roadmap）写 `no-test: 纯文档`，不产生红证；不得用纯文档任务顶替实现任务。
- 小块边界：一项任务一个交付物；实现 diff 目标 ≤300 行，超过则先拆任务；任何时刻仓库可构建；不跨任务顺手改；共享工作区有其他会话时只跑 `--case`，全量门禁在任务边界跑。

## 8. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | Phase 0 已交付 `tools/check.sh`/`tools/check-all.sh`；g3/g5/g7/g8 当前为 DISABLED，Phase 1 收口必须启用；构建骨架由 P1-T01 建立；CT 工具链可用；本卡 §2.4 的 registry 元数据与 T-001..T-006 一致；`AGENTS.md` 版本落点由 Phase 0/G0 补齐。 |
| 风险 1 | **换行与空格调用交互**：`read "a"` 换行 `"b"` 必须是两条语句，`read "a"` 换行 `\|> f` 必须续行；`f 1 - 2` 是减法，`f 1` 换行 `- 2` 不是合法延续。探针：`LX-06` 的 `let d = a` 换行 `\|> f b`，期望单条 pipe；`LX-04` 的 `read "a"` 换行 `"b"`，期望两条 expr_stmt。触发信号：token golden 多/少一个 NEWLINE。 |
| 风险 2 | **emit payload 与块界定**：`emit "e"` 换行 `{}` 是空 payload，不是空块；`if x` 换行 `{}` 是块；`emit "e" {}.x` 是语法错误。探针：`EM-01`/`LX-08`/`EM-04` 的 AST 与错误位置。触发信号：`{}` 被解析成 block，或 payload 后接受 `.x`。 |
| 风险 3 | **错误位置计算**：UTF-8 字节列、CRLF 归一、EOF、开定界符、第二个重复键。探针：`LX-10` 的 `let s = "中文" x`（`col` 按字节）、`ER-03` 的未闭合 `{`、`EM-05` 的第二个 `"a"`。触发信号：`col` 按字符计或未闭合指向 EOF。 |

以上探针在本卡只写期望，不实现；实现时先落成 `tests/phase1/cases/` 的红证 case。

## 9. 退出判据（exit-criteria）

§9 即 `exit-criteria` 字段；首个实现提交后冻结，变更须关闭当前 phase 另开。它显式包含“任务清单每项可独立验收（T-6）”。

| # | 条件 | 判定 |
| --- | --- | --- |
| E-1 | `tools/check-phase1.sh --all` 退出码 0；`tools/check-all.sh` 退出码 0（g3/g5/g7/g8 已启用）；§5 全部 case 通过 | 原始输出贴收口对照表 |
| E-2 | `tools/check-phase1.sh --coverage` 显示 S-001..S-024 每条至少 1 个 case | 退出码 0 |
| E-3 | `examples/phase1/` 五个示例 `sexpr` golden 全部相等 | diff 为空 |
| E-4 | 每个负例都断言 `error_kind`/`line`/`col`/文案要点，不止“失败” | case 元数据可枚举 |
| E-5 | 每个任务有红证：`test` 提交是实现的父提交，`baseline` 是实现前 sha 且是 HEAD 祖先 | `git log`/`git merge-base` 原始输出 |
| E-6 | 任务清单每项可独立验收（T-6）；无任务借用“全量门禁全绿” | 收口对照表逐项贴 `verify` |
| E-7 | 无执行语义越界：`src/` 不含 EventBus/PolicySnapshot/ExecLimits 实现；`--scope` 检查通过 | `tools/check-phase1.sh --scope` 退出码 0 |
| E-8 | S-* 验收命令由 REQ 在收口时更新：Phase 1 可覆盖的 M1/M2 部分替换为 `tools/check-phase1.sh --case …`；运行期部分保留 `尚未落盘` 并注明目标 phase；不改行为正文 | `git diff` 仅 S-* 命令行 |
| E-9 | 评审报告结论“通过”，P0=0，P1 已关闭或有目标 phase；无未关闭 `DOC-*` P1 | `reviews/closeout-PH-1.md` |

- 判定人：EDITOR 逐条核 E-1..E-9；VERIFY 签 E-5；REVIEW 签 E-9；USER 只在 tag/push 时介入，不参与中间判定。
- Phase 2 前提：E-1..E-9 全绿；Phase 2 卡已冻结；`DslResult` 与值模型接口在 Phase 2 卡中写死；registry fixture 版本化；无跨 phase 的 P0 缺陷。

## 10. 卡内裁定

AST 形态、擦除、位置、错误阶段、header 保序与 `*` 表示已由 [10 卷](../../spec/dsl/10-ast-position.md) 与 [D-020](../../decisions/D-020.md) 定；本表不再列这些项，也无未决项。旧未决项已由 01 §6、10 §6、07 §3.1 解决。

| # | 事项 | 裁定 | 依据 | 影响判据 |
| --- | --- | --- | --- | --- |
| A-1 | Phase 1 覆盖 09 的 M1+M2，并提前落地 M5/M7 的静态子集（arity/注入/递归/遮蔽/header 默认拒绝），而不是只做 lexer | 合并交付 | 用户指示“完整文法 + AST + 加载期名字校验”；09 §1 原则 3 要求可运行样例；M2 的加载校验依赖 M1 token；这些静态检查没有运行期依赖 | 无（范围定义） |
| A-2 | `$` 注入按词法位置静态判定，不按运行时调用点 | 词法 | 03 §6 要求“个数静态可算”；D-017 `$` 是词法绑定 | LD-13 |
| A-3 | `# allow:` 中的未注册工具不报错 | 允许 | 06 §1 第一层以调用为对象；S-014 C 的 `# deny: exec` 明确允许“即使注册”的未注册名，allow 同理 | HD-01 |
| A-6 | `read -1` 的 `error_kind` 取 `undefined_name` | 取 S-003 已列类别 | S-003 §3 写“undefined_name / 值位错误”；07 §3.1 无专用 kind，10 §5 加载阶段沿用 07 kind | GR-06 |
