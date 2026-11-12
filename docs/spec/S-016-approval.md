# S-016 审批绑定

- **状态**：`unverified`
- **决策**：[D-013](../decisions/D-013.md)
- **规范**：[06 §4](dsl/06-security.md)
- **里程碑**：M7

## 1. 输入

工具 `deploy` 声明 `requires_approval`，调用 `deploy "prod"`；另构造：审批后改参数为 `deploy "staging"`、重放同一审批、等待 30 秒、循环内连续两次 `deploy "prod"`。

## 2. 输出

- 未批准：`ok=0`、`error_kind=approval_required`，handler 未执行。
- 批准 `deploy "prod"` 后执行；审批对象为 `(policy_generation, "deploy", canonical_args_hash, nonce)`。
- 参数变化 → `approval_stale`；重放 → `approval_reused`；两者 handler 均未执行。
- 审批等待不计入 `timeout_ms`；结果含 `approval_wait_ms`。
- 同次执行内 `(deploy, args_hash)` 第二次调用不再弹窗（缓存）。
- DSL 中不存在 `approve` 语句；写了 → `syntax`。`# approval:` 不是 header，按注释处理：不报错、不参与校验、不产生任何审批效果（header 只认 `allow`/`deny`/`emit`/`dsl-version` 四种前缀）。

## 3. 失败语义

- 批准一次后任意参数都可执行 → 验收失败（安全缺陷）。
- 审批等待导致 `timeout` → 验收失败。
- 脚本能捕获 `approval_denied` → 验收失败（审批错误不可捕获）。

## 4. 验收命令与阈值

- **命令**：`尚未落盘`（M7 后 `tools/check.sh m7-security`）。
- **阈值**：6 个场景逐条断言；handler 未执行 4/4；缓存命中 1/1；`approval_wait_ms` 存在。

## 5. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 审批规则 | [06 §4](dsl/06-security.md) | 规范正文 |
| 决策 | [D-013](../decisions/D-013.md) | 决策记录 |
| 主体缺口 | PENDING P-020 | 未决项 |
