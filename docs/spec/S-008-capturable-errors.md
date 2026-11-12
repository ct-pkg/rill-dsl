# S-008 可捕获错误集与 degraded

- **状态**：`unverified`
- **决策**：[D-007](../decisions/D-007.md)
- **规范**：[04 §2.1](dsl/04-pipeline-errors.md)、[04 §4](dsl/04-pipeline-errors.md)
- **里程碑**：M4

## 1. 输入

| 场景 | 工具返回 |
| --- | --- |
| A | `error_kind=not_found` | 
| B | `error_kind=invalid_input` |
| C | `error_kind=transient` |
| D | `error_kind=denied` |
| E | `error_kind=limit` |
| F | `error_kind=approval_denied` |
| G | 成功，`value_json=null` |

均用于 `read "x" |? read "fallback"`。

## 2. 输出

- A/B/C：执行 `fallback`，`ok=1`，`degraded=1`，值为 fallback 结果。
- D/E/F：**不执行** fallback，`ok=0`，`error_kind` 为 D/E/F 原值。
- G：`null` 是值，左侧成功，不执行 fallback，`degraded=0`。
- 一次执行中只要发生过一次右侧接管，`DslResult.degraded=1`；全部正常为 0。

## 3. 失败语义

- 不可捕获错误被 `|?` 吞掉 → 验收失败（安全缺陷），不是“风格问题”。
- 错误类别未知（工具返回未列出的 `error_kind`）→ 按 `internal` 处理，不可捕获。

## 4. 验收命令与阈值

- **命令**：`尚未落盘`（M4 后 `tools/check.sh m4-pipeline`）。
- **阈值**：7 个场景逐条断言 `ok`、`error_kind`、`degraded`；不可捕获集 0 次被吞；`null` 场景 0 次触发 fallback。

## 5. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 可捕获表 | [04 §2.1](dsl/04-pipeline-errors.md) | 规范正文 |
| 安全理由 | [D-007 §理由](../decisions/D-007.md) | 决策记录 |
