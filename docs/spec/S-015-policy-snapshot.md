# S-015 策略快照与强杀

- **状态**：`unverified`
- **决策**：[D-012](../decisions/D-012.md)
- **规范**：[06 §3](dsl/06-security.md)
- **里程碑**：M7

## 1. 输入

构造：脚本 A 正在执行第 2 次工具调用；内核把 allow 从 `{read, write}` 收缩为 `{read}`，`policy_generation` 从 7 升到 8。

## 2. 输出

- 执行中的 A 仍用第 7 代：`write` 继续可用，直到本次执行结束。
- 新加载的脚本 B 用第 8 代：`write` 不再可见。
- 若内核在 A 的下一次工具调用边界强杀：`ok=0`、`error_kind=revoked`，已完成步骤的返回值保留；handler 内部不被打断。
- `DslResult.policy_generation == 7`（A 的代）。
- 加载期集合校验与执行期约束校验使用同一代。
- 脚本内容哈希与加载期不一致 → `script_changed`。
- 策略扩张未审批 → `policy_expansion_unapproved`；收缩只写审计。

## 3. 失败语义

- A 执行中途看到第 8 代 allow → 验收失败。
- 强杀发生在 handler 内部 → 验收失败。
- 同一执行混用两代约束 → 验收失败。

## 4. 验收命令与阈值

- **命令**：`尚未落盘`（M7 后 `tools/check.sh m7-security`）。
- **阈值**：跨代 2 例、强杀 1 例、代回显 1 例、哈希 1 例、扩张/收缩各 1 例全部通过；0 次混代。

## 5. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 快照规则 | [06 §3](dsl/06-security.md) | 规范正文 |
| 实时查的两类缺陷 | [D-012 §理由](../decisions/D-012.md) | 决策记录 |
