# S-005 括号与零参调用

- **状态**：`unverified`
- **决策**：[D-005](../decisions/D-005.md)
- **规范**：[02 §3](dsl/02-grammar.md)、[03 §2](dsl/03-semantics.md)
- **里程碑**：M2

## 1. 输入

```
read "x"
f()
a.b()
read "x".y
(read "x").y
f(a)(b)
let read = 1
```

## 2. 输出

- `read "x"` 是零/一参调用的统一形态；`(` 只作分组。
- `f()` → `syntax`：空括号不是 `expr`。
- `a.b()` → `syntax`：方法调用不支持。
- `read "x".y` 是 `read("x".y)`；`(read "x").y` 是对调用结果取字段。
- `f(a)(b)` = `f(a, b)`。
- 裸名 `f`：命中工具或零参 `fn` → 零参调用；命中**有参数** `fn` → `bare_fn_ref`（不是变量引用）；否则是变量引用。
- `let read = 1` → `shadow_tool`：局部绑定不得遮蔽工具名。

## 3. 失败语义

| 输入 | `error_kind` |
| --- | --- |
| `f()` | `syntax` |
| `a.b()` | `syntax` |
| `let read = 1` | `shadow_tool` |
| `fn grep(x) { }` | `shadow_tool` |

- `shadow_tool` 在加载期报，位置指向冲突名字；Hint 给出改名。

## 4. 验收命令与阈值

- **命令**：`尚未落盘`（M2 后 `tools/check.sh m2-parse`）。
- **阈值**：7 条输入逐条通过；`f()()`、`a.b()` 必须有负例；0 个 golden 失败。

## 5. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 形式规则 | [02 §3](dsl/02-grammar.md) | 规范正文 |
| 名字解析 | [03 §2](dsl/03-semantics.md) | 规范正文 |
| 决策 | [D-005](../decisions/D-005.md) | 决策记录 |
