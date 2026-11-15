# 03 `[into]` 的书写顺序与 `$`

**演示什么**：一条语句可以叠加多个 `[into]` 尾随块，它们按书写顺序执行，看到的是
同一个 `$`；`[into]` 是副作用作用域，块自己的输出不会传给下一个 `[into]`。

**语法要点**

- `[into]` 是尾随块里的一种，`]` 后直接跟 `{`，数量 0..N。
- 块内 `$` = 进入该块时语句的段输出（这里就是 `<read> data/one.txt` 的全文）。
- 执行顺序固定为：`[into]`（按书写顺序）→ `[ok]` / `[error]` → 段输出 → `|>` 下游。
- 块内新建的变量块外不可见。

**运行**（在 `examples/tour/` 下）

```console
$ ../../ct/bin/rill run 03-into-order.ri
```

**真实输出**

```console
第一份文件

第二份文件

{"ok":true,"value":"第一份文件\n","error":null,"host_meta":{},"host":{"profile":"shell","principal":{"kind":"os-user","name":"samxx"}}}
```

退出码 `0`。stderr 的两行证明两个块按书写顺序执行：第一个块 `send $`（one.txt），
第二个块先读 two.txt 再 `send $`。最终 `value` 仍是 `data/one.txt` 的内容——`[into]`
块的输出被丢弃，语句段输出没有被改写。
