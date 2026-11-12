# 11 常见错误清单

> 状态：`unverified`；依据 `docs/spec/dsl/` 与 `docs/spec/tools/`。每条给「错误写法 / 为什么错 / 正确写法 / 判据」。

## 1. 用括号调用

**错误写法**

```text
let hits = grep("TODO", text)
let x = read()
```

**为什么错**：rev.1 只有 `IDENT arg+` 一种调用形态，`(` `)` 只分组。逗号不是分组的一部分；空括号不是 `expr`。

**正确写法**

```rill
# allow: read, grep

let text = read "src/main.c"
let hits = grep "TODO" text
```

**判据**：`grep("TODO", text)` → `syntax`；`read()` → `syntax`。`read("a.txt")` 虽能解析成一个分组实参，但不是本教程形态，加第二个实参就会失败。

## 2. 把 `-1` 当成带符号字面量

**错误写法**

```text
let x = read -1
write "out.txt" a -1
```

**为什么错**：`NUMBER` 不带符号，`-` 是运算符。`read -1` 解析为 `(read) - 1`；`write "out.txt" a -1` 解析为 `(write "out.txt" a) - 1`。

**正确写法**

```rill
# allow: write

write "out.txt" (-1)
```

**判据**：`read -1` 加载期报「工具名不能作值」，Hint 提示 `read (-1)`；`write "out.txt" a -1` 会先执行写，再算 `null - 1`，随后报运行时 `type`。

## 3. 语句不换行，写成一串

**错误写法**

```text
let a = 1 let b = 2
```

**为什么错**：`NEWLINE` 是语句终止符；一行只能有一条语句，空行折叠但不产生空语句。

**正确写法**

```rill
# allow: read

let a = 1
let b = 2
```

**判据**：第一条写法 → `syntax`；正确写法正常加载。

## 4. `write "f" a + b` 不加括号

**错误写法**

```text
write "out.txt" a + b
```

**为什么错**：实参不递归，表达式按优先级继续解析。它等于 `(write "out.txt" a) + b`：先把 `a` 写进文件，再把返回值 `null` 与 `b` 相加。

**正确写法**

```rill
# allow: write

let a = 1
let b = 2
write "out.txt" (a + b)
```

**判据**：不加括号时解析树是 `(write "out.txt" a) + b`，副作用已发生；`null + 1` → 运行时 `type`（`null + 字符串` 则会拼出 `null...`，同样不是两个实参）。

## 5. `$` 用在 `into` 外面

**错误写法**

```text
let x = $
```

**为什么错**：`$` 只在 `into` 块内绑定，块外引用是加载错误。

**正确写法**

```rill
# allow: read, json_parse, get, write

read "config.json" |> json_parse into {
    let port = get "port"
    write "port.txt" port
}
```

**判据**：块外 `$` → `dollar_outside`，Hint 提示用 `into { ... }`；任何工具都不执行。

## 6. `emit` 没在 header 声明

**错误写法**

```text
emit "analysis_done" {}
```

**为什么错**：事件名必须先在 `# emit:` 列出；未声明 → 加载期拒绝。

**正确写法**

```rill
# allow: read
# emit: analysis_done

emit "analysis_done" {}
```

**判据**：未声明 → `event_not_declared`；正确写法加载成功。`emit` 的第一个参数必须是字符串字面量。

## 7. 忘了 `# allow:`

**错误写法**

```text
let text = read "notes.txt"
```

**为什么错**：默认拒绝；没有 `# allow:` 时有效工具集为空，加载拒绝。

**正确写法**

```rill
# allow: read

let text = read "notes.txt"
```

**判据**：无 header → `no_allow_header`，错误含 `Available:` 与 `Hint:`；只写 `# deny:` → `deny_without_allow`。

## 8. 把 `|?` 当 try/catch 包整段

**错误写法**

```text
let cfg = (read "a.json" |> json_parse) |? null
```

**为什么错**：`|?` 是调用级降级，左侧必须是单个 call；分组管道不是调用节点。

**正确写法**

```rill
# allow: read, json_parse

fn load_config() {
    return read "a.json" |> json_parse
}

let cfg = load_config |? null
```

**判据**：错误写法 → 加载期 `fallback_lhs`；正确写法在 `read` 或 `json_parse` 可捕获失败时采用 `null`，并置 `degraded=1`。没有块级恢复，失败后不会继续执行同块下一条语句。

## 9. 在 `while` 里等

**错误写法**

```text
while true {
    let x = read "status.txt"
}
```

**为什么错**：rev.1 没有 `while`。`while` 不是关键字，`while true { ... }` 会被当作调用 `while(true)` 后遇到块，报 `syntax`。

**正确写法**

```rill
# allow: read, grep

let lines = read "log.txt" |> grep "retry"
for line in lines {
    if line == "done" {
        break
    }
}
```

**判据**：`while` → `syntax`；等待/轮询应由工具的 `timeout`/`interval` 参数或内核重试承担，脚本内用有界 `for`。

## 10. 把工具名当变量名

**错误写法**

```text
let read = 1
fn grep(x) { return x }
```

**为什么错**：局部绑定、参数、`fn` 名不得遮蔽已注册工具名；冲突在加载期报，运行期没有优先级问题。

**正确写法**

```rill
# allow: read, grep

let text = read "notes.txt"
let hits = grep "TODO" text
```

**判据**：`let read = 1`、`fn grep(x) { ... }` → `shadow_tool`；改名后正常。

## 11. 在普通表达式里写对象字面量

**错误写法**

```text
let cfg = { "host": "localhost" }
```

**为什么错**：`{` 只在 emit payload 位置作对象字面量起始；其他位置的 `{` 是块。rev.1 没有通用对象字面量。

**正确写法**

```rill
# allow: json_parse

let cfg = json_parse "{\"host\": \"localhost\"}"
```

**判据**：对象字面量 → `syntax`；`json_parse` 返回 `json_object`。也可以使用工具返回的对象；`json_build` 是否注册由内核决定。

## 12. 写递归 `fn`

**错误写法**

```text
fn loop_forever() {
    return loop_forever
}
```

**为什么错**：加载期构建调用图，出现环（含自调用、互调用）→ `recursion`。rev.1 不支持递归。

**正确写法**

```rill
# allow: read, grep, write

let lines = read "log.txt" |> grep "error"
for line in lines {
    write "last.txt" line
}
```

**判据**：自调用 → `recursion`，脚本不执行；重复逻辑用 `for`。

## 13. 用 `!= null` 判断有没有匹配

**错误写法**

```text
let matches = read "src/main.c" |> grep "malloc"
if matches != null {
    write "report.txt" matches
}
```

**为什么错**：`grep` 无匹配返回空数组 `[]`，不是 `null`；`[] != null` 恒为 `true`，空结果也会进入分支。

**正确写法**

```rill
# allow: read, grep, write

let matches = read "src/main.c" |> grep "malloc"
if matches.length > 0 {
    write "report.txt" matches
}
```

**判据**：错误写法 `ok=1` 但条件恒真；`matches.length` 对数组返回元素个数，`> 0` 才是「有匹配」。`null` 表示缺键/缺失值，不表示空集合。
