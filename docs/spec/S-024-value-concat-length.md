# S-024 值层：拼接与 `length`

- **状态**：`unverified`
- **决策**：[D-016](../decisions/D-016.md)
- **规范**：[03 §1](dsl/03-semantics.md)、[03 §8](dsl/03-semantics.md)
- **里程碑**：M3、M5

## 1. 输入

```
let n = 3
let s = "count: " + n
let t = n + " files"
let u = "ok: " + true
let v = "value: " + null

let arr = json_parse "[1,2]"
let len = arr.length
let obj = json_parse "{}"
let obj_len = obj.length
let str_len = "abc".length

arr into {
    let inner_len = $.length
}
```

失败用例单独成脚本，避免在长度断言前中止：`let bad = 3 + true` → 运行期 `type`。

## 2. 输出

| 表达式 | 结果 |
| --- | --- |
| `"count: " + 3` | `"count: 3"` |
| `3 + " files"` | `"3 files"` |
| `"ok: " + true` | `"ok: true"` |
| `"value: " + null` | `"value: null"` |
| `3 + true` | 运行时 `type` |
| `arr.length` | 元素个数（`number`） |
| `$.length`（`$` 为数组） | 同 `arr.length` |
| 对象/字符串/`null` 的 `.length` | `null`，不报错 |

- `.length` 只挂在 `json_array`；`x.length` 与 `$.length` 是同一条后缀字段规则。
- `==` 仍严格：`"3" == 3` 为 `false`。

## 3. 失败语义

| 输入 | `error_kind` |
| --- | --- |
| `number + bool` 等非允许组合 | `type` |
| 数组 + 非数组 | `type` |

- `type` 为运行期错误，按 [04 §3](dsl/04-pipeline-errors.md) 中止块。

## 4. 验收命令与阈值

- **命令**：`尚未落盘`（M3 后 `tools/check.sh m3-control`）。
- **阈值**：8 条输出逐条断言；`type` 负例 2 个；`length` 三类值（数组/对象/字符串）各 1 例。

## 5. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 算术规则 | [03 §1](dsl/03-semantics.md) | 规范正文 |
| 字段规则 | [03 §8](dsl/03-semantics.md) | 规范正文 |
| 决策 | [D-016](../decisions/D-016.md) | 技术裁定 |
