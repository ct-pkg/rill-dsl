# S-006 emit payload

- **状态**：`unverified`
- **决策**：[D-006](../decisions/D-006.md)
- **规范**：[02 §4](dsl/02-grammar.md)
- **里程碑**：M2

## 1. 输入

```
emit "e" { "path": "src/a.c", "count": 3 }
emit "e" {
    "path": "src/a.c",
    "count": n + 1
}
emit "e" { "items": [1, 2, 3] }
emit "e" {}
emit "e" { "a": 1, "a": 2 }
emit "e" { "a": 1, }
```

## 2. 输出

- payload 是受限 JSON 字面量：对象、数组或任意 `expr` 作值；键必须是字符串字面量。
- 多行 payload 合法；JSON 内部与 `emit` 和 payload 之间的换行被 N8 删除。
- 值位可以是表达式（`n + 1`），不要求 `postfix_expr`。
- `emit "e" {}` 是合法空 payload。
- payload 之后不得接后缀。

## 3. 失败语义

| 输入 | `error_kind` |
| --- | --- |
| 重复键 | `dup_key` |
| 尾随逗号 | `syntax` |
| 非字符串键 | `syntax` |
| `emit "e" {...}.x` | `syntax` |
| 事件未声明 | `event_not_declared` |

## 4. 验收命令与阈值

- **命令**：`尚未落盘`（M2 后 `tools/check.sh m2-parse`）。
- **阈值**：6 条输入中 4 条成功、2 条报对应错误；多行 payload 与表达式值位各有 1 个 golden；0 个失败。

## 5. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 产生式 | [02 §4](dsl/02-grammar.md) | 规范正文 |
| 换行规则 | [01 §7 N8](dsl/01-lexical.md) | 规范正文 |
| 决策 | [D-006](../decisions/D-006.md) | 决策记录 |
