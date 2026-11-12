# B1 语法消歧 — 主张席（advocate）

- 席位：主张席（advocate）
- 争点集：B1（工具实参文法、数字字面量、语句终止、postfix `()`、emit 对象字面量）
- 基线 HEAD：`rill-dsl` = `033e5860406b91bbf226a5aa42a1818d520d28c0`；`ct-lang` = `da83aded69c78fdc377e4d3f2e31595709f1c8d2`
- 约束遵守：本文件是本人唯一写入的文件；未运行全量门禁；未 `git add/commit/checkout`。
- 说明：仓库当前**没有 lexer/parser/门禁**（见 §1.3 与 §7.2），所以本席所有“解析结果”都是**文法层面的唯一性论证 + 可实现的一次性预测（E3）**，不是“已跑通”。凡涉及运行时结论一律标 unverified。

---

## 0. 结论速览

| 争点 | 本席主张 | 一句话理由 |
| --- | --- | --- |
| B1-1 实参文法 | **`arg := postfix_atom`**（原子可带 `.`/`[]` 后缀，**不允许**在实参位再发生空格应用）；空格应用在 `tool_call := IDENT arg+` 这一层按书写顺序一次性收集实参（n 元调用）；嵌套必须 `f (g "x")` | 递归实参对“两个 IDENT 起头的常见调用”无解；不递归是唯一能 1 token 前瞻唯一解析的方案 |
| B1-2 数字字面量 | **无符号 `NUMBER := [0-9]+(\.[0-9]+)?`，`-` 只作一元运算符** | 带符号字面量让 `a-1` 被词法吞成 `a(-1)`，属静默误解析，比报错严重一个量级 |
| B1-3 语句终止 | **引入 NEWLINE 作为语句终止符**，并给出 7 条抑制规则（`()`/`[]` 内、管道续行、`}`/`else` 间等） | 用户已定空格调用（D-001）；没有 NEWLINE 就无法区分“第二个实参”和“下一条语句” |
| B1-4 postfix `()` | **彻底删除**；`(` 只保留“分组原子”身份（`f(a)` = `f (a)` = 调用 + 一个分组实参），不保留 `f()()`/`a.b()` | 无函数值、无方法调用；保留它只会制造 `f()()` 这类无法求值的 AST |
| B1-5 emit payload | **只在 `emit STRING` 之后引入受限 JSON 字面量**（对象/数组/表达式值）；`{` 永不作为普通表达式起始，因此与块界定天然消歧 | §8 示例 4 现在无产生式；`emit` 位置是唯一需要字面量的地方，上下文可判定 |

---

## 1. 证据环境（E1）与锚点（E2）

### 1.1 E1 命令与原始输出

命令 1（两个仓库的 HEAD，用于把 E2 锚点钉死在版本上）：

```
$ cd /Users/samxx/trae-ws/rill-dsl && git rev-parse HEAD && cd /Users/samxx/trae-ws/ct-lang && git rev-parse HEAD
033e5860406b91bbf226a5aa42a1818d520d28c0
da83aded69c78fdc377e4d3f2e31595709f1c8d2
```

命令 2（v0.1 中与 B1 直接相关的行，原样输出）：

```
$ cd /Users/samxx/trae-ws/rill-dsl && grep -n -E "数字|arg         :=|arg :=|postfix_expr|primary     :=|emit_stmt|对象字面量|刻意不引入|write \"issues.txt\" a \+ b|write \"summary.txt\" name|emit \"analysis_done\"|find_issues\(" docs/design/dsl-spec-v0.1.md
22:数字      -?[0-9]+(\.[0-9]+)?            整数、浮点
37:刻意不引入：;、()（函数调用参数用空格分隔）、=>、链式方法调用、尾随 lambda。这些是 JS 里最占 token 的样板。
61:             | fn_def | return_stmt | emit_stmt | expr_stmt
70:emit_stmt   := "emit" STRING expr
84:unary_expr  := ("not"|"-") unary_expr | postfix_expr
85:postfix_expr:= primary ("." IDENT | "[" expr "]" | "(" arg_list? ")")*
87:primary     := IDENT (" " arg)*             # 工具调用：name arg1 arg2
92:arg         := primary
158:DSL 无类型注解。值是动态的：null / bool / number / string / json_object / json_array。工具 schema 做浅校验（参数个数、字符串/数字区分），不做深类型检查。
199:对象字面量：{ "key": value } 仅作为 emit 的 payload 语法糖，不作为通用表达式。其他场景需要构造 JSON 时，用 json_build 工具。
324:             | fn_def | return_stmt | emit_stmt | expr_stmt
332:emit_stmt   := "emit" STRING expr
341:unary_expr  := ("not"|"-") unary_expr | postfix_expr
342:postfix_expr:= primary ("." IDENT | "[" expr "]" | "(" arg_list? ")")*
343:primary     := IDENT (" " arg)* | IDENT "(" arg_list? ")"
346:arg         := primary
382:fn find_issues(path) {
391:let a = find_issues("src/a.c")
392:let b = find_issues("src/b.c")
393:write "issues.txt" a + b
404:    emit "analysis_done" { "file": "src/main.c", "count": 3 }
417:        write "summary.txt" name + ":" + dep_count
431:· 通用对象字面量：{ } 仅用于 emit payload 和块界定。
491:M1 Lexer + Parser（工具调用、let、字符串/数字、字段访问） 1500 1–2 周
```

命令 3（CT 侧事实：换行被当空白吞掉、`into`/`$` 的现状）：

```
$ cd /Users/samxx/trae-ws/ct-lang && grep -n -E "c == '\\\\n'|#define T_|unexpected token|nested 'into' blocks|into_node >= 0" selfhost/ct-ast/frontend/lex/Lexer.h.ct selfhost/ct-ast/frontend/parse/Expr.h.ct | head -20
selfhost/ct-ast/frontend/lex/Lexer.h.ct:19:#define T_EOF    0
selfhost/ct-ast/frontend/lex/Lexer.h.ct:20:#define T_ID     1
selfhost/ct-ast/frontend/lex/Lexer.h.ct:21:#define T_NUM    2
selfhost/ct-ast/frontend/lex/Lexer.h.ct:22:#define T_STR    3
selfhost/ct-ast/frontend/lex/Lexer.h.ct:23:#define T_PUNCT  4
selfhost/ct-ast/frontend/lex/Lexer.h.ct:24:#define T_PP     5
selfhost/ct-ast/frontend/lex/Lexer.h.ct:70:            if (c == '\n') { self->bol = 1; self->line++; self->pos++; self->lstart = self->pos; continue; }
selfhost/ct-ast/frontend/parse/Expr.h.ct:98:#define T_EOF 0
selfhost/ct-ast/frontend/parse/Expr.h.ct:99:#define T_ID 1
selfhost/ct-ast/frontend/parse/Expr.h.ct:100:#define T_NUM 2
selfhost/ct-ast/frontend/parse/Expr.h.ct:101:#define T_PUNCT 4
selfhost/ct-ast/frontend/parse/Expr.h.ct:102:#define T_STR 3
selfhost/ct-ast/frontend/parse/Expr.h.ct:2903:            if (self->into_node >= 0) {
selfhost/ct-ast/frontend/parse/Expr.h.ct:2905:                    "nested 'into' blocks are not supported", self->sup->mem->path);
selfhost/ct-ast/frontend/parse/Expr.h.ct:4715:        /* Phase 24: the range index. `$` has no C spelling of its own ... */
selfhost/ct-ast/frontend/parse/Expr.h.ct:4721:            if (self->into_node >= 0) {
selfhost/ct-ast/frontend/parse/Expr.h.ct:4730:            if (!self->dollar_ok) return self->sup->fail("unexpected token");
```

### 1.2 关键锚点（E2：支持与不利于己方各至少一条）

| 编号 | 锚点 | 原文/事实 | 对己方 |
| --- | --- | --- | --- |
| A1 | [dsl-spec-v0.1.md L87-L92](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L87-L92) | `primary := IDENT (" " arg)*`，`arg := primary` | 支持：这就是递归实参，B1-1 要改的原点 |
| A2 | [dsl-spec-v0.1.md L22](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L22) | `数字 -?[0-9]+(\.[0-9]+)?` | 支持：带符号字面量，B1-2 要改的原点 |
| A3 | [dsl-spec-v0.1.md L37](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L37) | 「刻意不引入：;、()…」 | **不利于己方（B1-4）**：原文既说不引入 `()`，同一文档 L85/L342 又允许 postfix `()`；本席必须选一边并承认另一边是原文 |
| A4 | [dsl-spec-v0.1.md L85](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L85) | `postfix_expr:= primary ("." IDENT | "[" expr "]" | "(" arg_list? ")")*` | **不利于己方（B1-1/B1-4）**：原文把 postfix 放在 primary 外层，`read path.field` 因此只能解成 `(read path).field` |
| A5 | [dsl-spec-v0.1.md L70](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L70) + [L332](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L332) | `emit_stmt := "emit" STRING expr`，而 `expr` 不以 `{` 起始 | 支持（B1-5）：示例 4 无法用该产生式解析 |
| A6 | [dsl-spec-v0.1.md L393](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L393) 与 [L417](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L417) | `write "issues.txt" a + b`、`write "summary.txt" name + ":" + dep_count` | **不利于己方（B1-1）**：本席的 `arg := postfix_atom` 仍能“解析”，但会解成 `(write …) + b`，语义错；必须改示例 |
| A7 | [dsl-spec-v0.1.md L391-L392](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L391-L392) | `find_issues("src/a.c")` | 支持/中性：在 D-001 下它不再是独立调用形态；本席把它定义为“调用 + 分组实参”，因此原文示例仍可解析 |
| A8 | [Lexer.h.ct L19-L24](file:///Users/samxx/trae-ws/ct-lang/selfhost/ct-ast/frontend/lex/Lexer.h.ct#L19-L24) + [L70](file:///Users/samxx/trae-ws/ct-lang/selfhost/ct-ast/frontend/lex/Lexer.h.ct#L70) | 词法只有 6 类 token，`\n` 直接 `continue`，不产 token | **不利于己方（B1-3）**：CT 现成 lexer 没有 NEWLINE，复用即需改造 |
| A9 | [Expr.h.ct L2903-L2906](file:///Users/samxx/trae-ws/ct-lang/selfhost/ct-ast/frontend/parse/Expr.h.ct#L2903-L2906) | CT 明确禁止嵌套 `into` | 中性：DSL 若要保留嵌套 `into`（示例 5）就**不能**直接复用 CT 逻辑；与 B1 只在“别声称复用”上相关 |
| A10 | [dsl-discussion.md L122](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L122) | 「`f a b c` 至少有四种分析树」 | 支持（B1-1）：递归实参歧义的既有记录 |
| A11 | [dsl-discussion.md L104-L107](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L104-L107) | 「`read "a"` 换行 `"b"` 会被当成两个实参」 | 支持（B1-3）：NEWLINE 的缺失是实参/语句边界问题 |
| A12 | [dsl-discussion.md L164](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L164) | 「是否彻底删除 postfix `()`（我方倾向：删除…）」 | 支持（B1-4），但只是“倾向”，不是决定 |

### 1.3 E1 可复现的最小环境声明

- 环境：macOS；`docs/decisions/`、`docs/spec/`、`docs/requirements/` 由并行会话维护并已随 HEAD `033e586` 入库，本席**未修改**它们；`battle/B1/seats/advocate.md` 之外无写入。
- 证据席重跑命令 1–3 应得到逐字相同输出；若 `docs/design/dsl-spec-v0.1.md` 行号漂移，说明基线被改动，需要按新 HEAD 重钉锚点。
- **锚点分层**：`docs/design/dsl-spec-v0.1.md`、`docs/spec/S-001-call-form.md`、`docs/decisions/D-001.md` 在 HEAD `033e586` 中均为已跟踪文件（`git ls-files` 三者均有输出，命令见 §1.4）；引用行号以该 HEAD 为准。
- **席位隔离**：按 AGENTS 7.8 T1，本席不读取反证席的 `challenger.md`；§2.6/§3.6/§4.6/§5.6/§6.6 的“对方原文”取自讨论稿中已记录的反方立场与 S-001 的既有口径。交叉质证轮再逐条回应反证清单原文，不在本文件冒充已读。

### 1.4 锚点文件的跟踪状态（E1）

```
$ cd /Users/samxx/trae-ws/rill-dsl && git log --oneline -3 && git ls-files docs/spec/S-001-call-form.md docs/decisions/D-001.md docs/design/dsl-spec-v0.1.md
033e586 docs(design): classify baseline inputs and add repo entry
2d5f95e docs(governance): establish claim, spec and decision layers
362f2da docs(governance): import project AGENTS.md at spec v1.7.0
docs/decisions/D-001.md
docs/design/dsl-spec-v0.1.md
docs/spec/S-001-call-form.md
```

`git status --short` 在本席写入后只显示 `?? battle/`（本席新建的目录），其余引用文件无未提交改动。

---

## 2. B1-1 工具实参文法

### 2.1 主张（明确选边）

选 **`arg := postfix_atom`**，并固定如下形态：

```
tool_call    := IDENT arg+                     # 至少一个实参；空格应用在这一层展开
arg          := postfix_atom
postfix_atom := atom suffix*
suffix       := "." IDENT | "[" expr "]"
atom         := IDENT | STRING | NUMBER | BOOL | NULL | "$" | "(" expr ")"
```

三条硬规则：

1. **实参位不再发生应用**：`f g "x"` = `f(g, "x")`；`f` 之后的每个实参各自贪婪吃成一个 `postfix_atom`，遇到不能续接后缀的 token 即结束。
2. **嵌套要括号**：`f (g "x")` = `f(g("x"))`；`(g "x").y` 合法（atom 是分组，后缀可继续）。
3. **表达式实参要括号**：`write "issues.txt" (a + b)`。`+`/`-`/`*` 等是 `expr` 层运算符，不属于 `arg`。

### 2.2 唯一解析论证（为什么这是唯一解）

**反例 1（致命）：递归实参对多 IDENT 实参无解。**

工具调用的主流形态恰恰是“多个以标识符/字符串起头的实参”：

```
copy src dst
write "issues.txt" content
git_clone repo dir
```

在 `arg := primary` 且 `primary := IDENT (" " arg)*` 下，`copy src dst` 至少有两棵合法树：`copy(src, dst)` 与 `copy(src(dst))`。讨论稿已记录 `f a b c` 的四种树（[L122](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L122)）。要消歧只能加树外规则（“贪心/右结合/看缩进”），而任何一条都让“第二个实参是变量还是嵌套调用的第一个实参”变成不可判定。

**反例 2（会被当成“省 token”的诱惑）：右结合嵌套。**

如果规定“arg 递归且右结合”，`f g "x"` = `f(g("x"))`，看似省一对括号；但 `write "issues.txt" content` 里 `"issues.txt"` 是 STRING 不能应用，于是结果仍是 `write("issues.txt", content)`——**同一套规则对“实参是 IDENT”与“实参是 STRING”给出不同的嵌套能力**。LLM 无法从 token 表面区分，错误要到运行期才暴露。

**反例 3：postfix 归属。**

若保留 v0.1 的 `arg := primary` 且 `postfix` 在调用外层（[L85](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L85)），`read path.field` 只能解成 `(read path).field`（讨论稿 P0-6，[L168-L174](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L168-L174)）。把 postfix 收进实参原子后，`read path.field` = `read(path.field)`，唯一。

**本席方案的解析过程（可机械化）：**

1. 读 `IDENT`；若下一个 token 属于 `arg_start = {IDENT, STRING, NUMBER, true, false, null, $, (}`，则进入调用模式，循环读 `arg`。
2. 每个 `arg`：读一个 atom；若下一个 token 是 `.` 或 `[`，继续吃后缀；后缀结束后若下一个 token 仍是 `arg_start`，那是**下一个实参**，不是嵌套。
3. `arg` 在遇到 `NEWLINE`、`}`、`|>`、`|?`、任何二元运算符、比较符、`and`/`or`、`else`、EOF 时终止；**`into` 也一律终止实参列表**（见下）。

**`into` 的例外必须写死**：`into` 在词法上是 IDENT，若不特殊处理，`read "a" into { … }` 会把 `into` 当成第二个实参（`read("a", into)`），`into_stmt` 永远无法成立。本席主张：**在实参位，`into` 无条件按关键字处理并终止调用**；代价是工具/变量不能以 `into` 为名，P0-7 的保留字表应把 `into` 列为“上下文关键字（实参位与 `expr into {` 位）”。这是 B1-1 与 `into` 语句的交界，必须由规范显式写出，不能靠实现者自行猜测。

这套流程只需 **1 token 前瞻**，无回溯，无歧义。E3 预测：M1 解析 `f g "x"` 的 AST 必须是 `Call(f,[Name(g),Str("x")])`；若出现 `Call(g,...)` 嵌在实参里，本主张即被证伪。

### 2.3 token 成本（与 v0.1 对比）

| 写法 | v0.1 递归（意图） | 本席方案 | 差 |
| --- | --- | --- | --- |
| `read "path"` | 同 | 同 | 0 |
| `grep "foo" "file"` | 同 | 同 | 0 |
| `copy src dst` | 歧义 | `copy src dst` | 0（且唯一） |
| `f (g "x")` | 可能可省括号 | 必写括号 | +2 字符 |
| `write "x" (a+b)` | 有歧义（P0-9） | 必写括号 | +2 字符 |

结论：**最常见的两种形态零成本**；只有嵌套与表达式实参多一对括号，而这正是 LLM 最容易写错的位置——用 2 个字符换确定性，性价比为正。

### 2.4 实现量级（E4）

- 文法：`docs/design/dsl-spec-v0.1.md` §3.3（L84-L92）与 §7（L341-L346）各改约 4 行；新增 `postfix_atom` 一个非终结符。
- 解析器：一个实参循环 + 一个 `arg_start` 集合 + 终止集合，约 30–40 行 CT；无需回溯栈。
- 门禁：M1 golden 用例新增约 8 条（多 IDENT 实参、嵌套、后缀实参、表达式实参、`read -1` 报错）。
- 回退步骤：把 `arg := postfix_atom` 改回 `arg := primary` 并恢复 `primary := IDENT (" " arg)*` 即可，解析器改动可整体 revert，不影响词法。

### 2.5 对已有文档示例的影响（诚实账）

- 示例 1/2/4 不受影响（无嵌套实参、无表达式实参）；**示例 3 与示例 5 的 `+` 实参会变成“调用后再相加”**：
  - [L393](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L393) `write "issues.txt" a + b` → `(write "issues.txt" a) + b`
  - [L417](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L417) `write "summary.txt" name + ":" + dep_count` → `(write "summary.txt" name) + ":" + dep_count`
- 这两条在 v0.1 的 `arg := primary` 下同样错（P0-9，[L198-L206](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L198-L206)），**不是本席引入的新失效**；本席主张随文法一起把它们改成 `(a + b)` / `(name + ":" + dep_count)`，并写明“实参是原子，不是表达式”。
- [L391-L392](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L391-L392) 的 `find_issues("src/a.c")` 在 D-001 下仍可解析为“调用 + 分组实参”，不失效；但 S-001 建议改写为空格形态，属风格问题。

### 2.6 预判反证席（E5 steelman + 回应）

**预判反证 A（最可能）**：引用讨论稿“空格应用不递归”的倾向，主张把 `postfix_expr` 直接当 arg 且允许 `f (g "x")`，但**同时保留** `primary` 的 `IDENT (" " arg)*`，认为“解析器可以贪心取最长实参”。反驳：贪心无法处理 `copy src dst`——贪心会把 `src` 当嵌套调用并尝试把 `dst` 当它的实参，得到 `copy(src(dst))`；除非引入“只有被调方已知 arity 时才嵌套”，那就要在**解析期查工具注册表**，而注册表在加载期才可用，解析期不可知。语法制导解析必须与 arity 解耦。

**预判反证 B**：引用 §1“省 token 优先”（[L9](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L9)），认为多两字符违背原则。反驳：原则原文是“每个语法特性必须证明它能压缩 LLM 最常写的模式”；`read "path"`、`grep "a" "b"` 不变，成本只落在低频嵌套上，且减少的是**错误率**，而 §12 的验收指标明确包含“语法错误率低于 20%”（[L504](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L504)）。token 省 2 个、错误率上升，净值为负。

---

## 3. B1-2 数字字面量

### 3.1 主张

选 **无符号字面量**，`-` 只作一元运算符：

```
NUMBER      := [0-9]+ ("." [0-9]+)?
unary_expr  := ("not" | "-") unary_expr | postfix_expr     # 保留 v0.1 L84/L341 的已有形态
```

配套错误提示（必须随实现一起落地，否则本主张的收益减半）：

```
path:line:col: error: a negative number cannot be an argument here.
  Hint: parenthesize it: read (-1)
```

### 3.2 唯一解析论证

词法层用最大吞噬（maximal munch），这是所有实现都会自然采用的行为。对比两种词法：

| 输入 | 带符号 `-?[0-9]+(\.…)?` | 无符号 `[0-9]+(\.…)?` |
| --- | --- | --- |
| `a - 1` | `a - 1`（三 token，减法） | `a - 1`（减法） |
| `a-1` | `a`、`-1` → 相邻 primary；在空格调用文法下被读成 `a(-1)` | `a`、`-`、`1` → 减法 |
| `x-1` | `x(-1)`（静默变成调用） | `x - 1` |
| `1-2` | `1`、`-2` → 两个相邻 primary，**不是减法也不是合法调用** | `1 - 2` |
| `f 1-2` | `f(1, -2)`（静默变成两个实参） | `(f 1) - 2` |
| `read -1` | `read(-1)`（正确） | `read - 1` → `read` 作值使用，加载期报错 + hint |

**核心论点是第 5 行**：带符号字面量会把 `f 1-2` 这种“本意是减法”的输入静默变成“两个实参”。静默语义漂移是 LLM 自纠错回路最难发现的一类错误——它不报错，只是算错。无符号词法则把同一串 token 稳定地读成减法，唯一需要额外字符的只有“实参确实是负数”这一低频场景。

**v0.1 的隐含矛盾**：`primary := IDENT (" " arg)*`（[L87](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L87)）把“空格”写进了产生式。若空白在词法阶段被跳过（任何常规 lexer 都如此，CT 亦如此，见 [Lexer.h.ct L70-L71](file:///Users/samxx/trae-ws/ct-lang/selfhost/ct-ast/frontend/lex/Lexer.h.ct#L70-L71)），这个空格不可实现；若真按空格敏感词法实现，`read"path"` 与 `read "path"` 就分属两种语法，错误面反而扩大。带符号字面量只有在“空格敏感”前提下才安全，二者绑定；既然 D-001 的调用形态依赖空格分隔，就不能再让词法对空格敏感。

### 3.3 token 成本

- 负数字面量在现有 5 个示例中出现 **0 次**（§8 只有 `"count": 3` 等非负值；可用命令 2 的原始输出核对）。
- 每次需要负数实参时多 `(` 与 `)` 两个字符；对比带符号词法在 `a-1` / `f 1-2` 上造成的静默错误，成本不对称。
- 一元 `-` 已在 v0.1 文法中存在（[L84](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L84)、[L341](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L341)），不新增语法能力。

### 3.4 实现量级（E4）

- 词法：`NUMBER` 正则去掉 `-?`，1 行；`-` 归入已有 `算术` 标点，0 行新增。
- 文法：删除词法表 L22 的 `-?`；`unary_expr` 无需改动。
- 解析器：0 行新增（一元 `-` 已有优先级位置）。
- 门禁：新增 5 条 golden（`a-1`、`1-2`、`f 1-2`、`read -1` 报错、`read (-1)` 通过）。
- 回退：正则加回 `-?` 并补 `f 1-2` 的“实参吞并”测试；回退影响词法一处，解析器无需回退。

### 3.5 对已有文档示例的影响

- §8 五个示例**全部不受影响**（无负数实参）。
- 讨论稿 §6.3 表格里“`read -1` → 非法实参；写 `read (-1)`”（[L446](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L446)）与本主张一致，属既有倾向被确认。
- 唯一“失效”的是 v0.1 词法表 L22 的写法本身，必须改写为无符号；这是本争点的目的。

### 3.6 预判反证席（E5）

**预判反证 A**：`read -1` 是最自然的写法，LLM 会写，要求括号会增加错误率。回应：本主张不靠“LLM 不写负数”成立，而靠**报错可纠正**：`read -1` 在无符号词法下解成 `Name(read) - 1`，加载期即可判定“`read` 是工具名，不能作值”，给出 `Hint: parenthesize it: read (-1)`。带符号词法把同一个输入解成“正确调用”，代价是 `a-1` 与 `f 1-2` 变成静默错误——用“低频正确”换“高频静默错”，不划算。若实测负数实参占比 >5%，可重开本争点（失效条件，见 §7）。

**预判反证 B**：一元 `-` 与二元 `-` 在同一 token 上靠上下文区分，会让 `f -1` 的报错位置不精确。回应：无符号词法下 `f -1` 的 `-` 稳定是二元减（因为 `-` 不在 `arg_start` 集合里），解析结果确定；错误位置落在 `read` 这个“工具名作值”的 token 上，不是猜出来的。精度由名字解析阶段保证。

---

## 4. B1-3 语句终止（NEWLINE）

### 4.1 主张：NEWLINE 是语句终止符，并按 7 条规则抑制

```
program     := header? (NEWLINE | statement)* EOF
statement   := let_stmt | if_stmt | for_stmt | into_stmt
             | fn_def | return_stmt | emit_stmt | expr_stmt      # P1 的 while/assign/break/continue 不在 B1 范围
NEWLINE     := "\n" | "\r\n"          # 连续多个折叠为一个逻辑终止
```

抑制规则（前 5 条为必需，后 2 条为消除常见误报）：

| # | 规则 | 理由 |
| --- | --- | --- |
| N1 | 语句以 NEWLINE、`}` 或 EOF 终止；空行折叠 | 语句列表需要边界；`if x { a }` 单行也能成立 |
| N2 | `(` 与 `[` 内部的 NEWLINE 一律忽略 | 分组与索引天然是多行上下文，且内部不能出现语句 |
| N3 | `{}` 内部的 NEWLINE 仍是语句终止符（普通块；emit payload 的 JSON 字面量除外，见 §6） | `{}` 是语句列表；`if/for/into/fn` 都靠它切分 |
| N4 | NEWLINE 紧跟在 `\|>` 或 `\|?` 之后时忽略（管道续行） | 管道是最常见的跨行形态 |
| N5 | NEWLINE 之后的首个非空 token 是 `\|>` 或 `\|?` 时忽略（前导管道续行） | LLM 常把 `\|>` 写在行首；与 N4 合起来才覆盖两种写法 |
| N6 | `}` 与 `else` 之间的 NEWLINE 忽略 | `} \n else {` 是主流排版 |
| N7 | 控制头 `if expr`、`for id in expr`、`expr into`、`fn id(...)` 后若遇 NEWLINE 且下一 token 是 `{`，忽略该 NEWLINE；`emit STRING` 后接 payload 的同类规则见 §6.1 规则 4 | `{` 永不作为表达式起始（见 §6），因此无歧义；禁止它只会制造无收益的报错 |

补充两条硬规则：

- **一次调用不能跨逻辑行**：实参必须与工具名在同一逻辑行（N2/N4/N5 的抑制除外）。这是 N1 的直接推论。
- **同一行只能有一条语句**：`if x { write "a" write "b" }` 会被解析成**一条**调用 `write("a", write, "b")`（`write` 在实参位是名字，不是调用）；加载期因“工具名不能作值”或参数个数不符而报错，并给 hint“one statement per line”。这是本主张的已知弱点（第二行意图不可从 token 表面恢复），规范必须写明“一行一条语句”。

### 4.2 唯一解析论证（为什么 MUST 有 NEWLINE）

**反例 1（决定性，且是 D-001 的直接后果）**：

```
read "a"
"b"
```

若换行只是空白，`read "a" "b"` 是**两次实参**，无法表达“第一条语句是 `read "a"`，第二条是字符串表达式”。也就是说：**用户选定空格调用之后，换行是唯一能把“第二个实参”与“下一条语句”分开的东西**。这不是风格问题，是表达力问题。讨论稿已记录同一现象（[L104](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L104)）。

**反例 2（静默合并）**：

```
let x = 1
-2
```

无 NEWLINE 时，`-` 是二元运算符，第二行被并进第一行变成 `let x = 1 - 2`；两条本意独立的语句静默变成一条。NEWLINE 终止后，第二行是 `-2`（合法的 unary 表达式语句），语义稳定。

**反例 3（块头）**：`if x` 换行 `{` 是否合法必须写死，否则不同实现的 accepted 集合不同。本主张选“合法”（N7），因为 `{` 不可能是表达式，判定成本为 0。

**为什么不是 `;`**：§2 明确“刻意不引入 `;`”（[L37](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L37)），且每行多 1 token，直接违背 §1 的省 token 优先。NEWLINE 是**零 token**（不出现在源码文本里，只出现在 token 流）。

**为什么不是缩进**：§2 已给理由（[L39](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L39)）：“缩进错误在 LLM 输出里极常见且难以定位”。本主张不重开这一条。

**唯一性检查**：给定 token 流，语句边界只由 NEWLINE/`}`/EOF 决定；N2、N4–N7 都是“删除特定位置的 NEWLINE token”，是单向过滤器，不会产生两种可选解析。E3 预测：对上面反例 1，M1 必须产出**两条**语句（`Expr(Call(read,["a"]))`、`Expr(Str("b"))`）；若产出单条 `Call(read,["a","b"])`，本主张被证伪。

### 4.3 token 成本

- 源码层面 **+0 token**；token 流层面每条语句 +1 个内部 NEWLINE（不计入 LLM 输出，不计入提示词）。
- 对比 `;` 方案：每行 +1 个 LLM 输出 token，按 §12 的 10 个真实任务估算，属净增。
- 对比“无终止符 + 靠解析失败恢复”：不增加源码 token，但把确定文法变成错误恢复启发式，`read "a"\n"b"` 直接不可表达。

### 4.4 实现量级（E4）

- 词法：新增 `T_NEWLINE`；`\n`/`\r\n` 不再 `continue`；N4/N5 需要 1 个 token 的前瞻或一个“上一有效 token”状态，约 25–35 行。
- 解析：`stmt_list` 跳过 NEWLINE；`( )`/`[ ]` 内部跳过；`}` 后探测 `else`；控制头后探测 `{`；约 40–60 行。
- 门禁：新增约 12 条 golden（跨行实参、空行、行首管道、`}`/`else`、`if x\n{`、反例 1/2）。
- 回退：NEWLINE 只影响词法产 token 与解析跳过点；回退时把 `\n` 恢复为 `continue` 并删跳过点，约 1 次 revert。
- 与 CT 的关系：CT 现成 lexer 把 `\n` 当空白（[Lexer.h.ct L70](file:///Users/samxx/trae-ws/ct-lang/selfhost/ct-ast/frontend/lex/Lexer.h.ct#L70)），**不能直接复用**；DSL 是新 parser（讨论稿 §5 结论，[L364](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L364)），不存在“改造 CT 主干”的风险。

### 4.5 对已有文档示例的影响

- §8 五个示例全部是“一行一条语句 / 块头与 `{` 同行”，N1–N7 下**全部可解析**（B1-5 修好后示例 4 亦然）。
- 唯一需要补写的是**规范正文**：v0.1 词法表没有 NEWLINE（[L19-L35](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L19-L35)），必须把 N1–N7 写进 §2/§3.2。
- 讨论稿 §6.2 的 `stmt_list := (NEWLINE | statement)*`（[L397](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L397)）与本主张一致，可直接吸收。

### 4.6 预判反证席（E5）

**预判反证 A**：NEWLINE 让解析器状态变多，跨行表达式会频繁报错，不如“换行当空白 + 依赖 arity/错误恢复”。回应：状态数是常数（一个 `prev_token` + 一个 `delim_depth`），不随程序规模增长；而“换行当空白”在 D-001 下连 `read "a"\n"b"` 都无法表达（§4.2 反例 1）。牺牲可表达性换实现简单，不可接受。

**预判反证 B**：N5（行首管道续行）会让 `|>` 在语句开头出现时难以区分“续行”与“新语句”。回应：DSL 没有“以 `|>` 开头的语句”，`|>` 不是任何语句的首 token；因此在语句边界处看到 `|>` 唯一可能的解释就是续行。若解析器已在语句内，`|>` 按二元运算符处理；两种位置不重叠。

**预判反证 C**：N7 允许 `if x\n{` 会诱导 LLM 学成 Rust 风格，然后 `for` 也照写。回应：允许不等于推荐，few-shot 仍只展示同行写法；允许它是为了把“排版差异”从错误里剔除，错误预算应留给真正的语义问题（工具名、参数个数）。

---

## 5. B1-4 postfix `()` 是否保留

### 5.1 主张：删除 postfix 调用，`(` 只保留“分组原子”

```
postfix_expr := tool_call | atom suffix*
tool_call    := IDENT arg+
arg          := atom suffix*
atom         := IDENT | STRING | NUMBER | BOOL | NULL | "$" | "(" expr ")"
suffix       := "." IDENT | "[" expr "]"
fn_def       := "fn" IDENT "(" param_list? ")" block
```

关键点：`f(a)` **不**被解释为 postfix 调用，而是“`tool_call f` + 一个分组实参 `(a)`”，与 `f (a)` 完全同构。这正是 [S-001 L25](file:///Users/samxx/trae-ws/rill-dsl/docs/spec/S-001-call-form.md#L25) 的口径：“`analyze_file "src/a.c"` 在语法上都是‘一个调用 + 一个分组实参’”。

### 5.2 唯一解析论证

- `f()()`：`f` 后的第一个 `(` 进入 atom，期望 `expr`，立即遇 `)` → 报错“empty parentheses; an argument or grouped expression is required”。第二个 `()` 不再有产生式可达。**不会**产生 `f()()` 链。
- `a.b()`：`a.b` 是完整 `postfix_expr`；`(` 不是后缀、也不是二元运算符，语句无法继续 → 报错“unexpected '('; method calls are not supported. Call a tool instead, e.g. `b a`”。**不会**产生“先取字段再调用”。
- `f(a)(b)`：`f` + 两个分组实参 `(a)`、`(b)`，即 `f(a, b)`。这是“括号只是分组”的**必然推论**，没有第二种解释；它不是歧义，只是排版少见。规范应明文写出，避免实现者各自发明“第二个 `(` 开始新调用”。
- `f(a,b)`：`(` 内是 `expr`，`expr` 不含 `,` → 在 `,` 处报错，hint“calls are space-separated: `f a b`”。这样 D-001 的迁移错误能在解析期被抓住。
- `(read "x").y`：atom 是分组，后缀 `.y` 作用于分组 → 合法。这给出“对调用结果取字段”的唯一写法，补偿 `read "x".y`（按 §2 规则会被解成 `read(("x").y)`，是对字符串取字段）。
- `read "x".y` 的语义必须明说：后缀绑定**最近的 atom**，所以是 `read("x".y)`。要取结果字段请写 `(read "x").y` 或 `let r = read "x"` 后 `r.y`。这不是歧义，是一条必须写进规范的绑定规则。

E3 预测：M1 对 `f()()` 必须在第一个 `)` 报错；若成功产出 `Call(Call(f,[]),[])`，本主张被证伪。

### 5.3 token 成本

- 删除 postfix `()` **不增加**任何写法成本：常用调用与字段访问形态不变；`f(a)` 仍可写（且与 `f a` 等价），所以从 v0.1 迁移的脚本不会因删除而大面积失败。
- 唯一增加成本的是“对调用结果取字段”：需 `(read "x").y` 的 2 个字符，或先 `let` 绑定；这在 v0.1 里本来也走不通（v0.1 的 `postfix_expr` 允许 `(read "x").y`，但同一文法也让 `read path.field` 绑错，二选一）。
- 保留 postfix `()` 的“收益”只存在于 `f()()`/`a.b()`，而这两者都需要一等函数或方法调用，§2 已明确不做（[L37](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L37)），§9 再次明确“链式调用”不做（[L430](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L430)）。

### 5.4 实现量级（E4）

- 文法：删除 `postfix_expr` 的第三个分支，1 行（[L85](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L85)、[L342](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L342)）。
- 解析器：删掉一个分支 + 增加一个 `(` 的报错路径（带 hint），约 10–15 行；**净减少**代码。
- 门禁：新增 4 条 golden（`f()()` 报错、`a.b()` 报错、`f(a,b)` 报逗号错、`(read "x").y` 通过）。
- 回退：恢复一个分支即可；回退不影响词法与 B1-1/B1-3。

### 5.5 对已有文档示例的影响

- [L391-L392](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L391-L392) 的 `find_issues("src/a.c")` **仍可解析**（调用 + 分组实参），但按 D-001 应改写为 `find_issues "src/a.c"`；本主张不使该示例失效。
- 其余示例没有 `f()` / `a.b()` 形态（命令 2 的原始输出可核对：L382-L393 只有 `fn find_issues(path)` 与两次括号调用）。
- 失效的是 v0.1 §2 与 §3.3 的**自相矛盾**本身：本主张选 §2，删除 §3.3 的 postfix 分支。

### 5.6 预判反证席（E5）

**预判反证 A（最强）**：删掉 postfix `()` 后，用户函数零参调用 `f()` 没有写法；而 S-001 又说 `f(a)` 只是“调用 + 分组”，那 `f()` 自然应读成“零参调用”。回应：这是两个不同问题。文法上 `f()` 是“空分组”，空分组不是 `expr`，所以必须报错；零参调用的正确写法是**裸名字** `f`，由加载期名字解析判定（本地变量 → 零参 fn/tool → 否则报错）。`f()` 若被接受，就必然需要“空分组=调用”的特例，而那正是 postfix `()` 的残余。裸名字方案既满足零参，又不引入链式调用。注意：这条**属于 P-018 的名字解析范围**，本席只主张解析层“`f()` 报错”，不替 P-018 拍板解析顺序。

**预判反证 B**：`f(a)(b)` 被读成 `f(a,b)` 是危险的静默接受，应报错。回应：可以加一条**语法层禁令**——“一个调用的实参列表中，若某个实参是分组且其后紧邻另一个分组，报错并提示去掉一组括号”。但这条禁令本身需要额外规则，且会误伤 `f (a) (b)` 这种“两个分组实参”的合法写法（虽然罕见）。本席选择**不禁止**、只写进规范，理由是：`f(a)(b)` 没有任何其他可解释含义，静默接受不会改变作者本意（作者写 `f(a)(b)` 时想要的就是 `f(a)(b)` 这个调用，只是把参数写成了括号形式）；真正危险的是“同样文本有两种含义”，这里没有。若评审认为必须报错，本席接受把它降级为实现建议，不影响 B1-4 主结论。

---

## 6. B1-5 emit 的 `{ "key": value }`

### 6.1 主张：只在 `emit STRING` 的 payload 位置引入受限 JSON 字面量

```
emit_stmt    := "emit" STRING emit_payload
emit_payload := json_value
json_value   := json_object | json_array | expr
json_object  := "{" json_members? "}"
json_members  := json_pair ("," json_pair)*
json_pair    := STRING ":" json_value
json_array   := "[" json_values? "]"
json_values  := json_value ("," json_value)*
```

四条硬规则：

1. **位置受限**：`json_object` / `json_array` 只出现在 `emit_payload`（含其嵌套值）中；**任何**其他表达式位置都不以 `{` 或 `[` 起始。`[` 在表达式里只作**后缀索引**（`x[0]`），不是数组字面量。
2. **键必须是字符串字面量**；非 STRING 键报错“object keys must be quoted strings”。
3. **无尾随逗号**；出现 `,]` / `,}` 报错并提示删除。**重复键是加载期错误**（键是字面量，可静态判定），不是运行期 last-wins。
4. **JSON 内部的 NEWLINE 忽略**（与 B1-3 的 N3 相反，因为 JSON 里不可能有语句）；`emit STRING` 与 payload 起始之间的 NEWLINE 也忽略（同 N7 的理由：`{`/`[` 不可能是表达式）。

### 6.2 唯一解析论证（与块界定消歧）

**为什么 `if expr {` 不会误读成对象**：`expr` 的产生式里没有任何分支以 `{` 起始（v0.1 [L77-L92](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L77-L92) 与本主张均如此）。因此 `if` / `for` / `into` / `fn` 之后的 `{` 只能是块。**块 `{` 与对象 `{` 的判定不靠“看里面像不像语句”，而靠“当前位置是否允许表达式起始 `{`”**——本主张把它永远设为“不允许”，判定退化为 1 个上下文标志。

**为什么 `emit "x" {` 不会误读成块**：`emit` 的语句位置没有“块”这一选项；`emit STRING` 之后只接受 payload。因此这里的 `{` 只能是 JSON 对象。两个上下文互斥，不需要回溯。

**反例（证明 v0.1 现状不可用）**：§8 示例 4（[L404](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L404)）与 R7 的例子（[L189](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L189)）都写 `emit "..." { "k": v }`，而 `emit_stmt := "emit" STRING expr`（[L70](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L70)、[L332](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L332)）没有 `{` 起始的 expr。**今天的规范无法解析自己的示例**——这是本争点必须修的硬证据。

**嵌套与边界**：

- `emit "e" { "a": { "b": [1, 2] } }`：对象→对象→数组，括号严格配对，无歧义。
- `emit "e" { "n": -1 }`：`json_value := expr` 覆盖一元 `-`（B1-2），无需在 JSON 里另设带符号数字。
- `emit "e" { "s": a + b }`：`expr` 在 `,` / `}` 处终止，`+` 不会吞掉分隔符；这是安全的，因为 `,` 与 `}` 都不是 `expr` 的延续 token。
- `emit "e" { }` / `emit "e" []`：空 payload 合法。
- `emit "e" { "k": 1 }.k`：对象后不允许后缀（`json_value` 不接 `suffix`），报错“unexpected '.'”；payload 是事件数据，不是可继续访问的值。
- 同行的 `if x { emit "e" { "k": 1 } }`：内层对象先闭合，外层块的 `}` 后到；平衡括号保证不串。

E3 预测：示例 4 的 AST 必须是 `Emit("analysis_done", Obj{("file", Str("src/main.c")), ("count", Num(3))})`；若 M1 在 `{` 处报“unexpected token”，本主张被证伪。

### 6.3 token 成本

- 事件 payload 是 `emit` 的常态写法；对象字面量是**最短**表达。替代方案 `json_build` 要么仍需字面量语法（等于本主张），要么退化为 JSON 字符串转义：`json_build "{\"path\":\"a\"}"`，把 `"` 全部翻倍，token 与错误率双升。
- 词法新增 `:` 与 `,` 两个标点（v0.1 §2 词法表只列了 `.`、`[ ]`、`{ }`，**没有**列 `:` 与 `,`，见 [L19-L35](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L19-L35)；尽管 §3.3 的 `arg_list`/`param_list` 已在用逗号）；`,`、`{`、`}`、`[`、`]` 在源码里已出现，但只有 `:` 与 `,` 需要补进词法表。
- 表达式层零新增：`{` 不被任何表达式分支接受，普通脚本不受影响。

### 6.4 实现量级（E4）

- 文法：新增 `emit_payload`/`json_value`/`json_object`/`json_members`/`json_pair`/`json_array`/`json_values` 七个非终结符，约 9 行；删除 `emit_stmt := "emit" STRING expr` 中的 `expr`。
- 解析器：一个 JSON 值递归解析器，约 55–70 行；JSON 内 NEWLINE 跳过约 10 行；重复键静态检查约 20 行。
- 词法：`:` 与 `,` 入标点表，2 行。
- 门禁：新增约 10 条 golden（空对象、嵌套、数组、负数、重复键报错、尾随逗号报错、非字符串键报错、与 `if {` 消歧、示例 4 原文）。
- 回退：删除五个非终结符与解析函数即可；不影响 B1-1..B1-4。

### 6.5 对已有文档示例的影响

- **修复**：§8 示例 4（[L404](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L404)）与 R7 例子（[L189](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L189)）从“不可解析”变为“可解析”。
- **不变**：其余四个示例不含 JSON 字面量；`into` 块仍是块（`{` 在 `into` 后），不会被当成对象。
- **必须补写**：§4 R7 的散文“对象字面量…仅作为 emit 的 payload 语法糖，不作为通用表达式”（[L199](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L199)）已给出方向，但缺少产生式；本主张把它落成文法。
- **`json_build` 的地位**：全仓只有 [L199](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L199) 一次提及，无接口、无 schema、无示例（命令 2 的 grep 可核对 `json_build` 仅 L199 命中）。本主张不改它，但指出“用 json_build 替代字面量”在当前规范里没有可依赖的定义。

### 6.6 预判反证席（E5）

**预判反证 A（最强）**：对象字面量是通用语言特性，一旦开了口子，LLM 会写 `let cfg = { "a": 1 }`，然后要求通用对象表达式，破坏“最少语法”。回应：文法上**没有**这个口子——`{` 在表达式位置一律报错，错误信息明确写“object literals are only allowed as emit payload; use json_build”。这是**生产式级**限制，不是约定级限制；LLM 写错会立即得到可纠正的错误，而不是被默许。反过来说，禁止 payload 字面量并没有减少“对象”这个概念，只是把它赶到 `json_build` 字符串里，错误率更高。

**预判反证 B**：`json_value := expr` 让 payload 里可以写任意表达式（管道、比较），范围过大，且与“payload 是数据”冲突。回应：payload 值需要变量、字段、`$`、算术（如 `"count": n + 1`），这些正是 `expr`；若收窄为“仅字面量”，示例 4 的 `"count": 3` 能过，但真实事件几乎都要带变量，会迫使作者先 `let` 再引用，反而更长。真正的边界由**终止符**保证：JSON 值在 `,` / `}` / `]` 处结束，`expr` 不含这些 token，不会越界。若实测出现“payload 里写管道导致难读”，可把 `json_value` 收窄到 `unary_expr`，属可回退的实现级调整。

**预判反证 C**：重复键报加载错会让“后写覆盖前写”的合法用法消失。回应：事件 payload 的重复键几乎总是笔误（复制粘贴），静态报错成本低、收益高；若确有覆盖需求，用不同事件名或 `json_build` 显式构造。该规则与 §1“错误信息给 LLM 看”一致（[L12](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L12)）。

---

## 7. 合并后的文法（五条主张的交点）

```
program       := header? (NEWLINE | statement)* EOF
header        := header_line*
header_line   := ("# allow:" IDENT_LIST) | ("# deny:" IDENT_LIST) | ("# emit:" IDENT_LIST)

statement     := let_stmt | if_stmt | for_stmt | into_stmt
               | fn_def | return_stmt | emit_stmt | expr_stmt
let_stmt      := "let" IDENT "=" expr
if_stmt       := "if" expr block ("else" block)?
for_stmt      := "for" IDENT "in" expr block
into_stmt     := expr "into" block
fn_def        := "fn" IDENT "(" param_list? ")" block
return_stmt   := "return" expr?
emit_stmt     := "emit" STRING emit_payload
expr_stmt     := expr
block         := "{" (NEWLINE | statement)* "}"

expr          := or_expr ("|>" or_expr)*
or_expr       := and_expr ("or" and_expr)*
and_expr      := cmp_expr ("and" cmp_expr)*
cmp_expr      := add_expr (("=="|"!="|"<"|">"|"<="|">=") add_expr)?
add_expr      := mul_expr (("+"|"-") mul_expr)*
mul_expr      := unary_expr (("*"|"/"|"%") mul_expr)*
unary_expr    := ("not"|"-") unary_expr | postfix_expr
postfix_expr  := tool_call | postfix_atom
tool_call     := IDENT arg+
arg           := postfix_atom
postfix_atom  := atom suffix*
suffix        := "." IDENT | "[" expr "]"
atom          := IDENT | STRING | NUMBER | BOOL | NULL | "$" | "(" expr ")"

emit_payload  := json_value
json_value    := json_object | json_array | expr
json_object   := "{" json_members? "}"
json_members  := json_pair ("," json_pair)*
json_pair     := STRING ":" json_value
json_array    := "[" json_values? "]"
json_values   := json_value ("," json_value)*
```

说明：

- `tool_call := IDENT arg+` 是“空格应用”的唯一产生式；**实参位（`arg`）只到 `postfix_atom`，不含应用**，所以 `f g "x"` = `f(g, "x")`。
- `NUMBER := [0-9]+("." [0-9]+)?`；`-` 只在 `unary_expr`。
- `block` 里的 `NEWLINE` 由 N1–N7 过滤；`{}` 在 `json_object` 里不走 `block`，其 NEWLINE 全忽略。
- `|?` 的优先级/失败单元属 P-012，不在 B1；本合并文法为聚焦 B1 未展开 `fallback_expr`，N4/N5 对 `|?` 的抑制规则在 P-012 定稿后同样适用。
- 本合并文法**仍然只是提案**，不是已生效规范；落盘须经裁判与用户。

### 7.1 五条主张的交叉点（互相不能打架）

| 交叉 | 结论 | 验证输入 |
| --- | --- | --- |
| B1-1 × B1-2 | `f -1` = `(f) - 1`；`f (-1)` = `f(-1)`；`read -1` 在加载期报“工具名不能作值”+ hint | `read -1`、`read (-1)` |
| B1-1 × B1-3 | 实参不跨逻辑行；`read "a"` 换行 `"b"` = 两条语句 | 反例 1 |
| B1-1 × B1-4 | `f(a)` = `f (a)` = 调用 + 分组实参；`f(a)(b)` = `f(a,b)`；`f()` 报错 | 四个输入 |
| B1-3 × B1-5 | 块 `{}` 内 NEWLINE 是终止符；JSON `{}` 内 NEWLINE 忽略；`emit STRING` 后允许换行再接 payload | 多行 emit、多行 if |
| B1-4 × B1-5 | `emit "e" [...]` 的 `[` 是数组字面量；表达式位置的 `[` 仍是索引后缀 | `emit "e" [1]` vs `x[1]` |

### 7.2 E4 汇总（代价量化）

| 项 | 数值 |
| --- | --- |
| 需改文件（文档） | 1 个：`docs/design/dsl-spec-v0.1.md`（§2 词法表、§3.2、§3.3、§4 R7、§7、§8 示例 3/4/5） |
| 需改文件（代码） | 0 个：仓库无 lexer/parser/门禁（`docs/spec/S-001-call-form.md` §3 明说“尚未实现”，[L36](file:///Users/samxx/trae-ws/rill-dsl/docs/spec/S-001-call-form.md#L36)） |
| 预计解析器新增 | 约 200–260 行 CT（B1-1 40 + B1-3 90 + B1-5 90），B1-2/B1-4 为净减少或 0 |
| 门禁影响 | 无既有门禁可跑；M1 需新增约 39 条 golden（8+5+12+4+10） |
| 回退步骤 | 文档单 commit 反转；解析器按 §2.4/§3.4/§4.4/§5.4/§6.4 各自的“回退”段逐条 revert，五项互不依赖 |
| 版本号 | 无产品版本号，不 bump；不触发 Phase 版本策略 |

### 7.3 E3 汇总（一次性可证伪预测）

| 主张 | 输入 | 预测 | 证伪条件 |
| --- | --- | --- | --- |
| B1-1 | `f g "x"` | `Call(f,[Name(g), Str("x")])` | 出现嵌套 `Call(g,…)` |
| B1-2 | `f 1-2` | `Sub(Call(f,[1]), 2)` | 出现 `Call(f,[1,-2])` |
| B1-3 | `read "a"\n"b"` | 两条语句 | 单条两实参调用 |
| B1-4 | `f()()` | 第一个 `)` 处报错 | 产出链式调用节点 |
| B1-5 | §8 示例 4 原文 | `Emit(..., Obj{…})` | `{` 处 unexpected token |

---

## 8. 我可能错在哪

1. **B1-1 的最大风险是“LLM 嵌套调用频率被我低估”。** 我用“最常写的是 `read "path"`/`grep "a" "b"`”来论证零成本，但若真实任务里 `f (g x)` 形态占比高，强制括号会让错误率上升。这正是 M1 路径 A/B 实验要测的；若实测嵌套错误 ≥3 次/同提示（讨论稿 [L476](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L476)），本主张应重开。
2. **B1-1 与 B1-4 合起来会让 `read "x".y` 静默变成“对字符串取字段”。** 我承认这是本方案最反直觉的一条，只能靠规范明文与错误信息弥补；若评审认为它比“调用后取字段”更常被写错，可能需要引入“后缀只允许作用于 IDENT/分组，不允许作用于字面量”的额外限制（那会增加文法复杂度，我倾向不做）。
3. **B1-2 的“负数实参低频”是估计，不是实测。** 我没有 LLM 真实输出样本；若实测负数（坐标、偏移、温度等）占比不低，`read (-1)` 的括号成本会被放大。缓解是错误信息必须带 `Hint`，但这不是零成本。
4. **B1-3 的 7 条抑制规则可能不全。** 例如 LLM 可能写“行尾 `and`/`or` 续行”或“行尾 `+` 续行”，我的 N1–N7 不覆盖，会报错。我选择“先窄后宽”，因为宽抑制会把真正的语句边界错误吞掉；但若实测误报集中在 `and`/`or`，可能需要加 N8，那是增量而非推翻。
5. **B1-3 的 N7（`if x\n{` 合法）可能与“一行一条语句”的 N1 产生交互误解**：`if x` 换行 `{` 时，`if` 头部本身没有 NEWLINE 终止，属于“跨行头部”。我认为无歧义，但实现者若在 `if` 后统一“跳到行尾再找 `{`”，会把 `if x` 后的表达式吃掉；这是实现细节，规范要写清“只跳过 NEWLINE，不回退”。
6. **B1-4 的 `f(a)(b)` = `f(a,b)` 可能被裁判判为“不可接受的静默接受”。** 我已给出“若评审坚持则降级为实现建议”的退路，但若它被视为本主张的硬失效条件，B1-4 可能需要改为“分组实参必须与前一实参有空白分隔”（而这会让解析器重新依赖空白，我不建议）。
7. **B1-5 的 `json_value := expr` 可能过宽。** 我论证了终止符保证不越界，但没有实测“payload 里写管道”的可读性；若实测变差，收窄到 `unary_expr` 是一行文法改动，不影响其他四条。
8. **全部五条主张都建立在“先改文档、后写实现”的顺序上。** 仓库现在没有任何实现与门禁（S-001 [L36](file:///Users/samxx/trae-ws/rill-dsl/docs/spec/S-001-call-form.md#L36)），所以本席的“实现量级”是估算；真实行数可能差 2 倍。E4 的数字请按“估算”引用，不要当成已核对的代码事实。



