# 12 运行期失败：管道中断

**演示什么**：管道首段失败且没有 `[error]` 时，管道中断、下游不执行；程序以默认错误串
收口，退出码 1，失败原因留在 `host_meta.host_error`。

**语法要点**

- 段失败 + 无 `[error]` → 隐式 `break 'RILL DSL ERROR'`，只中断当前场域。
- 顶层语句的失败会中断整个 program，后面的语句都不执行。
- 宿主错误码放在 `host_meta.host_error.code`；失败时 `value` 为 `null`。
- 退出码约定：`ok=true` → 0，未处理失败 → 1，诊断（词法/解析/加载/宿主能力拒绝）→ 2。

**运行**（在 `examples/tour/` 下）

```console
$ ../../ct/bin/rill run 12-error-run.ri
```

**真实输出**

```console
{"ok":false,"value":null,"error":"RILL DSL ERROR","host_meta":{"host_error":{"code":"E-HOST-FS-READ"}},"host":{"profile":"shell","principal":{"kind":"os-user","name":"samxx"}}}
```

退出码 `1`。stderr 是空的：`<read> data/missing.txt` 就失败了，`<send> '下游不执行'`
根本没有运行。`host_meta` 里的 `E-HOST-FS-READ` 是宿主给的细分类别，`error` 字段是 DSL
层的默认串。
