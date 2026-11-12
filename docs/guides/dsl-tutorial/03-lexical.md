# 03 词法与书写规则

> 状态：`unverified`；依据 `docs/spec/dsl/01-lexical.md`、`02-grammar.md` 与 D-001..D-006。非规范性文档。

## 1. 为什么调用用空格，不用括号

rev.1 只有一个调用形态：

```
call := IDENT arg+
```

`(` `)` 只承担两件事：**表达式分组** 和 **`fn` 的参数表**。它们不是调用语法。

```rill
# allow: read, grep

let text = read "src/main.c"
let hits = grep "TODO" text
```

- `grep "TODO" text` 是一个调用，带两个实参。
- `grep("TODO", text)` **不是**合法写法：逗号不是分组的一部分，会报 `syntax`。
- `read("src/main.c")` 恰好能解析成「一个调用 + 一个分组实参」，但它不是本教程教的形态；只要再加第二个实参就会暴露问题（`grep("TODO", text)` 直接失败）。统一写空格形态。

## 2. 括号只做分组

| 写法 | 解析结果 | 说明 |
| --- | --- | --- |
| `read "a.txt"` | `read("a.txt")` | 空格调用 |
| `read ("a.txt")` | `read("a.txt")` | 分组包住单个原子，等价 |
| `grep pattern text` | `grep(pattern, text)` | 两个实参，不递归 |
| `grep pattern (read "a.txt")` | `grep(pattern, read("a.txt"))` | 嵌套调用必须加括号 |
| `write "f" (a + b)` | `write("f", a + b)` | 表达式实参必须加括号 |
| `f()` | `syntax` | 空括号不是 `expr` |
| `a.b()` | `syntax` | 不支持方法调用 |

**空格应用不递归**：`grep pattern text` 是「两个实参」，不是 `grep(pattern(text))`。要嵌套就加括号。

## 3. NEWLINE 是语句终止符

一行一条语句；语句由换行、`}` 或文件结束终止。以下换行会被抑制，允许跨行：

| 规则 | 允许位置 |
| --- | --- |
| N2 | `(` 或 `[` 内部 |
| N4 | `\|>` 或 `\|?` 之后 |
| N5 | 行首 `\|>` 或 `\|?` 之前 |
| N6 | `}` 与 `else` 之间 |
| N7 | `if` / `for` / `into` / `fn` / `else` 头与 `{` 之间 |
| N8 | emit payload 的 JSON 内部，以及 `emit STRING` 与 payload 之间 |

```rill
# allow: read, write

let a = (1
       + 2)
let b = a
    |> write "out.txt"
if a == 3
{
    write "x.txt" a
}
else {
    write "y.txt" a
}
```

反例（均报 `syntax`）：

```text
let a = 1 let b = 2          # 一行两条语句
let a = 1;                   # 不支持分号
let b = a +                  # 运算符后换行不在允许位置
1
```

空行折叠，不产生空语句；连续的 NEWLINE 不会变成多条语句。

## 4. 注释与 header

- `#` 到行尾是注释；**注释不吃换行**，后面的 `\n` 仍然终止语句。
- 不支持块注释。
- 文件最前面的 `# allow:` / `# deny:` / `# emit:` / `# dsl-version:` 是 **header**，不是注释；header 行内不能再写注释。

```rill
# allow: read
let x = 1 # 这是注释
let y = 2
```

反例：`# allow: read # x` 是语法错误，header 行按整行文本解析，不支持行内注释。

## 5. 数字

- 词法层只接受非负十进制：`0`、`42`、`3.14`。
- 不接受 `1.`、`.5`、`1e9`、`0x10`、`1_000`。
- `-` 是运算符，不是数字的一部分；**不存在带符号的数字字面量**。

```rill
# allow: write

let a = 42
let b = 3.14
let c = -1
let d = a - 1
write "out.txt" (-1)
```

- `let c = -1` 解析为「一元 `-` 作用于 `1`」，是表达式，不是字面量。
- `read -1` 解析为 `(read) - 1`，加载期报「工具名不能作值」；要传负数实参写 `(-1)`，如 `write "out.txt" (-1)`。`read` 的 `path` 需要字符串，传 `-1` 会得到 `constraint`。
- `12abc` 是词法错误，不会被切成 `12` + `abc`。

## 6. 字符串

- 双引号或单引号；转义只支持 `\n` `\t` `\"` `\'` `\\` `\$`。
- 不允许字符串内出现裸换行。

```rill
# allow: write

let s = "line1\nline2"
let q = 'it\'s fine'
let money = "cost: \$5"
write "out.txt" s
```

`"cost: \$5"` 里的 `\$` 是字面美元符，不会触发 `$` 语义。

## 7. 标识符与关键字

- 标识符：`[A-Za-z_][A-Za-z0-9_]*`。
- 关键字不能作工具名、变量名、函数名、字段名或参数名。
- 关键字表：`let` `mut` `if` `else` `for` `in` `into` `fn` `return` `emit` `break` `continue` `and` `or` `not` `true` `false` `null`。
- `par` 是保留字：脚本任何位置出现都报加载期 `not_implemented`，不能当名字用。

## 8. 书写模板

```rill
# allow: read, grep, write
# deny: exec
# emit: analysis_done
# dsl-version: 1

let text = read "src/main.c"
let hits = grep "TODO" text
write "todo.json" hits
```

- header 必须在第一条语句之前；`# dsl-version:` 可选，只接受 `1`。
- 每行一条语句；复杂实参加括号；管道可以换行，但 `|>` 要在行尾或下一行行首。
