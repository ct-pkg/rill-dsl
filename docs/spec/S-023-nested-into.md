# S-023 嵌套 `into`

- **状态**：`unverified`
- **决策**：[D-017](../decisions/D-017.md)
- **规范**：[03 §7](dsl/03-semantics.md)
- **里程碑**：M5

## 1. 输入

```
read "pkg.json" |> json_parse into {
    let name = $.name
    let deps = $.dependencies
    deps into {
        let dep_count = deps.length
        write "summary.txt" (name + ":" + dep_count)
    }
    write "outer.txt" $.name
}
```

## 2. 输出

- 外层 `$` 是整份配置；内层 `$` 是 `deps` 数组。
- 内层块结束后 `$` 恢复为外层配置；`write "outer.txt" $.name` 读到配置的 `name`。
- 内层块内 `deps.length` 与外层 `name` 都可见（闭包只读）。
- `$` 只读；任何 `$ = ...` → `immutable_assign`。
- 块外使用 `$` → 加载期 `dollar_outside`。

## 3. 失败语义

| 输入 | `error_kind` |
| --- | --- |
| 内层 `$ = ...` | `immutable_assign` |
| `into` 块外 `$` | `dollar_outside` |
| 内层引用外层 `$` 而不是恢复后的值 | 语义错误，验收失败 |

- 嵌套不额外消耗 `max_fn_depth`；语句计数照常。

## 4. 验收命令与阈值

- **命令**：`尚未落盘`（M5 后 `tools/check.sh m5-into-fn`）。
- **阈值**：上述 1 个三段式用例逐行断言；覆盖 1 例、恢复 1 例、只读负例 1 例；0 次 `$` 逃逸。

## 5. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 作用域规则 | [03 §7](dsl/03-semantics.md) | 规范正文 |
| 决策与 CT 对比 | [D-017](../decisions/D-017.md) | 技术裁定 |
