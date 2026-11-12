# S-019 emit 上限、双通道与重复键

- **状态**：`unverified`
- **决策**：[D-014](../decisions/D-014.md)、[D-008](../decisions/D-008.md)
- **规范**：[05 §2](dsl/05-data-metadata.md)、[06 §5.4](dsl/06-security.md)
- **里程碑**：M6、M8

## 1. 输入

- `max_emit_bytes=1024`，payload 为 2000 字节。
- `max_payload_depth=4`，payload 嵌套 5 层。
- 工具声明 `args_json` 路径约束，但同一路径由隐式 `$` 传入（`ctx_json`）。
- 工具 schema 未给 `$` 参数名或约束。
- args JSON 含重复键 `{"path":"/workspace/a","path":"/etc/passwd"}`。
- 事件标 `external_egress`，订阅方为外部 webhook；另一事件未标。

## 2. 输出

- 超字节/深度：`ok=0`、`error_kind=limit`，位置指向 emit 语句；不得静默丢弃。
- 隐式 `$` 也必须过约束；未给名字/约束 → `unconstrained_arg`。
- 协议重复键 → `dup_key_json`，且约束与 handler 看到同一份规范化结果（不得一份取第一、一份取最后）。
- 未标 `external_egress` 的事件不投递给外部订阅方；进程内订阅方不受影响。

## 3. 失败语义

- 超限被静默丢弃 → 验收失败。
- `ctx_json` 绕过约束 → 验收失败（安全缺陷）。
- 重复键导致校验对象 ≠ 执行对象 → 验收失败。

## 4. 验收命令与阈值

- **命令**：`尚未落盘`（M6/M8 后 `tools/check.sh m6-events`、`m8-constraints`）。
- **阈值**：6 条逐条通过；静默丢弃 0 次；双通道覆盖 2/2；重复键 1/1。

## 5. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| emit 上限 | [05 §2](dsl/05-data-metadata.md) | 规范正文 |
| 双通道 | [06 §5.4](dsl/06-security.md) | 规范正文 |
| 决策 | [D-014](../decisions/D-014.md) | 决策记录 |
