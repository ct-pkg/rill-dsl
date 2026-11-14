# 样例 03：循环与遍历（逐个处理，含提前退出）

> 状态：`unverified`。本样例按 [规范 v0.1 rev.1](../spec/dsl/README.md) 手工推导，仓库没有解释器，**未运行**。
> 依赖工具：[`read`](../spec/tools/T-001-tool-read.md)、[`json_parse`](../spec/tools/T-004-tool-json-parse.md)、[`grep`](../spec/tools/T-002-tool-grep.md)、[`write`](../spec/tools/T-003-tool-write.md)。

## 1. 场景一句话

从 `tasks.json` 读出一组文件路径，逐个文件统计 `TODO` 命中行数；空路径跳过，遇到 `STOP` 提前结束，最后写出总命中数。

## 2. DSL 源码

```rill
# allow: read, json_parse, grep, write
# dsl-version: 1

let tasks = read "tasks.json" |> json_parse
let mut processed = 0

for task in tasks {
    # 空字符串不是错误，只是这一项不处理。
    if task == "" {
        continue
    }

    # STOP 是清单里的哨兵值，用来演示提前退出。
    if task == "STOP" {
        break
    }

    let text = read task
    let hits = text |> grep "TODO"
    processed = processed + hits.length
}

write "processed.txt" processed
```

## 3. 逐步语义

**加载期**

1. 有效工具集 `{read, json_parse, grep, write}`；`json_parse` 只用于把清单文本转成数组。
2. `read "tasks.json" |> json_parse` 的管道值补到 `json_parse` 的唯一形参，arity 满足。
3. `for task in tasks` 的集合表达式是变量引用；加载期不判断它的运行期类型。
4. `break`/`continue` 都位于 `for` 块内（可以嵌套在 `if` 里），位置检查通过（[03 §4](../spec/dsl/03-semantics.md)）。
5. `processed` 用 `let mut` 声明；`processed = processed + ...` 是合法赋值。

**执行期**

| 步 | 读到什么 / 返回什么 | 控制流 |
| --- | --- | --- |
| `read "tasks.json"` | `string` 清单文本 | 顺序执行 |
| `... |> json_parse` | `json_array`，元素按 JSON 文本顺序 | 解析失败 → `invalid_input`；上游截断 → `limit` |
| `for task in tasks` | 每轮把当前元素的值拷贝绑定到 `task` | 集合不是数组 → `for_not_array`；空数组 → 0 轮 |
| `task == ""` | `bool` | 为真 → `continue`，进入下一轮，不执行本轮剩余语句 |
| `task == "STOP"` | `bool` | 为真 → `break`，结束最近一层 `for` |
| `read task` | `string` 文件内容 | 相对 workspace root 解析；文件不存在 → `not_found` |
| `text |> grep "TODO"` | `json_array<string>`，命中行 | 无命中 → `[]` |
| `processed = processed + hits.length` | `number` 累加 | 每轮至少计 1 步；`continue` 不重置步数 |

**失败传播**

- `for` 的集合求值失败、集合不是数组（`for_not_array`）、循环体内任一调用失败，都会中止整个 `for` 块，不会继续下一轮（[04 §3](../spec/dsl/04-pipeline-errors.md)）。
- 本样例没有 `|?`，所以单个 `read task` 的 `not_found` 会终止整批；不会跳过失败项继续。要逐项容错，需要把调用写成 `read task |? ""` 一类的降级（见 [样例 05](05-batch-serial.md)）。
- `continue`/`break` 只处理正常控制流，不处理错误；它们不能跨 `fn` 边界。
- 循环变量是每轮的不可变值拷贝；本样例没有给 `task` 赋值。

## 4. 如果由 LLM 生成：prompt 大意

```text
读取 tasks.json，把它解析成数组。
逐个处理数组里的文件路径：
- 空字符串跳过；
- 遇到 STOP 停止整个循环；
- 其他路径读取文件，统计包含 TODO 的行数，累加到总数。
最后把总数写入 processed.txt。
只使用 read、json_parse、grep、write；不要写 while；不要用 par。
调用用空格实参；脚本开头写 # allow:。
```

## 5. 这个样例暴露的空白

- **EX-01（高）**：依然需要外部提供 `tasks.json`；没有目录枚举或 `glob` 工具，脚本无法自己发现待处理文件。
- **EX-02（高）**：`for` 只保证集合是数组，不保证元素是字符串。若清单里混入数字，`task == ""` 只是跨类型比较为 `false`，随后 `read task` 会报不可捕获的 `constraint`，整批中止；语言没有 `typeof` 或模式匹配来先过滤。
- **EX-06（高）**：本应「同时处理」的一组输入，只能串行 `for`；没有并行/汇合原语。`par` 是保留字，出现即加载失败（[D-019](../decisions/D-019.md)）。
