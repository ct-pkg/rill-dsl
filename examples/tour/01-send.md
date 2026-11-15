# 01 最小动词调用：`<send>`

**演示什么**：RILL 的最小单位是一条「动词 + 宾语 + 介宾」的句子；执行结果以 JSON
信封写到 stdout，`<send>` 的文本落到 stderr，元数据在 `host_meta` 里。

**语法要点**

- 动词写成 `<send>`，宾语是单引号纯字面量 `'hello, rill'`（引号内不转义）。
- `[to] user` 是介宾短语：介词放方括号，后面跟宾语。
- 一条语句只有 `ok` / `value` / `error` 三个结果位；`host_meta` 由宿主填写。
- 退出码：`ok=true` 为 0。

**运行**（在 `examples/tour/` 下）

```console
$ ../../ct/bin/rill_ct run 01-send.rill
```

**真实输出**

```console
hello, rill
{"ok":true,"value":"hello, rill","error":null,"host_meta":{"stdio":{"channel":"stderr","text":"hello, rill"}},"host":{"profile":"shell","principal":{"kind":"os-user","name":"samxx"}}}
```

退出码 `0`。第一行是 `<send>` 写到 stderr 的文本；第二行是 stdout 上的结果信封。
`host_meta.stdio` 说明这次 `send` 走的是 stderr 通道，`text` 是实际写出的字符串。
`host.principal.name` 是本机 OS 用户名，换机器会变；其余字段跨机器一致。
