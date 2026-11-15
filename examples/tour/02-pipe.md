# 02 管道 `|>`：段间只传 value

**演示什么**：`|>` 把上一段的段输出作为下一段的 `$`（self）；下游只拿到值，
拿不到上一段的 `ok` 状态。

**语法要点**

- 管道写作 `|>`（不是 `|`；单独的 `|` 是词法错误 `E-LEX-PIPE`）。
- 段间传的是 `value`：`<read>` 的段输出是文件全文，`<send> $` 里的 `$` 就是它。
- 每段各自持有自己的尾随块（`[ok]` / `[error]` / `[into]`），互不影响。
- 折行时 `|>` 留在前一段行尾，例如：

```rill
<read> data/greeting.txt |>
<send> $ [to] user
```

**运行**（在 `examples/tour/` 下）

```console
$ ../../ct/bin/rill run 02-pipe.ri
```

**真实输出**

```console
hello from a file

{"ok":true,"value":"hello from a file\n","error":null,"host_meta":{"stdio":{"channel":"stderr","text":"hello from a file\n"}},"host":{"profile":"shell","principal":{"kind":"os-user","name":"samxx"}}}
```

退出码 `0`。文件本身带一个换行，所以 stderr 上是文本加一个空行；`value` 里的
`\n` 就是那个换行。`host_meta` 来自末段（`<send>`），不是首段。

管道中某段失败会中断管道、下游不执行，见 [12-error-run](12-error-run.md)。
