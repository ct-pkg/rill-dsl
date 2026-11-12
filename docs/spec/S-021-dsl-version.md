# S-021 `# dsl-version:` 头

- **状态**：`unverified`
- **决策**：[D-018](../decisions/D-018.md)
- **规范**：[02 §1](dsl/02-grammar.md)、[07 §5](dsl/07-runtime.md)
- **里程碑**：M2

## 1. 输入

```
# allow: read
# dsl-version: 1
```
另测 `# dsl-version: 2`、`# dsl-version: 1.0`、`# dsl-version: v1`、重复的版本头。

## 2. 输出

- `1`：接受，不改变任何解析；header 可选，不写也正常加载。
- `2`、`1.0`：`version`，Hint 指出只支持 `1`。
- `v1`：`syntax`（版本头只接受数字）。
- 重复版本头：`dup_header`。
- 版本头不参与 `# allow:` 默认拒绝判定；没有 `# allow:` 仍然 `no_allow_header`。

## 3. 失败语义

| 输入 | `error_kind` |
| --- | --- |
| `2` / `1.0` | `version` |
| `v1` | `syntax` |
| 重复 | `dup_header` |

- 失败发生在加载期，任何工具都不执行。

## 4. 验收命令与阈值

- **命令**：`尚未落盘`（M2 后 `tools/check.sh m2-parse`）。
- **阈值**：5 条输入逐条通过；`1` 不影响解析结果（与省略版本头的 AST 相等）。

## 5. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| header 文法 | [02 §1](dsl/02-grammar.md) | 规范正文 |
| 决策 | [D-018](../decisions/D-018.md) | 技术裁定 |
