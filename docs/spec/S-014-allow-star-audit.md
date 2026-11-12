# S-014 `# allow: *` 与 deny 优先级

- **状态**：`unverified`
- **决策**：[D-011](../decisions/D-011.md)
- **规范**：[06 §2](dsl/06-security.md)
- **里程碑**：M7

## 1. 输入

| 脚本 | header |
| --- | --- |
| A | `# allow: *` |
| B | `# allow: read, grep` + `# deny: grep` |
| C | `# allow: *` + `# deny: exec` |

## 2. 输出

- A：有效集 = 注册表全集；加载成功，并产出一条审计记录（脚本路径、内容哈希、`policy_generation`、有效工具数、时间戳）。
- B：`grep` 不可调用（`tool_not_allowed`）；`read` 可调用。
- C：`exec` 即使注册也不可调用。
- `# deny:` 优先于 `# allow:`；deny 列表里的名字不必在 allow 中。

## 3. 失败语义

- A 加载成功但没有审计记录 → 验收失败。
- B/C 中 deny 的名字仍可调用 → 验收失败（安全缺陷）。
- 把 `*` 当成“无 header”而不审计 → 验收失败。

## 4. 验收命令与阈值

- **命令**：`尚未落盘`（M7 后 `tools/check.sh m7-security`）。
- **阈值**：3 条逐条通过；审计记录字段 5 项齐全；deny 覆盖 2/2。

## 5. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 三态与审计 | [06 §2](dsl/06-security.md) | 规范正文 |
| 决策 | [D-011](../decisions/D-011.md) | 决策记录 |
