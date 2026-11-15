# 11 解析错误：介词表外的 `[frobnicate]`

**演示什么**：方括号里的介词必须在 §4.5 的表内；表外名称是解析期错误
`E-PARSE-UNKNOWN-PREP`，不是运行期失败。

**语法要点**

- 通用介词只允许 `to` / `with` / `from` / `in` / `on` / `into` / `ok` / `error`。
- `[results]` 不在通用介词表里，只允许出现在 `parallel` 块级。
- 解析错误同上：`{"error": {...}}` + 退出码 2，不执行任何语句。

**运行**（在 `examples/tour/` 下）

```console
$ ../../ct/bin/rill_ct run 11-error-parse.rill
```

**真实输出**

```console
{"error":{"stage":"parse","code":"E-PARSE-UNKNOWN-PREP","line":1,"col":22,"message":"未知介词 [frobnicate]；§4.5 只接受 to/with/from/in/on/into/ok/error"}}
```

退出码 `2`。第 22 列是 `frobnicate` 在源码里的起始列。提示里直接列出合法介词，
方便照着改。
