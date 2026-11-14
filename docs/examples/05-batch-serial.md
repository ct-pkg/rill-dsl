# 样例 05：批量处理与「并行」的当前等价写法

> 状态：`unverified`。本样例按 [规范 v0.1 rev.1](../spec/dsl/README.md) 手工推导，仓库没有解释器，**未运行**。
> 依赖工具：[`read`](../spec/tools/T-001-tool-read.md)、[`json_parse`](../spec/tools/T-004-tool-json-parse.md)、[`grep`](../spec/tools/T-002-tool-grep.md)、[`write`](../spec/tools/T-003-tool-write.md)。

## 1. 场景一句话

从 `files.json` 读出一组文件路径，逐个统计 `TODO` 命中数并累加。语言当前没有并行原语，这里展示串行批量写法，以及 `par` 为什么不能写。

## 2. DSL 源码（当前等价写法：串行批量）

```rill
# allow: read, json_parse, grep, write
# dsl-version: 1

let paths = read "files.json" |> json_parse
let mut total = 0

for path in paths {
    # 单项读取失败时降级为空串；grep 空串返回 []。
    # 只有 not_found / invalid_input / transient / type 会被接住；
    # constraint / denied / limit 仍然中止整批。
    let text = read path |? ""

    let hits = text |> grep "TODO"
    total = total + hits.length
}

write "total.txt" total
```

```text
# 反例：par 是保留字；脚本出现即加载期 not_implemented，不解析块。
# allow: read

par {
    let a = read "a.txt"
}
```

期望的 `par` 错误（[D-019](../decisions/D-019.md)、[07 §3.1](../spec/dsl/07-runtime.md)）：

- `error_kind`：`not_implemented`（消息文本按 [07 §4](../spec/dsl/07-runtime.md) 的格式由实现给出；规范只固定类别与 Hint）。
- Hint：`parallel execution is scheduled by the kernel; remove 'par'`。

## 3. 逐步语义

**为什么不是并行**

- 规范 MVP 全串行：每个工具调用完成后才继续（隐式 await，[04 §1](../spec/dsl/04-pipeline-errors.md)）。
- `par` 是保留关键字，不能作工具名/变量名/函数名；脚本里出现 `par` → 加载期 `not_implemented`，Hint 指向「并行由内核调度」（[D-019](../decisions/D-019.md)、[06 §6](../spec/dsl/06-security.md)）。
- 因此「多个独立调用同时发起、等待汇合」当前**没有对应语法**；等价写法只有：
  1. 顺序写多条调用（按源码顺序执行、逐条等待）；
  2. 用 `for` 串行遍历数组（本样例）；
  3. 由内核调度层并发调用多个 `dsl_exec`，脚本内部仍然看不到并发。

**执行期**

| 步 | 读到什么 / 返回什么 | 控制流 |
| --- | --- | --- |
| `read "files.json"` | `string` 清单文本 | 顺序执行 |
| `... |> json_parse` | `json_array` | 解析失败 → `invalid_input`；上游截断 → `limit` |
| `for path in paths` | 每轮一个路径的值拷贝 | 非数组 → `for_not_array` |
| `read path` | `string` 或失败信号 | 可捕获失败 → `""`，`degraded=1`；不可捕获 → 中止 |
| `text |> grep "TODO"` | `json_array<string>` | 无命中 → `[]` |
| `total = total + hits.length` | `number` | 累加；每轮至少计 1 步 |
| `write "total.txt" total` | `null` | 写数字的 JSON 文本 |

- `read path |? ""` 的右侧是任意表达式，不接收左侧管道值；它只在左侧整次调用失败且类别可捕获时执行。
- 如果清单里某个路径越界，`read` 报 `constraint`，不可捕获，整批中止；不会跳过该项。
- `paths` 不是数组时，`for` 语句本身报 `for_not_array`；这个错误不在任何 `|?` 左操作数位置，所以不会被降级。

**顺序调用等价写法**

```rill
# allow: read, write
# dsl-version: 1

let a = read "a.txt"
let b = read "b.txt"
write "both.txt" (a + b)
```

这两次读取是独立的，但按源码顺序串行执行；`write` 的第二个实参必须加括号，否则会先执行 `write` 再算 `+`（[11 常见错误 §4](../guides/dsl-tutorial/11-mistakes.md)）。

## 4. 如果由 LLM 生成：prompt 大意

```text
读取 files.json，得到一个文件路径数组。
逐个读取每个文件，统计包含 TODO 的行数并累加，最后写入 total.txt。
单个文件读不到时当作空内容继续，但路径越界或策略拒绝不要兜底，直接失败。
当前不支持并行；不要写 par，也不要把多个调用写成伪并行。
只使用 read、json_parse、grep、write；调用用空格实参；开头写 # allow:。
```

## 5. 这个样例暴露的空白

- **EX-01（高）**：批量输入仍然来自外部 `files.json`；没有目录枚举/`glob`，脚本不能自己发现文件。
- **EX-02（高）**：没有元素类型校验；清单中混入非字符串会让 `read path` 报不可捕获的 `constraint`，整批中止。
- **EX-06（高）**：没有并行/汇合原语；`par` 只报 `not_implemented`，当前只能串行，无法表达「同时发起、等待汇合」。
