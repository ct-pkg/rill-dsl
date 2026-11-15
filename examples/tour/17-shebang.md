# 17 · shebang：让 `.rill` 直接执行

**演示什么**：首行 `#!/usr/bin/env rill` 不被当成语法错误，`chmod +x` 后可以
`./17-shebang.rill` 直接跑。

**需要知道的语法**：动词 + `|>` 管道 + `$` 取段值。shebang 本身不是语言语法，
只是首行注释；解释器由 PATH 上的 `rill` 提供（`bash ct/build.sh` 会把它链到
`~/.local/bin/rill`）。

脚本（本目录，已 `chmod +x`）：

```rill
#!/usr/bin/env rill
<read> data/one.txt |> <send> $ [to] user
```

```console
$ ./17-shebang.rill
第一份文件

{"ok":true,"value":"第一份文件\n","error":null,"host_meta":{"stdio":{"channel":"stderr","text":"第一份文件\n"}},"host":{"profile":"shell","principal":{"kind":"os-user","name":"samxx"}}}
$ echo $?
0
```

也可以不靠 shebang，显式调入口：`../../ct/bin/rill run 17-shebang.rill`，结果相同。

## 规则（实测）

- **只认文件首行首列**的 `#!`。第 2 行再写 `#!/usr/bin/env rill` 会按普通源码解析，
  报 `E-PARSE-UNEXPECTED`（`line: 2, col: 1`），退出码 2。
- `tokenize` 里 shebang 被当注释吃掉，第一个 token 是首行的 `NEWLINE`
  （`line: 1, col: 20`），所以行号列号不受影响。
- `fmt` **保留** shebang 原样，压缩态与展示态都一样；格式化后的输出仍可直接执行。

```console
$ ../../ct/bin/rill fmt --compress 17-shebang.rill
#!/usr/bin/env rill
<read>data/one.txt|><send>$[to]user
$ ../../ct/bin/rill fmt --display 17-shebang.rill
#!/usr/bin/env rill
<read> data/one.txt |> <send> $ [to] user
```

想自己验证：`cp 17-shebang.rill /tmp/x.rill && chmod +x /tmp/x.rill`，再在
`examples/tour/` 下执行 `/tmp/x.rill`（`data/one.txt` 是相对当前目录的）。
