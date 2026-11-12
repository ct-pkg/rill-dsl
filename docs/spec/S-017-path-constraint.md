# S-017 路径约束

- **状态**：`unverified`
- **决策**：[D-014](../decisions/D-014.md)
- **规范**：[06 §5.1](dsl/06-security.md)
- **里程碑**：M8

## 1. 输入

root=`/workspace`。工具 `read` 声明 `path` 约束；依次传入：

```
/workspace/a.txt
/workspace/../../etc/passwd
/workspace/link-to-etc/passwd
/workspace/link-to-sub/a.txt
/workspace-evil/x
/workspace/new.txt          （不存在，父目录存在）
```

## 2. 输出

| 输入 | 结果 |
| --- | --- |
| `/workspace/a.txt` | 允许 |
| `/workspace/../../etc/passwd` | `constraint` |
| symlink → `/etc` | `constraint` |
| symlink → `/workspace/sub` | 允许 |
| `/workspace-evil/x` | `constraint` |
| `/workspace/new.txt` | 允许（父目录解析后仍在界内） |

- 判定使用解析后的绝对路径；界内判定为等于 root 或 `root + "/"` 前缀。
- 判定与打开同源（fd 或逐段 `O_NOFOLLOW`）；handler 不得再解析原始字符串。
- 拒绝时 handler 未执行。

## 3. 失败语义

- 任一应拒路径被允许 → 验收失败（安全缺陷）。
- 应允路径被拒且属于夹具五件套 → 验收失败（误杀）。
- 错误缺少 `Constraint:` 行 → 验收失败。

## 4. 验收命令与阈值

- **命令**：`尚未落盘`（M8 后 `tools/check.sh m8-constraints`；夹具在 `examples/m8-constraints/`）。
- **阈值**：6 条逐条通过；handler 未执行 3/3；符号链接两向各 1 例。

## 5. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 路径规则 | [06 §5.1](dsl/06-security.md) | 规范正文 |
| 决策 | [D-014](../decisions/D-014.md) | 决策记录 |
