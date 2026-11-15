# 06 `each`：遍历与结果收集

**演示什么**：`each $x [in] <expr>` 逐项执行循环体；`[ok]` 里的 `$` 是按源序收集的
结果数组，长度等于轮数。

**语法要点**

- 头固定为 `each $变量 [in] <expr>`；`[in]` 是普通介词，宾语是 `expr`。
- 从句是数组 → 逐项遍历；是 `null` → 直接失败、0 轮；是其他单值 → 当成单元素数组跑一次。
- 每轮的结果取该轮最后一条语句的段输出；某轮未处理失败时该轮占 `null`，循环继续。
- each 级 `[ok]`：所有轮都成功才触发，`$` = 结果数组；each 级 `[error]`：存在未处理失败
  时触发，`$` = 第一个失败轮的错误串。
- 循环体内变量按轮隔离；`break` 只中断循环。

**运行**（在 `examples/tour/` 下）

```console
$ ../../ct/bin/rill run 06-each.rill --fakes fakes/each.json
```

**真实输出**

```console
{"ok":true,"value":["A","B","C"],"error":null,"host_meta":{},"host":{"profile":"fakes","principal":{"kind":"test-transport","name":"--fakes"}}}
```

退出码 `0`。`[ok]` 里的 `break $` 把结果数组直接作为程序 `value`，所以能在 payload 里
看到收集结果：三轮各执行一次 `<read>`，结果按源序排成 `["A","B","C"]`。

**为什么要 `--fakes`**：真实 Shell 宿主的 `read` 一次只能读一个文件，没有产生数组的
动词；`search` 属于工具动词，只有在 `--fakes` 的测试传输里才有应答。`--fakes` 是 CLI
的既有能力（`run --fakes <json>`），fakes 文件见 [fakes/each.json](fakes/each.json)；
此时 `host.profile` 变成 `fakes`、`host.principal` 变成 `test-transport`，这是传输层
标记，不是脚本语义。
