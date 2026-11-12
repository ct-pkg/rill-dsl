# S-009 截断元数据

- **状态**：`unverified`
- **决策**：[D-008](../decisions/D-008.md)
- **规范**：[05 §1](dsl/05-data-metadata.md)
- **里程碑**：M6

## 1. 输入

| 场景 | 工具返回 |
| --- | --- |
| A | `value_json="abc"`, `truncated=1`, `original_size=9000` |
| B | `value_json={"truncated":false,"x":1}`, `truncated=0` |
| C | A 的结果再 `grep "z"`（grep 返回空数组，未截断） |

另测 `(read "big").truncated` 与 `read "big".truncated`。

## 2. 输出

- A：`r.truncated == true`，`r.original_size == 9000`；工具边界只看到 `"abc"`。
- B：`r.truncated == false`（伪字段优先）；`get "truncated" r == false` 读 payload 自带键。
- C：结果 `truncated == true`（粘性；上游截断不被下游洗白）。
- `(read "big").truncated` 读 meta；`read "big".truncated` 是 `read("big".truncated)`。
- 六类 payload 的 `r.truncated` 都返回 `false`/`true`，不返回 `null`。

## 3. 失败语义

- meta 泄漏进 `args_json` 或 handler 入参 → 验收失败。
- 下游截断后 `truncated=false` → 验收失败（假阴性）。
- 单位不是 UTF-8 字节 → 验收失败。

## 4. 验收命令与阈值

- **命令**：`尚未落盘`（M6 后 `tools/check.sh m6-events`）。
- **阈值**：A/B/C 三场景 + 分组 2 例 + 六类 payload 各 1 例全部通过；泄漏 0 次。

## 5. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 侧车规则 | [05 §1](dsl/05-data-metadata.md) | 规范正文 |
| 决策与反例 | [D-008](../decisions/D-008.md) | 决策记录 |
