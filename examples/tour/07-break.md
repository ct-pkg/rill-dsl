# 07 `break`：带值收口

**演示什么**：`break <value>` 中断当前场域，值成为该场域的结果；在顶层就中断整个
program，后面的语句不再执行。

**语法要点**

- `break` 后可跟 `value`（字符串 / 数字 / 裸词 / `$变量` / `.字段`），不能直接跟动词调用。
- 裸词按字符串处理（`break done` 等于 `break 'done'`）。
- `break <值> -> $变量` 可把值交给外层变量捕捉。
- 场域由所在区块决定：块内中断块，管道内中断管道，顶层中断整个 program。
- 未写 `[error]` 的失败等价于隐式 `break 'RILL DSL ERROR'`。

**运行**（在 `examples/tour/` 下）

```console
$ ../../ct/bin/rill run 07-break.ri
```

**真实输出**

```console
读取失败，用 break 收口
{"ok":true,"value":"fallback","error":null,"host_meta":{},"host":{"profile":"shell","principal":{"kind":"os-user","name":"samxx"}}}
```

退出码 `0`。`<read> data/missing.txt` 失败进入 `[error]` 块，先 `send` 再 `break
'fallback'`；break 中断 program，payload 的 `value` 就是 `"fallback"`，`ok` 为 `true`
（`break` 是正常收口，不是失败）。最后一条 `<send>` 没有执行——stderr 只出现一行。
