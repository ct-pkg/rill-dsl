# S-010 赋值与 `let mut`

- **状态**：`unverified`
- **决策**：[D-009](../decisions/D-009.md)
- **规范**：[03 §3](dsl/03-semantics.md)
- **里程碑**：M3

## 1. 输入

```
let x = 1
x = 2

let mut y = 0
y = y + 1

fn f(p) {
    p = 1
}

let mut z = 0
let z = 1
```

## 2. 输出

- `x = 2` → `immutable_assign`，Hint：`declare it with 'let mut x = ...'`。
- `let mut y` 后 `y = y + 1` 成功，`y == 1`。
- 参数 `p` 不可赋值 → `immutable_assign`；要改先 `let mut q = p`。
- 同一作用域 `let z` 两次 → `dup_decl`。
- 赋值是语句：`if x = 1` → `syntax`，Hint 提示 `==`。
- 赋值只存不建名：`n = 1`（无 `let`）→ `assign_undefined`。

## 3. 失败语义

| 输入 | `error_kind` |
| --- | --- |
| 不可变目标 | `immutable_assign` |
| 未定义目标 | `assign_undefined` |
| 同作用域重复 `let` | `dup_decl` |
| 赋值作表达式 | `syntax` |
| 对外层/闭包捕获变量赋值 | `immutable_assign` |

- 全部为加载期错误（作用域内可静态判定）；Hint 必须给出可照做的修法。

## 4. 验收命令与阈值

- **命令**：`尚未落盘`（M3 后 `tools/check.sh m3-control`）。
- **阈值**：6 条输入逐条通过；4 类错误各有 golden；成功用例中 `y == 1`。

## 5. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 赋值规则 | [03 §3](dsl/03-semantics.md) | 规范正文 |
| 决策 | [D-009](../decisions/D-009.md) | 决策记录 |
