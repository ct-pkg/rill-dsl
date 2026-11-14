# 样例 01：顺序编排（读取 → 搜索 → 合并写盘）

> 状态：`unverified`。本样例按 [规范 v0.1 rev.1](../spec/dsl/README.md) 手工推导，仓库没有解释器，**未运行**。
> 依赖工具：[`read`](../spec/tools/T-001-tool-read.md)、[`grep`](../spec/tools/T-002-tool-grep.md)、[`write`](../spec/tools/T-003-tool-write.md)。

## 1. 场景一句话

读取两个源文件，分别找出包含 `TODO` 的整行，把两次结果合并后写入 `todo.json`。

## 2. DSL 源码

```rill
# allow: read, grep, write
# dsl-version: 1

# 第 1 步：读取两个输入文件。
let a = read "src/a.c"
let b = read "src/b.c"

# 第 2 步：上一步的结果通过管道追加到 grep 的第二个实参。
let a_hits = a |> grep "TODO"
let b_hits = b |> grep "TODO"

# 第 3 步：两个数组值连接，然后写盘。
let all = a_hits + b_hits
write "todo.json" all
```

## 3. 逐步语义

**加载期（脚本尚未执行）**

1. header 建立有效工具集 `{read, grep, write}`；`# dsl-version: 1` 被接受（[D-018](../decisions/D-018.md)）。
2. `read` 是固定 arity=1，`grep` 是 arity=2，`write` 是 arity=2（[T-001](../spec/tools/T-001-tool-read.md)–[T-003](../spec/tools/T-003-tool-write.md)）。
3. `a |> grep "TODO"` 的实参个数按「显式实参 + 管道值」静态计算为 2，满足 arity（[04 §1](../spec/dsl/04-pipeline-errors.md)）。
4. 所有名字都在 allow 集内，加载通过。

**执行期**

| 步 | 读到什么 / 返回什么 | 控制流 |
| --- | --- | --- |
| `read "src/a.c"` | `string`（文件 UTF-8 内容）+ 侧车 `truncated`/`original_size` | 等待完成；路径相对 workspace root 解析 |
| `read "src/b.c"` | 同上 | 顺序执行 |
| `a |> grep "TODO"` | `json_array<string>`，每个元素是命中的整行；无匹配返回 `[]` | `grep("TODO", a)` |
| `b |> grep "TODO"` | 同上 | 顺序执行 |
| `a_hits + b_hits` | `json_array`，两个数组连接（[D-016](../decisions/D-016.md)） | 纯值运算 |
| `write "todo.json" all` | `null`；内容是数组的 JSON 序列化文本 | 覆盖写；不返回字节数 |

**失败传播**

- 本样例没有 `|?`。任一调用失败都会中止当前块并向外传播：`read` 的 `not_found`/`denied`/`invalid_input`，`grep` 的 `invalid_input`，`write` 的 `constraint`/`denied`/`transient`/`limit`。
- 失败前没有写盘副作用；`write` 是最后一条语句。
- `degraded=0`（从未使用 `|?` 右侧）。
- 没有 `expr_stmt`，所以 `DslResult.value_json` 为 `null`（[07 §1](../spec/dsl/07-runtime.md)）；`write` 的 `null` 不是脚本返回值。

## 4. 如果由 LLM 生成：prompt 大意

```text
读取 src/a.c 和 src/b.c。
分别找出包含 TODO 的行，保留整行。
把两次结果合并，写入 todo.json。
只使用 read、grep、write 三个工具。
调用写成「名字 + 空格实参」，不要写 f(...)；每条语句一行；脚本开头写 # allow:。
```

## 5. 这个样例暴露的空白

- **EX-01（高）**：路径是硬编码的；脚本无法自己发现文件，批量读取必须先有一份外部清单。见 [问题清单](README.md#5-样例暴露的问题清单)。
- **EX-08（中）**：`grep` 的正则方言没有定义；`"TODO"` 恰好可以按字面理解，但带元字符的模式无法保证跨实现一致。
- **EX-07（中）**：`write` 收到数组时写 JSON 文本，不会把它拼成「一行一条」的纯文本；规范没有 `join`。
