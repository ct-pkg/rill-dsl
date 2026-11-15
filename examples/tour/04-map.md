# 04 `//map{}`：值映射与动词映射

**演示什么**：`//map{}` 在脚本头部定义短词到长词的映射；值类标记（`` ` `` / `'`）
展开成字符串，动词类标记（`<`）展开成动词名。

**语法要点**

- 区块头写 `//map{`，`//` 与 `map`、`map` 与 `{` 之间允许空格；`//map` 后没有 `{` 就只是注释。
- 每行格式是「短词 + 标记符 + 行尾长词」，标记符只允许 `'` / `` ` `` / `<` 三个。
- ``cfg`data/config.txt`` 让 `` `cfg` `` 在解析期变成字符串 `"data/config.txt"`。
- `r<read` 让 `<r>` 等价于 `<read>`；加载期按映射后的动词名校验动词集。
- 同一个 `//map{}` 内短词不能重复（加载期 `E-LOAD-MAP-DUP-SHORT`）。

**运行**（在 `examples/tour/` 下）

```console
$ ../../ct/bin/rill run 04-map.ri
```

**真实输出**

```console
port: 8080

{"ok":true,"value":"port: 8080\n","error":null,"host_meta":{"stdio":{"channel":"stderr","text":"port: 8080\n"}},"host":{"profile":"shell","principal":{"kind":"os-user","name":"samxx"}}}
```

退出码 `0`。`<r>` 被当作 `<read>` 执行，`` `cfg` `` 被当作字符串 `data/config.txt`。
把这一份交给 `fmt --display` 会把映射展开成可读文本，见 [14-fmt](14-fmt.md)。
