# 07 函数

> 状态：`unverified`；依据 `docs/spec/dsl/03-semantics.md` §2、§5 与 D-005、D-009。非规范性文档。

## 1. 定义与调用

```
fn name(p1, p2) { ... }
```

- 调用仍用空格：`scan "a.c" "TODO"`，不是 `scan("a.c", "TODO")`。
- 零参函数写 `fn name() { ... }`，调用写裸名 `name`。
- 实参个数必须等于形参个数；否则加载期 `arity`。固定 arity 工具同此规则：个数由 `params_schema` 长度与管道/`$` 注入规则静态可算。
- 函数名不得与已注册工具同名；否则加载期 `shadow_tool`。
- 同一脚本内不得重名；否则 `dup_decl`。

```rill
# allow: read, grep, write

fn scan(path, pattern) {
    let text = read path
    return text |> grep pattern
}

let todos = scan "src/main.c" "TODO"
if todos.length > 0 {
    write "todo.json" todos
}
```

`scan "src/main.c" "TODO"` 按位置绑定：`path = "src/main.c"`、`pattern = "TODO"`。`text |> grep pattern` = `grep(pattern, text)`。

函数返回搜索类结果时，直接返回 `grep` 的数组：无匹配是 `[]`，不是 `null`；调用方用 `.length > 0` 判断。不要写「有结果返回数组、无结果返回 `null`」，否则下游 `a + b` 会变成 `null + json_array`，运行时 `type`。

## 2. 参数是局部不可变值拷贝

- 参数只在函数体内可见；函数外引用 → `undefined_name`。
- 参数不可赋值；`p = 1` → `immutable_assign`。
- 对象/数组参数按值拷贝，函数内修改副本不影响调用方。
- 要改参数，先 `let mut v = p`。

```rill
# allow: write

fn bump(n) {
    let mut v = n
    v = v + 1
    return v
}

let x = bump 1
write "x.txt" x
```

## 3. 只读捕获外层

函数体可以读取外层绑定，但不能赋值给外层绑定：

```rill
# allow: read, write

let path = "notes.txt"

fn load() {
    return read path
}

let text = load
write "copy.txt" text
```

- `load` 读取外层 `path`，合法。
- 函数体内 `path = "other.txt"` → `immutable_assign`（闭包捕获变量不可赋值）。
- `let text = load` 中裸名 `load` 解析为零参函数调用。

## 4. 没有递归

加载期构建调用图；出现环（自调用或互调用）→ `recursion`，脚本不执行。

反例：

```text
fn loop_forever() {
    return loop_forever
}
```

`loop_forever` 在函数体内被解析为零参自调用，调用图成环，加载失败。

需要重复逻辑时用 `for`，不要写成递归。

## 5. 返回值

- `return expr` 返回该值；`return` 不带表达式返回 `null`。
- 执行到函数体末尾没有 `return`，返回 `null`。
- `return` 出现在 `fn` 外 → 加载期 `return_outside_fn`。

```rill
# allow: write

fn classify(n) {
    if n > 0 {
        return "positive"
    }
    return "non-positive"
}

write "class.txt" (classify 1)
```

`classify 1` 是调用表达式，作为 `write` 的第二个实参要加括号。

## 6. 函数与管道

管道值对 `fn` 按普通追加实参处理，不注入 `$`；形参个数必须匹配。

```rill
# allow: read, grep

fn matches(pattern, text) {
    return text |> grep pattern
}

let hits = read "src/main.c" |> matches "TODO"
```

解析与求值：

```
read "src/main.c" |> matches "TODO"
= matches("TODO", read("src/main.c"))
```

`matches` 的 `pattern = "TODO"`、`text = read 的结果`，正好 2 个实参。若写成 `|> matches`（没有显式 `"TODO"`），管道只补 1 个实参，`arity` 失败。

## 7. `fn` 不接收隐式 `$`

`$` 注入只发生在「`into` 块内 + 工具声明 `accepts_context` + 参数位不足」三个条件同时成立时。`fn` 永不满足第二条。

```rill
# allow: read, json_parse, get, write

fn save(port) {
    write "port.txt" port
}

read "config.json" |> json_parse into {
    let port = get "port"
    save port
}
```

函数里要用上下文，就把 `$` 或从 `$` 取出的值作为显式实参传入。

## 8. 错误速查

| 场景 | `error_kind` |
| --- | --- |
| `fn` 或固定 arity 工具的实参个数不符 | `arity`（加载期） |
| 函数名与工具同名 | `shadow_tool` |
| 同一脚本重名函数 | `dup_decl` |
| 调用图有环 | `recursion` |
| `return` 在函数外 | `return_outside_fn` |
| 给参数/捕获变量赋值 | `immutable_assign` |
| 调用不存在的工具或函数名 | `unknown_tool`（Hint 同时提示工具名与函数名） |
