# S-011 for 循环、break 与 continue

- **状态**：`unverified`
- **决策**：[D-009](../decisions/D-009.md)
- **规范**：[03 §4](dsl/03-semantics.md)
- **里程碑**：M3

## 1. 输入

```
for x in items {
    if bad x { continue }
    if done x { break }
    write "out.txt" x
}

for x in items {
    let mut v = x
    v = v + 1
}

for x in items {
    x = 1
}

for x in 42 {
    write "out.txt" x
}

break
```

## 2. 输出

- 第一个循环：`continue` 跳过本轮剩余语句；`break` 结束整个循环；item 是值拷贝。
- 第二个循环合法：`v` 是每轮新建的 `mut` 绑定。
- 第三个循环 → `immutable_assign`（循环变量不可赋值）。
- 第四个循环 → `for_not_array`。
- `break` 在循环外 → `loop_control`；`continue` 同。
- 空数组执行 0 次；每次迭代至少计 1 步。

## 3. 失败语义

| 输入 | `error_kind` |
| --- | --- |
| `for x in 42` | `for_not_array` |
| `x = 1` 于循环体 | `immutable_assign` |
| 循环外 `break`/`continue` | `loop_control` |
| 步数超限 | `limit`（`ok=0`） |

## 4. 验收命令与阈值

- **命令**：`尚未落盘`（M3 后 `tools/check.sh m3-control`）。
- **阈值**：5 条输入逐条通过；break/continue 行为各有轨迹 golden；`limit` 用例证明 `continue` 不重置计数。

## 5. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 循环语义 | [03 §4](dsl/03-semantics.md) | 规范正文 |
| 无 `while` 的裁定 | [D-009](../decisions/D-009.md) | 决策记录 |
