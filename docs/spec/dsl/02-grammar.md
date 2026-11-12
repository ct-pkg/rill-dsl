# 02 文法

> 规范版本 `v0.1 rev.1`；状态 `unverified`。本卷对应旧文 §3 与 §7，是唯一权威文法。冲突时以本卷 EBNF 为准。

## 1. 程序结构

```
program       := header? statement* EOF
header        := header_line+
header_line   := allow_line | deny_line | emit_line | version_line
allow_line    := "# allow:" allow_list TERM
allow_list    := "*" | ident_list
deny_line     := "# deny:" ident_list TERM
emit_line     := "# emit:" ident_list TERM
version_line  := "# dsl-version:" NUMBER TERM          # [D-018]
ident_list    := IDENT ("," IDENT)*
TERM          := NEWLINE | &EOF
```

- header 必须位于文件最前（允许空行与注释），出现第一条语句后不得再有 header 行。
- header 行按**整行文本**解析（行首 `#`、键、`:`、逗号列表），不进入表达式词法；行内不支持注释，`# allow: read # x` 是语法错误。
- 每个 header 键最多出现一次；重复 → `E_DUP_HEADER`。
- 缺少 `# allow:` 时有效工具集为空，加载拒绝 `E_NO_ALLOW_HEADER`（见 [06](06-security.md)）[D-011]。
- `# deny:` 单独出现（无 `# allow:`）→ `E_DENY_WITHOUT_ALLOW` [D-011]。
- `# allow: *` 表示“继承注册表级”，必须产出一条审计记录 [D-011]。
- `# dsl-version:` 的文本必须严格为 `1`；其他数字 → `E_VERSION`，Hint：`only '# dsl-version: 1' is supported`；非数字 → `syntax` [D-018]。

## 2. 语句

```
statement     := let_stmt | assign_stmt | if_stmt | for_stmt | into_stmt
               | fn_def | return_stmt | emit_stmt | break_stmt | continue_stmt
               | expr_stmt

let_stmt      := "let" mut? IDENT "=" expr stmt_end
mut           := "mut"
assign_stmt   := IDENT "=" expr stmt_end
if_stmt       := "if" expr block ("else" block)?
for_stmt      := "for" IDENT "in" expr block
into_stmt     := expr "into" block
fn_def        := "fn" IDENT "(" param_list? ")" block
return_stmt   := "return" expr? stmt_end
emit_stmt     := "emit" STRING emit_payload stmt_end
break_stmt    := "break" stmt_end
continue_stmt := "continue" stmt_end
expr_stmt     := expr stmt_end
stmt_end      := NEWLINE | &"}" | &EOF
block         := "{" statement* "}"
param_list    := IDENT ("," IDENT)*
```

- `stmt_end` 是**零宽断言**：不消费 `}`/`EOF`，只表示语句在此结束。
- `if`/`for`/`into`/`fn` 的块 `{` 与语句结束都由 `stmt_end` 与 `block` 表达，不额外接受 `;`。
- `assign_stmt` 与 `expr_stmt` 的前缀都是 `IDENT`；解析用两 token 前瞻：`IDENT` 后紧跟 `=`（不是 `==`）→ 赋值，否则按 `expr` 解析。
- `return` 无表达式时返回 `null`。
- `break`/`continue` 只允许出现在 `for` 块内；位置检查在加载期（见 [03 §5](03-semantics.md)）。

## 3. 表达式

```
expr          := pipe_expr
pipe_expr     := fallback_expr ("|>" fallback_expr)*
fallback_expr := or_expr ("|?" or_expr)*                  # 左结合
or_expr       := and_expr ("or" and_expr)*
and_expr      := cmp_expr ("and" cmp_expr)*
cmp_expr      := add_expr (cmp_op add_expr)?
cmp_op        := "==" | "!=" | "<" | ">" | "<=" | ">="
add_expr      := mul_expr (("+"|"-") mul_expr)*
mul_expr      := unary_expr (("*"|"/"|"%") unary_expr)*
unary_expr    := ("not" | "-") unary_expr | postfix_expr
postfix_expr  := atom suffix*
suffix        := "." IDENT | "[" expr "]"
atom          := call | IDENT | STRING | NUMBER | BOOL | NULL | "$"
               | "(" expr ")"

call          := IDENT arg+
arg           := postfix_atom                             # 不递归 [D-002]
postfix_atom  := plain_atom suffix*
plain_atom    := IDENT | STRING | NUMBER | BOOL | NULL | "$" | "(" expr ")"
```

规则：

1. `|?` **高于** `|>`：`a |> f b |? g c` = `a |> (f b |? g c)`；`read "p" |? read "f" |> parse` = `(read "p" |? read "f") |> parse` [D-007]。
2. `atom` 中的 `call` 要求至少一个实参；`IDENT` 后能开始一个 `arg` 时按调用解析，否则是标识符引用。判定只需 1 token 前瞻。
3. 空格应用**不递归**：`f g "x"` = `f(g, "x")`；要传嵌套调用写 `f (g "x")`；要传表达式写 `f (a + b)` [D-002]。
4. 没有 postfix `()`：`f()` 的 `()` 里缺 `expr` → `E_SYNTAX`；`a.b()` 同理 [D-005]。
5. `f(a)(b)` = `f(a, b)`（两个分组实参）；这是分组的自然结果，不为它另设禁令。
6. `a.b` 是字段访问；`a["b"]` 是索引导航；两者都可跟在调用结果后，但必须分组：`(read "x").y`。
7. 比较运算符不可链式：`a < b < c` → `E_SYNTAX`，提示加括号。
8. 没有逗号表达式；`(a, b)` 不是表达式。
9. `[` `{` `-` `not` 不能作为实参起始：`f "a" [0]` 是对 `f "a"` 的结果索引，不是第二个实参；要传负数/取反表达式必须分组，如 `f (-1)`、`f (not x)`。数组没有字面量（`[` 只在 emit payload 中作数组起始），只能来自工具结果或 `let` 绑定。

## 4. emit payload

```
emit_payload  := json_value
json_value    := json_object | json_array | expr
json_object   := "{" json_members? "}"
json_members  := json_pair ("," json_pair)*
json_pair     := STRING ":" json_value
json_array    := "[" json_values? "]"
json_values   := json_value ("," json_value)*
```

- `{`/`[` 只在 emit payload（含嵌套值）位置作字面量起始；表达式中 `[` 只作索引后缀 [D-006]。
- 键必须是 `STRING` 字面量；值可以是对象、数组或任意 `expr`（如 `"count": n + 1`）。
- 无尾随逗号；重复键 → 加载期 `E_DUP_KEY`；`emit` 与 payload 之间的 `NEWLINE` 忽略（N8）。
- payload 后不得接后缀；`emit "e" {...}.x` 是语法错误。
- 除 emit payload 外，`{ }` 只用于块界定；没有通用对象字面量。

## 5. 完整骨架（可直接抄写）

```
program       := header? statement* EOF
statement     := let_stmt | assign_stmt | if_stmt | for_stmt | into_stmt
               | fn_def | return_stmt | emit_stmt | break_stmt | continue_stmt
               | expr_stmt
expr          := pipe_expr
pipe_expr     := fallback_expr ("|>" fallback_expr)*
fallback_expr := or_expr ("|?" or_expr)*
```

其余产生式见 §1–§4；本卷不重复列出，避免两处漂移。

## 6. 歧义判定表

| 输入 | 解析 | 依据 |
| --- | --- | --- |
| `read path.field` | `read(path.field)` | `arg := postfix_atom` [D-002] |
| `read (path.field)` | 同上 | 分组 |
| `f g "x"` | `f(g, "x")` | 不递归 [D-002] |
| `f (g "x")` | `f(g("x"))` | 分组里的调用 |
| `f 1 - 2` | `f(1) - 2` | 无负数字面量 [D-003] |
| `f -1` | `(f) - 1` → 加载错误 | 非法值位 |
| `f (1 - 2)` | `f(-1)` | 分组 |
| `x = 1` | 赋值语句 | 两 token 前瞻 |
| `x == 1` | 比较表达式 | 最长匹配 |
| `matches.length` | 字段访问 | `suffix` |
| `emit "e" { "k": 1 }` | emit + JSON payload | §4 |
| `emit "e"\n{ "k": 1 }` | 同上 | N8 |
| `emit "e" {}` | 合法空 payload | §4 |

## 7. 验收锚点

- [S-002](../S-002-arguments.md)、[S-004](../S-004-newline.md)、[S-005](../S-005-parens-zero-arg.md)、[S-006](../S-006-emit-payload.md)。
- 解析 golden：§6 判定表逐行 + 五个示例（见 [08](08-examples.md)）。
