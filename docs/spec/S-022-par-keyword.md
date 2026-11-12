# S-022 `par` 保留字

- **状态**：`unverified`
- **决策**：[D-019](../decisions/D-019.md)
- **规范**：[01 §3](dsl/01-lexical.md)、[07 §3.1](dsl/07-runtime.md)
- **里程碑**：M1、M2

## 1. 输入

```
par { write "a" "b" }
let par = 1
```
另测内核注册名为 `par` 的工具。

## 2. 输出

- 脚本出现 `par` → 加载期 `not_implemented`，Hint：`parallel execution is scheduled by the kernel; remove 'par'`；不解析后面的块。
- `let par = 1` → 同一个 `not_implemented`（任何位置出现 `par` token 都在加载期报此错误，不进入后续文法判定）。
- 注册工具名 `par` → `reserved_name`。

## 3. 失败语义

| 输入 | `error_kind` |
| --- | --- |
| 脚本含 `par` | `not_implemented` |
| 注册工具名 `par` | `reserved_name` |

- 均为加载期错误；任何工具都不执行。

## 4. 验收命令与阈值

- **命令**：`尚未落盘`（M1/M2 后 `tools/check.sh m1-tokens`、`m2-parse`）。
- **阈值**：3 条输入逐条通过；`par` 不得被解析为工具调用或变量；错误必须带 Hint。

## 5. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 关键字表 | [01 §3](dsl/01-lexical.md) | 规范正文 |
| 决策 | [D-019](../decisions/D-019.md) | 技术裁定 |
