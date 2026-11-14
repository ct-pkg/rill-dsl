# 样例 02：条件分支（按工具返回值走不同路径）

> 状态：`unverified`。本样例按 [规范 v0.1 rev.1](../spec/dsl/README.md) 手工推导，仓库没有解释器，**未运行**。
> 依赖工具：[`read`](../spec/tools/T-001-tool-read.md)、[`grep`](../spec/tools/T-002-tool-grep.md)、[`write`](../spec/tools/T-003-tool-write.md)。

## 1. 场景一句话

读取应用日志，搜索 `ERROR` 行；有命中就把命中行写成 JSON 数组，没有命中就写纯文本 `none`。

## 2. DSL 源码

```rill
# allow: read, grep, write
# dsl-version: 1

let text = read "logs/app.log"
let errors = text |> grep "ERROR"

# grep 无匹配返回空数组 []，不是 null；判空必须用 .length。
if errors.length > 0 {
    write "errors.txt" errors
} else {
    write "errors.txt" "none"
}
```

## 3. 逐步语义

**加载期**

1. 有效工具集 `{read, grep, write}`；版本头 `1` 合法。
2. `read` arity=1；`text |> grep "ERROR"` 的显式实参 1 个 + 管道值 1 个 = 2，满足 `grep` 的 arity。
3. `write` 两个分支都是 2 个实参，满足 arity。
4. `if` 出现在语句位置；条件表达式在运行期求值，加载期只做文法与名字检查。

**执行期**

| 步 | 读到什么 / 返回什么 | 控制流 |
| --- | --- | --- |
| `read "logs/app.log"` | `string` 日志全文 | 顺序执行 |
| `text |> grep "ERROR"` | `json_array<string>`；无匹配为 `[]`，不是 `null` | `grep("ERROR", text)` |
| `errors.length` | `number`，数组元素个数；只有 `json_array` 有这个内建字段（[03 §8](../spec/dsl/03-semantics.md)） | 纯值运算 |
| `errors.length > 0` | `bool` | `if` 条件必须是 `bool`；非 `bool` 运行期 `condition_not_bool` |
| 命中分支 | `write "errors.txt" errors` 写数组的 JSON 文本，返回 `null` | 只执行 then 块 |
| 未命中分支 | `write "errors.txt" "none"` 写原始字符串 `none`，返回 `null` | 只执行 else 块 |

**失败传播**

- `read` 失败（如 `not_found`）或 `grep` 失败（如非法正则 `invalid_input`）会在 `if` 之前中止当前块；不会进入任一分支，也不会写文件。
- 条件求值失败（例如 `errors` 不是数组，`.length` 返回 `null`，`null > 0` 触发 `type`）中止包含该 `if` 的块（[04 §3](../spec/dsl/04-pipeline-errors.md)）。
- 本样例没有 `|?`，`degraded=0`。

## 4. 如果由 LLM 生成：prompt 大意

```text
读取 logs/app.log，找出包含 ERROR 的行。
如果有命中，把命中行写入 errors.txt；如果没有命中，写入字符串 none。
只使用 read、grep、write。不要用 errors != null 判空，空结果是 []。
调用用空格实参，不用括号；每条语句一行；开头写 # allow:。
```

## 5. 这个样例暴露的空白

- **EX-09（中）**：文法没有 `else if`，多分支只能写成 `else { if ... }` 的嵌套；`if` 也只是语句，不能写成 `let x = if ... { ... } else { ... }` 来选择值。
- **EX-04（高）**：`grep` 的 `[]` 与 `null` 语义不同，但语言没有 null 合并或空集合谓词；判空只能靠 `.length > 0`，这类规则需要 LLM 记住。
- **EX-08（中）**：`ERROR` 作为正则模式的含义依赖未定义的正则方言；如果实现把 `ERROR` 当字面量、另一实现当正则，边界行为可能不同。
