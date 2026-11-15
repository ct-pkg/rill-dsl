# 10 词法错误：未闭合的引号

**演示什么**：词法阶段的错误不产生 `ok/value` 信封，而是 `{"error": {...}}` 诊断，
带 `stage` / `code` / `line` / `col` / `message`，退出码 2。

**语法要点**

- 词法错误码形如 `E-LEX-*`；这里双引号没闭合是 `E-LEX-QUOTE`。
- 行列号定位到出错的字符（列从 1 开始）。
- 诊断阶段固定为最早失败的阶段：`tokenize` → `parse` → `load` → `run`。

**运行**（在 `examples/tour/` 下）

```console
$ ../../ct/bin/rill run 10-error-lex.rill
```

**真实输出**

```console
{"error":{"stage":"tokenize","code":"E-LEX-QUOTE","line":1,"col":8,"message":"字符串未闭合：行尾前缺少结束引号"}}
```

退出码 `2`。第 8 列是双引号的位置；因为没有 AST，也就不存在 `ok` 字段。
`tokenize` 子命令会在同一处报同一个错误。
