# 05 作用域：into 与 $

> 状态：`unverified`；依据 `docs/spec/dsl/03-semantics.md` §6–§8、D-007、D-017。非规范性文档。

## 1. `into` 做什么

```
into_stmt := expr "into" block
```

求值 `expr`，进入块，把结果绑定为块内只读的 `$`。`into` 是语句，块的值被丢弃（即使块内最后一条是 `expr_stmt`）；块内需要保留的结果请显式 `let` 绑定到变量，不要依赖块值。

`into` 不是表达式。不要写 `let x = read "a" into { ... }`；需要保留结果就在块内 `let`。

```rill
# allow: read, json_parse, get, write

read "config.json" |> json_parse into {
    let port = get "port"
    write "port.txt" port
}
```

- `$` 是整份配置对象。
- `get` 声明 `accepts_context`，`get "port"` 在块内自动补 `$`，等价于 `get "port" $`。
- `write` 不声明 `accepts_context`，所以块内必须显式写 `write "port.txt" $`，或写 `$ |> write "port.txt"`。

## 2. `$` 的规则

| 规则 | 结果 |
| --- | --- |
| `$` 只在 `into` 块内可见 | 块外使用 → 加载期 `dollar_outside` |
| `$` 只读 | `$ = ...` → `immutable_assign` |
| `$` 是环境帧里的词法绑定 | 不是全局变量，不跨块泄漏 |
| `into` 可嵌套 | 内层 `$` 覆盖外层；内层块结束后恢复外层 |
| `expr` 为 `null` | 仍可进入块；`$.x` 返回 `null`，不报错 |

反例：块外引用 `$`，加载期 `dollar_outside`，Hint 提示用 `into { ... }` 绑定。

```text
# allow: read, write
let x = $
```

## 3. 嵌套 `into`：覆盖与恢复

```rill
# allow: read, json_parse, get, write

read "pkg.json" |> json_parse into {
    let name = get "name"
    let deps = get "dependencies"
    deps into {
        let dep_count = deps.length
        write "summary.txt" (name + ":" + dep_count)
    }
    write "outer.txt" $.name
}
```

| 位置 | `$` 指向 | 说明 |
| --- | --- | --- |
| 外层块 | 整份 `pkg.json` 对象 | `get "name"`、`get "dependencies"` 自动补外层 `$` |
| 内层块 | `deps` 数组 | `deps.length`（或 `$.length`）是数组元素个数 |
| 内层块结束后 | 恢复为整份对象 | `$.name` 读回配置的 `name` |

内层块内仍能读外层变量 `name`（闭包只读）。`$` 的覆盖只影响 `$` 这个名字，不影响普通变量。

## 4. `accepts_context`：工具自动拿 `$`

只有三条同时成立，才会把 `$` 作为隐式末参注入：

1. 当前位于 `into` 块内；
2. 被调用工具声明 `accepts_context`（`fn` 永不注入）；
3. 显式实参数 + 管道值个数 `n` 小于该工具的固定位置形参数 `m`。

工具目录中只有 `get` 声明 `accepts_context: true`；`read`、`grep`、`write`、`json_parse` 为 `false`，变长的 `json_build` 也不注入。

```rill
# allow: read, json_parse, get

read "config.json" |> json_parse into {
    let a = get "port"
    let b = get "port" $
    let c = $ |> get "port"
}
```

三种写法最终都是 `get("port", $)`：

| 写法 | 显式 | 管道 | 注入 | 最终实参 |
| --- | --- | --- | --- | --- |
| `get "port"` | 1 | 0 | 是（1<2） | `["port", $]` |
| `get "port" $` | 2 | 0 | 否 | `["port", $]` |
| `$ \|> get "port"` | 1 | 1 | 否 | `["port", $]` |

块外调用 `get "port"` 只有 1 个实参且没有 `$`，个数不符 → **加载期** `arity`。

## 5. 不自动注入的工具怎么写

`write` 是固定 2 参且 `accepts_context: false`。块内三个正确写法：

```rill
# allow: read, json_parse, write

read "config.json" |> json_parse into {
    write "a.txt" $
}
```

```rill
# allow: read, json_parse, write

read "config.json" |> json_parse into {
    $ |> write "a.txt"
}
```

```rill
# allow: read, json_parse, write

read "config.json" |> json_parse into {
    let cfg = $
    write "a.txt" cfg
}
```

反例：`write "a.txt"` 在块内只有 1 个实参，`write` 不注入 → **加载期** `arity`，handler 不执行。

## 6. 字段、索引与 `length`

- `x.k`：对象取键，缺键返回 `null`；数组只支持 `.length`；其他类型返回 `null`。
- `x[i]`：数组 0 基索引，越界返回 `null`；对象用 `x["k"]` 取键。
- `.length` 只挂在数组上；对象、字符串、`null` 取 `.length` 返回 `null`。
- 对 `null` 做字段访问返回 `null`，便于缺省处理。

```rill
# allow: read, json_parse, write

read "config.json" |> json_parse into {
    let host = $.server.host
    let port = $.server.port
    let n = $.items.length
    write "host.txt" host
}
```

如果 `$.server` 缺失，`$.server.host` 返回 `null`；`write` 会把它序列化为 JSON `null`，不会报错。

## 7. `fn` 与 `$`

`fn` 调用永远不接收隐式 `$`。需要在函数里使用上下文，就把值作为显式参数传入：

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

`save port` 只把 `port` 作为普通实参传入；函数体内没有隐式 `$`。
