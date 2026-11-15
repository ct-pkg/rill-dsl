# 16 `host_meta`：成功与失败都能带元数据

**演示什么**：`host_meta` 是宿主填的旁路信息，和 `value` / `error` 并列；成功时记录
通道、路径、进程等细节，失败时记录 `host_error.code`。

**语法要点**

- `host_meta` 不参与脚本逻辑，脚本读不到它，只有调用方看得到。
- 成功形态举例：`send` → `{"stdio": {...}}`，`write` → `{"fs": {"path": ...}}`，
  `run` → `{"process": {...}}`。
- 失败形态：`{"host_error": {"code": "E-HOST-..."}}`。
- `-> $v` 把上一条语句的值存进变量，后续语句可以用 `$v`。

**运行**（在 `examples/tour/` 下；第一条 `<env>` 读的是命令前置的环境变量）

```console
$ RILL_TOUR_SET=demo ../../ct/bin/rill run 16-host-meta.rill
```

**真实输出**

```console
demo
{"ok":false,"value":null,"error":"RILL DSL ERROR","host_meta":{"host_error":{"code":"E-HOST-ENV-MISSING"}},"host":{"profile":"shell","principal":{"kind":"os-user","name":"samxx"}}}
```

退出码 `1`。前两条语句成功：`<env> RILL_TOUR_SET` 拿到 `demo`，存进 `$v` 再 `send` 出来。
第三条 `<env> RILL_TOUR_MISSING` 没有 `[error]`，按默认收口；`host_meta` 记录失败类别
`E-HOST-ENV-MISSING`。注意 `host_meta` 是**最后一条实际执行的语句**留下的：前面那次
`send` 的 `stdio` 元数据不会留在最终 payload 里。

去掉 `RILL_TOUR_SET=demo` 再跑，第一条语句就会失败（`host_error.code` 仍是
`E-HOST-ENV-MISSING`，stderr 为空），可以对照观察同一份脚本的两种走向。
