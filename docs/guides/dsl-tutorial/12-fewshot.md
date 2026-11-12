# 12 few-shot 片段

> 状态：`unverified`。下面整段可直接放进提示词；示例只按 `v0.1 rev.1` 文法推导过，未经运行。

## 两条硬规则

1. **调用用空格，不用括号**：`read "a.txt"`、`grep "TODO" text`；括号只用于分组和 `fn` 参数表。
2. **每条语句独占一行**：语句由换行终止；一行写两条语句是语法错误。

其余必须遵守的规则：脚本第一行起写 `# allow:`；复杂实参加括号（`write "f" (a + b)`）；`emit` 的事件名先写进 `# emit:`；没有 `while`。

## 示例 1：读一个文件并写出

```rill
# allow: read, write

let text = read "notes.txt"
write "copy.txt" text
```

## 示例 2：管道 + 条件

```rill
# allow: read, grep, write

let hits = read "src/main.c" |> grep "TODO"
if hits.length > 0 {
    write "todo.json" hits
}
```

## 示例 3：`into` + `$` + 自动注入

```rill
# allow: read, json_parse, get, write

read "config.json" |> json_parse into {
    let host = get "host"
    let port = get "port"
    write "server.txt" (host + ":" + port)
}
```

## 示例 4：有界循环 + 事件

```rill
# allow: read, grep
# emit: analysis_done

let lines = read "src/main.c" |> grep "malloc"
let mut count = 0
for line in lines {
    count = count + 1
}
emit "analysis_done" { "file": "src/main.c", "count": count }
```

## 示例 5：函数返回数组 + 调用方判长度

```rill
# allow: read, grep, write

fn scan(path) {
    let text = read path
    return text |> grep "TODO"
}

let hits = scan "src/main.c"
if hits.length > 0 {
    write "todo.json" hits
}
```

## 写完后自检

- 每个调用是不是「名字 + 空格实参」？有没有 `f()`、`f(a, b)`？
- 每条语句是不是独占一行？复杂实参有没有括号？
- `# allow:` 是否覆盖全部调用？`emit` 的事件是否在 `# emit:`？
- 条件是不是 `bool`？数组长度是不是用 `.length`？
- 固定 arity 工具/函数的实参个数不符是加载期 `arity`，不是运行期 `constraint`，也不能用 `|?` 兜底。
- 有没有写 `while`、`par`、对象字面量、递归 `fn`？
