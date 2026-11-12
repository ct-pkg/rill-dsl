# 10 AST 与位置契约

> 规范版本 `v0.1 rev.1`；状态 `unverified`。依据 [D-020](../../decisions/D-020.md)。本卷是 Phase 1 golden 的冻结依据：节点、字段顺序、序列化与位置口径一经引用，实现不得自行增删或重排。

## 1. 适用范围与冻结面

- 本卷只规定 parser 的输出（AST）、稳定序列化、位置，以及错误发生在哪个阶段；不求值、不涉及工具。
- **冻结面**：§3 的 `sexpr` 形式逐字节比对；§4 的 `sexpr-loc` 用于位置断言。golden 不得对空白、字段顺序、转义做“等价”归一。
- AST 不含注释、空行、NEWLINE、分组括号，也不含 `# dsl-version:`（校验后擦除，见 §6）。

## 2. 节点集合与字段

字段按表中顺序出现在序列化里；`?` 表示可选，缺省时整个字段不输出。

| 节点 | 字段 | 说明 |
| --- | --- | --- |
| `program` | `header?`, `block` | 整个脚本 |
| `header` | `entry*` | 按源码顺序，见 §6 |
| `entry` | `key`, `items*` | `key ∈ allow/deny/emit`；`items` 是 IDENT 或单个 `*` |
| `block` | `stmt*` | `{ ... }`；`program` 的顶层也用 `block` |
| `let` | `name`, `mutable`, `value` | `mutable` 是 `true`/`false` |
| `assign` | `name`, `value` | 无 `mutable` |
| `if` | `cond`, `then`, `else?` | `then`/`else` 是 `block` |
| `for` | `name`, `iterable`, `body` | `body` 是 `block` |
| `into` | `subject`, `body` | `body` 是 `block` |
| `fn` | `name`, `params*`, `body` | `params` 是 IDENT |
| `return` | `value?` | 无值时不输出字段 |
| `emit` | `event`, `payload` | `event` 是 `str` 节点的值 |
| `break` / `continue` | — | 无字段 |
| `exprstmt` | `expr` | 语句位置的表达式 |
| `call` | `callee`, `arg*` | `callee` 是 IDENT；至少 1 个 `arg` |
| `ident` | `name` | |
| `str` | `value` | 已解码的字符串 |
| `num` | `lexeme` | **源文本原样**，不做数值归一 |
| `bool` | `value` | `true`/`false` |
| `null` | — | |
| `dollar` | — | `$` |
| `field` | `object`, `name` | `a.b` |
| `index` | `object`, `index` | `a[i]` |
| `unary` | `op`, `operand` | `op ∈ not/-` |
| `binary` | `op`, `left`, `right` | 算术、比较、`and`/`or` |
| `pipe` | `left`, `right` | `|>`，左结合成树 |
| `fallback` | `left`, `right` | `|?`，左结合成树 |
| `pobj` | `pair*` | emit payload 的对象 |
| `parr` | `value*` | emit payload 的数组 |
| `pair` | `key`, `value` | `key` 是已解码字符串，`value` 是 payload 节点 |
| `pexpr` | `expr` | payload 位是普通表达式时的包装 |

**擦除**：分组 `( ... )` 不产生节点，内层表达式保留自己的 span，不含括号；注释与空行不产生节点；`# dsl-version:` 不产生节点（§6）。

## 3. 稳定 S-expression（`sexpr`）

规则：

1. 节点写成 `(` 节点名 字段… `)`；字段之间 **一个** ASCII 空格；无换行、无尾随空格。
2. 字段按 §2 顺序输出；可选字段缺省时整段省略，不写 `null` 占位。
3. 字符串用 JSON 字符串字面量：`\"`、`\\`、`\n`、`\r`、`\t` 转义；其余 U+0000–U+001F 写 `\u00xx`（小写十六进制）；非 ASCII 原样输出 UTF-8，不转义。
4. `num` 输出源 lexeme（如 `(num 3.14)`），不补零、不改写指数（本文法不接受指数）。
5. 标识符、运算符、header 的 `*` 以裸 token 输出；`true`/`false` 小写。
6. 空列表写作 `(block)`、`(pobj)`、`(parr)`、`(header)`；`null` 值写作 `(null)`。header 的空列表条目写作 `(entry allow)`。
7. `let` 的不可变与可变分别是 `(let x false …)`、`(let x true …)`。

示例：

```
# allow: read, grep
let x = read "a" |> grep "m"
```

```
(program (header (allow read grep)) (block (let x false (pipe (call read (str "a")) (call grep (str "m"))))))
```

## 4. 位置

- 行、列均 1 基；**列按 UTF-8 字节计**（与 [07 §4](07-runtime.md) 的错误列同口径）。Tab 计 1 字节；文件头 BOM 不计入列。
- span 为 `[start, end)`：`start` 是首 token 首字节，`end` 是末 token 之后一字节。
- 节点 span 取法：语句从首 token 到末 token（不含行尾 NEWLINE）；`block` 含 `{` 与 `}`；`call` 从 callee 到末实参；`field`/`index` 从对象起点到后缀末；`program` 从首个非空行到末 token，空脚本或无语句时为 `1:1-1:1`；`header` 从首个 header 行行首到末个 header 行末。
- 分组被擦除，内层 span 不扩到括号；但未闭合括号的诊断位置用开括号（见 §5）。
- 可选字段缺省不占位置；`return` 无值时 span 止于 `return`。
- **`sexpr-loc`**：每个节点名前插入 `@<sl>:<sc>-<el>:<ec>` 加一个空格，例如 `(@1:1-1:20 program …)`。golden 默认比对 `sexpr`；位置用例比对 `sexpr-loc`。

## 5. 错误阶段与位置

| 阶段 | 触发 | `error_kind` | 位置 |
| --- | --- | --- | --- |
| 词法 | 非法字符、未闭合字符串/转义、非法数字、数字后紧跟标识符 | `syntax` | 违规字节；未闭合字符串指向开引号 |
| 解析 | 文法不符（`f()`、比较链、payload 后接后缀等）、未闭合定界符 | `syntax` | 违规 token；未闭合定界符指向**最内层未匹配的开定界符** |
| 加载 | header 语义、名字解析、`arity`、作用域与静态检查 | [07 §3.1](07-runtime.md) 的对应 kind | 相关节点 start |
| 运行 | 求值期失败 | [07 §3.2](07-runtime.md) | 产生失败的调用/表达式 start |

- `syntax` 同时覆盖词法与解析两阶段；诊断行不显示阶段名，调试 JSON 可带 `"stage": "lexer"|"parser"`。
- 解析失败不产出 AST；加载失败发生在 AST 已建成之后，AST 可供调试输出，但不是合法执行输入。
- 多个未闭合定界符时只报栈顶（最后打开）的那一个；不得报文件末尾。
- `no_allow_header`：`# allow:` 存在但为空 → 该行行首（列 1）；完全没有 `# allow:` → 第一条**有效语句**的行首（列 1），空脚本或无语句 → `1:1`。
- `deny_without_allow`：指向第一条 `# deny:` 的行首（列 1）。
- EOF 位置：文件在表达式/语句中间结束、且不是未闭合定界符 → 报**最后一字节之后**：`line` 为末行号；若文件以换行结束，`line` 为末行号 + 1、`col=1`；否则 `col` = 末行 UTF-8 字节数 + 1。空文件 → `1:1`。

## 6. header 的 AST 形态

- `header` 的 `entry*` **保持源码顺序**，不按 key 归并；同一 key 重复 → 加载期 `dup_header`，位置指向第二次出现的行首。
- 列表保持书写顺序，不去重、不排序：`# allow: grep, read` → `(entry allow grep read)`。
- `# allow: *` → `(entry allow *)`；`# allow:` 后为空 → `(entry allow)`（AST 合法，加载期 `no_allow_header`）。
- `# dsl-version: 1` 校验通过后**擦除**，不进入 AST；其他数字 → `version`，位置指数字 token；非数字 → `syntax`。
- 不匹配四种前缀的 `#` 行是注释，不产生 `entry`；`# approval:` 因此不出现、不报错。
- header 解析只做词法与结构：`# allow:` 列表里的名字**不在解析期校验**是否注册；未注册名不报错、不产生诊断，按 [06 §2](06-security.md) 在加载期被忽略。

## 7. 验收锚点

- 解析 golden：`sexpr` 逐字节比对五个示例（[08](08-examples.md)）与 [02 §6](02-grammar.md) 判定表；位置用例用 `sexpr-loc` 覆盖多字节字符、Tab、未闭合定界符。
- 门禁：`尚未落盘`（M2 后 `tools/check.sh m2-parse`）。
