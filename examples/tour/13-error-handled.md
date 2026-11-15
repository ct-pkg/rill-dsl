# 13 `[error]` 与默认收口的差别

**演示什么**：同样一次 `<env>` 失败，写了 `[error]` 就处理后继续，不写就按默认
`break 'RILL DSL ERROR'` 中断 program。

**语法要点**

- `[error]` 块内 `$` 是错误字符串（`CODE: detail` 形态），块执行完语句算成功、继续往下。
- 没有 `[error]` 的失败不会把错误串交给脚本，而是直接默认 break，`ok=false`。
- `[ok]` / `[error]` 每条语句各最多一次，重复是解析期 `E-PARSE-DUP-OK` / `E-PARSE-DUP-ERROR`。

**运行**（在 `examples/tour/` 下）

```console
$ ../../ct/bin/rill run 13-error-handled.ri
```

**真实输出**

```console
E-HOST-ENV-MISSING: 环境变量 'RILL_TOUR_MISSING' 未定义
{"ok":false,"value":null,"error":"RILL DSL ERROR","host_meta":{"host_error":{"code":"E-HOST-ENV-MISSING"}},"host":{"profile":"shell","principal":{"kind":"os-user","name":"samxx"}}}
```

退出码 `1`。stderr 只有一行：第一条语句的 `[error]` 把错误串 `send` 出来并继续；第二条
同样的失败没有 `[error]`，默认 break 中断 program，所以第三条 `<send>` 没有执行。
payload 记录的是最终那次失败（`host_error.code` 为 `E-HOST-ENV-MISSING`）。
