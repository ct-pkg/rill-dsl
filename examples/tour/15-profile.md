# 15 能力清单：`--host-profile` 决定能不能写

**演示什么**：脚本能调用什么，由宿主的 Shell profile 决定；未声明的能力是 `run` 阶段
诊断（退出码 2），不是 `ok=false`。

**语法要点**

- profile 是普通 JSON，`schema` 固定 `rill.shell-profile/0`，`allow` 下四个槽位：
  `process` / `fs` / `env` / `stdio`。
- 内置默认（不传 `--host-profile`）是只读：`fs.read`、`env.get`、`stdio.write`。
- `<write>` 需要 `allow.fs` 里有 `write`；被拒绝时不写文件，直接出诊断。
- 成功写盘会回填 `host_meta.fs.path`。

**运行**（在 `examples/tour/` 下，先看只读 profile）

```console
$ ../../ct/bin/rill_ct run 15-profile.rill --host-profile profiles/min.json
```

**真实输出（min：拒绝写）**

```console
{"error":{"stage":"run","code":"E-HOST-CAPABILITY-DENIED","line":0,"col":0,"message":"E-HOST-CAPABILITY-DENIED: Shell profile 'tour-min' 未声明能力 fs.write；在 --host-profile 的 allow.fs 中加入 'write'"}}
```

退出码 `2`，`out/copy.txt` 没有产生（目录里只有 `.gitkeep`）。

```console
$ ../../ct/bin/rill_ct run 15-profile.rill --host-profile profiles/full.json
```

**真实输出（full：允许写）**

```console
{"ok":true,"value":"out/copy.txt","error":null,"host_meta":{"fs":{"path":"out/copy.txt"}},"host":{"profile":"shell","principal":{"kind":"os-user","name":"samxx"}}}
```

退出码 `0`，`out/copy.txt` 的内容与 `data/one.txt` 相同（`第一份文件` 加一个换行）。
`out/` 已在 [.gitignore](.gitignore) 里忽略，跑完不会污染工作树。
