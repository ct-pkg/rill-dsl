# S-020 错误格式与 error_kind

- **状态**：`unverified`
- **决策**：[D-015](../decisions/D-015.md)、[D-010](../decisions/D-010.md)
- **规范**：[07 §3](dsl/07-runtime.md)、[07 §4](dsl/07-runtime.md)
- **里程碑**：M3、M9

## 1. 输入

依次触发：未在 allow 的工具、无 `# allow:`、路径越界、`$` 在 into 外、不可变赋值、`|?` 左侧非法、emit 未声明、步数超限。

## 2. 输出

每条错误使用以下格式（`label` 行按类别可选；`Hint:` 必填）：

```
<path>:<line>:<col>: error: <message>
  <label>: <detail>
  Hint: <hint>
```

- `path` 为脚本标识，缺省 `<script>`；`line`/`col` 1 基，`col` 按 UTF-8 字节。
- `message` 单行英文 ≤120 字符；`Hint:` 必须存在。
- 只报第一个错误。
- `DslResult.error_kind` 与 [07 §3](dsl/07-runtime.md) 的表一致；成功时为 `null`。

## 3. 失败语义

| 问题 | 判定 |
| --- | --- |
| 缺 `path` 或行列号为 0 | 验收失败 |
| 缺 `Hint:` | 验收失败 |
| 缺 `label` 行 | 验收通过（该类别规定必须有时除外） |
| 一次失败报多条错误 | 验收失败 |
| `error_kind` 不在枚举内 | 验收失败 |
| 加载与运行格式不一致 | 验收失败 |

## 4. 验收命令与阈值

- **命令**：`尚未落盘`（M3 后 `tools/check.sh m3-control`、M9 后 `m9-errors`）。
- **阈值**：8 条错误逐条匹配格式正则；每条 `error_kind` 至少 1 个 golden；0 条缺 Hint。

## 5. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 格式规则 | [07 §4](dsl/07-runtime.md) | 规范正文 |
| 类别表 | [07 §3](dsl/07-runtime.md) | 规范正文 |
| 决策 | [D-015](../decisions/D-015.md) | 决策记录 |
