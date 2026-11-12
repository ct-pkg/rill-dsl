# 02 最小可运行脚本

> 状态：`unverified`；依据 `docs/spec/dsl/` 与 `docs/spec/tools/`。示例只做过文法推导，未运行。

「可运行」在 rev.1 的含义是：脚本能被加载，且内核注册了脚本调用的工具。没有 parser 之前，本卷第 2 节起只保证「按 EBNF 可推导」。

## 1. 一个工具调用 + 写文件

```rill
# allow: read, write

let text = read "notes.txt"
write "copy.txt" text
```

逐行读法：

| 行 | 作用 |
| --- | --- |
| `# allow: read, write` | header；不写等于默认拒绝，加载失败 |
| `let text = read "notes.txt"` | 空格调用：`read` 是工具名，`"notes.txt"` 是唯一实参 |
| `write "copy.txt" text` | 两个空格实参；第二个是变量引用 |

语句以换行终止。一行写两条语句（`let a = 1 let b = 2`）是语法错误。

`read "notes.txt"`、`read "src/main.c"` 这类相对路径都以 **workspace root** 为基准，不以进程 cwd 为基准；脚本不能声明或改写 root。

## 2. 接管道 + 判断

```rill
# allow: read, grep, write

let hits = read "src/main.c" |> grep "TODO"
if hits.length > 0 {
    write "todo.json" hits
}
```

- `read "src/main.c" |> grep "TODO"` 等于 `grep("TODO", <read 的结果>)`：管道值**追加到显式实参之后**。
- `hits` 是 `json_array`；`hits.length` 是数组内建字段。
- `hits.length > 0` 是 `bool`，满足 `if` 条件必须是 `bool` 的要求。
- 不要写 `if hits != null`：`grep` 无匹配返回 `[]`，`[] != null` 恒为 `true`，条件不起过滤作用。

## 3. 把上一步结果带进块

```rill
# allow: read, json_parse, get, write

read "config.json" |> json_parse into {
    let port = get "port"
    write "port.txt" port
}
```

- `into` 把管道结果绑定为块内只读的 `$`。
- `get` 声明了 `accepts_context`，块内 `get "port"` 少一个实参时会自动补 `$`，等价于 `get "port" $`。
- `write` 不声明 `accepts_context`；要写 `$` 必须显式写 `write "port.txt" $`，或走管道 `$ |> write "port.txt"`。

## 4. 等价写法：下限在哪

同一个「读文件再搜索」有三种正确写法。它们产生同一组工具实参：

```rill
# allow: read, grep

let x = read "a.txt" |> grep "b"
```

```rill
# allow: read, grep

let text = read "a.txt"
let x = grep "b" text
```

```rill
# allow: read, grep

let x = grep "b" (read "a.txt")
```

| 写法 | 依赖的语法糖 | 什么时候用 |
| --- | --- | --- |
| `read "a.txt" \|> grep "b"` | 管道追加 | 数据从一步流到下一步 |
| 先 `let text` 再 `grep "b" text` | 无 | 需要复用 `text` 或分步调试 |
| `grep "b" (read "a.txt")` | 括号分组 | 嵌套调用只出现一次 |

**下限**：显式实参 + 括号分组永远可用；`|>`、`into`、`$` 都是在此基础上减少重复书写的语法糖。拿不准时先写显式形态。

再看 `$` 的两种等价写法（都在 `into` 块内）：

```rill
# allow: read, json_parse, write

read "config.json" |> json_parse into {
    write "out.txt" $
}
```

```rill
# allow: read, json_parse, write

read "config.json" |> json_parse into {
    $ |> write "out.txt"
}
```

前者是「显式 `$` 作第二个实参」；后者是「`$` 作管道值追加到 `write "out.txt"` 之后」。两者最终都是 `write("out.txt", $)`。

## 5. 一个空脚本也是合法程序

```rill
# allow: read
```

`program := header? statement* EOF`，header 之后可以没有语句。`DslResult.value_json` 在没有 `expr_stmt` 时为 `null`。但 header 不能省：没有 `# allow:` 会被加载期拒绝。

## 6. 写脚本前的固定检查

1. 第一行起是否有 `# allow:`，列出的工具是否覆盖全部调用。
2. 每个调用是否是「工具名 + 空格实参」，没有 `f()`、`f(a, b)`。
3. 每条语句是否独占一行；跨行是否只落在括号内或管道续行位置。
4. 复杂实参是否加了括号：`write "f" (a + b)`。
5. 条件是否是 `bool`；数组长度是否用 `.length` 而不是 `!= null`。
