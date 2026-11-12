# S-013 默认拒绝与 header 校验

- **状态**：`unverified`
- **决策**：[D-011](../decisions/D-011.md)
- **规范**：[06 §2](dsl/06-security.md)
- **里程碑**：M7

## 1. 输入

| 脚本 | header |
| --- | --- |
| A | 无 |
| B | `# allow:`（空） |
| C | `# deny: exec`（无 allow） |
| D | `# allow: read, grep` |
| E | `# allow: read` + 调用 `write` |

## 2. 输出

- A/B → `no_allow_header`，错误列出 `Available:` 与 Hint；拒绝加载，任何工具都不执行。
- C → `deny_without_allow`；不得静默变成空集。
- D → 正常加载。
- E → `tool_not_allowed`，列出 `Allowed tools: read` 与 Hint。
- 默认拒绝只改第二层，不改第一层注册表。

## 3. 失败语义

- headerless 脚本被加载成功 → 验收失败（安全缺陷）。
- `# deny:` 单独出现被当成空 allow → 验收失败。
- 错误缺少 `Available:` 或 `Hint:` → 验收失败。

## 4. 验收命令与阈值

- **命令**：`尚未落盘`（M7 后 `tools/check.sh m7-security`）。
- **阈值**：A–E 五条逐条断言 `error_kind` 与错误字段；5/5 通过；0 次 headerless 加载成功。

## 5. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 三态规则 | [06 §2](dsl/06-security.md) | 规范正文 |
| 迁移成本实测 | `.rill`/`.dsl` 计数 0（[D-011](../decisions/D-011.md)） | 决策记录 |
