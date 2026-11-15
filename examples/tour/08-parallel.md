# 08 `parallel` 与 `[results]`

**演示什么**：`parallel { ... }` 的分支各自成段，`[results]` 在全部完成后触发一次，
`$` 是按源序的结果数组；分支的三态（成功 / 未处理失败 / 已处理失败）都能在数组里看到。

**语法要点**

- 块内一行一个 `simple_stmt`；分支可带自己的 `[ok]` / `[error]` / `[into]` 尾随块。
- 分支未处理失败 → 该位置为 `null`，并计入整体失败；分支内 `[error]` 处理且未 break →
  该分支算成功，位置上是处理后的 `$`。
- `[results]` 只允许出现在 `parallel` 块级（`[results]` 写别处是解析期
  `E-PARSE-RESULTS-CONTEXT`）；它永远触发，只管值，不带状态字段。
- 整体失败时程序 `ok=false`、`error` 是默认串，但 `value` 仍保留 `[results]` 的段输出。
- 块后可继续接 `|>`。

**运行**（在 `examples/tour/` 下）

```console
$ ../../ct/bin/rill run 08-parallel.ri
```

**真实输出**

```console
branch-3 已处理
["第一份文件\n", null, "E-HOST-ENV-MISSING: 环境变量 'RILL_TOUR_MISSING_B' 未定义"]
{"ok":false,"value":["第一份文件\n",null,"E-HOST-ENV-MISSING: 环境变量 'RILL_TOUR_MISSING_B' 未定义"],"error":"RILL DSL ERROR","host_meta":{},"host":{"profile":"shell","principal":{"kind":"os-user","name":"samxx"}}}
```

退出码 `1`（有未处理失败）。stderr 第一行来自第 3 个分支的 `[error]` 块，第二行是
`[results]` 里 `<send> $` 的输出。数组三个位置分别是：成功（一段文件内容）、未处理
失败（`null`）、已处理失败（`$` 即错误串）。注意 `[error]` / `[ok]` 块的段输出就是
块的 `$`，块内 `send` 的返回值不会替换它。
