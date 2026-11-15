# 14 `fmt --compress` / `fmt --display`

**演示什么**：同一份脚本的两种表示。`--compress` 去掉 token 间可选空白、把映射长词换回
短词引用；`--display` 补空格、按 `{}` 缩进、把 `` `短词` `` 展开成长词。

**语法要点**

- `fmt` 是 token 级机械转换，不执行、不校验脚本。
- 压缩态保留语句换行（换行是语句边界），只压缩行内空白。
- 展示态展开的是「值类映射」和「动词类映射」；`<r>` → `<read>`、`` `cfg` `` → `'data/one.txt'`。
- 展示态会保留源里紧贴的 token（如 `->$t`、`[to]user`），因为紧贴可能表示相邻拼接；
  所以展示态的空格依赖于源里的空白，不是无条件铺开。

**运行**（在 `examples/tour/` 下）

```console
$ ../../ct/bin/rill fmt --compress 14-fmt.rill
```

**真实输出（压缩态）**

```console
//map{
cfg`data/one.txt
r<read
}
<r>`cfg`->$t
<send>$t[to]user
```

```console
$ ../../ct/bin/rill fmt --display 14-fmt.rill
```

**真实输出（展示态）**

```console
//map{
cfg`data/one.txt
r<read
}
<read> 'data/one.txt' ->$t
<send> $t[to]user
```

两次退出码都是 `0`。压缩态把 `<r> `cfg` ->$t` 收成 `<r>`cfg`->$t`；展示态把动词映射
展开成 `<read>`、值映射展开成 `'data/one.txt'`，并补出 `<read> ` 后面的空格。`//map{}`
块本身在两种形态下都原样保留（长词到行尾，没有可压缩的空白）。

这份脚本本身也能跑：

```console
$ ../../ct/bin/rill run 14-fmt.rill
第一份文件

{"ok":true,"value":"第一份文件\n","error":null,"host_meta":{"stdio":{"channel":"stderr","text":"第一份文件\n"}},"host":{"profile":"shell","principal":{"kind":"os-user","name":"samxx"}}}
```

退出码 `0`——格式化只是换写法，语义不变。
