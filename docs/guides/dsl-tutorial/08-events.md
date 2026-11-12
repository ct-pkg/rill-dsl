# 08 事件

> 状态：`unverified`；依据 `docs/spec/dsl/05-data-metadata.md` §2 与 D-006、D-014。非规范性文档。

## 1. 先声明，再发布

`emit` 的事件名必须出现在 header 的 `# emit:` 列表中：

```rill
# allow: read, grep
# emit: analysis_done

let lines = read "src/main.c" |> grep "malloc"
emit "analysis_done" { "file": "src/main.c", "count": lines.length }
```

- 未在 `# emit:` 声明 → 加载期 `event_not_declared`。
- `# emit:` 可以列多个名字：`# emit: analysis_done, scan_failed`。
- `emit` 的第一个参数必须是字符串字面量；不能写变量名代替事件名。

## 2. payload 语法

```
emit_payload  := json_value
json_value    := json_object | json_array | expr
json_object   := "{" json_members? "}"
json_pair     := STRING ":" json_value
json_array    := "[" json_values? "]"
```

- 键必须是字符串字面量；值可以是对象、数组或任意 `expr`。
- 无尾随逗号；重复键 → 加载期 `dup_key`；非字符串键 → `syntax`。
- payload 后不得接后缀：`emit "e" {...}.x` 是语法错误。
- `{` / `[` 只在 emit payload 位置作字面量起始；其他位置的 `{` 是块，`[` 是索引。

多行 payload 合法，JSON 内部的换行被抑制：

```rill
# allow: read, grep
# emit: analysis_done

let lines = read "src/main.c" |> grep "malloc"
emit "analysis_done" {
    "file": "src/main.c",
    "count": lines.length,
    "tags": ["memory", "review"]
}
```

空 payload 也合法：

```rill
# allow: read
# emit: ping

emit "ping" {}
```

`emit "ping"` 与 `{}` 之间的换行也被抑制，但本教程统一写在同一行。

## 3. fire-and-forget

- `emit` 把 payload 深拷贝后交给事件总线，**不等待、不阻塞、不关心订阅方**。
- `emit` 没有返回值，也不能当表达式用：`let ok = emit ...` 是语法错误。
- 无订阅方 → 丢弃并记日志，脚本不受影响；队列满 → 丢弃并记日志。
- 订阅方的失败不会回灌到发布方。
- 事件发布不是工具调用，不参与 `# allow:` / `# deny:`，也不计入 `max_tool_calls`；但计入 `max_emit_count`。

## 4. 上限

| 限制 | 默认 | 超限结果 |
| --- | --- | --- |
| `max_emit_count` | 100 | `ok=0`、`error_kind=limit` |
| `max_emit_bytes` | 65536 | 单条 payload 序列化超限 → `ok=0`、`error_kind=limit` |
| `max_payload_depth` | 8 | 任何 JSON payload（工具结果 + emit）嵌套超限 → `ok=0`、`error_kind=limit` |

超限是**脚本可见的错误**，不得静默丢弃；失败位置指向 emit 语句。

不要写「发出去就算成功」的假设：`emit` 成功只代表已交给总线，不代表订阅方处理成功。

## 5. 不要写通用对象字面量

rev.1 没有通用对象字面量。以下写法是语法错误：

```text
let cfg = { "host": "localhost" }        # 对象字面量只在 emit payload 里合法
let cfg = { "host": "localhost" }.host   # payload 后也不能接后缀
```

需要对象时，用 emit payload 发布，或使用工具返回的对象；脚本内没有构造任意对象的语法。

## 6. `external_egress` 不是脚本 header

事件能否投递给外部 webhook，由内核的事件注册属性 `external_egress` 决定，不是脚本 header。脚本不能自行把事件提升为可外发；未标记的事件只能进进程内订阅方。
