# 样例 07：综合例子（批量读取 → 逐项摘要 → 汇总报告）

> 状态：`unverified`。本样例按 [规范 v0.1 rev.1](../spec/dsl/README.md) 手工推导，仓库没有解释器，**未运行**。
> 依赖工具：[`read`](../spec/tools/T-001-tool-read.md)、[`json_parse`](../spec/tools/T-004-tool-json-parse.md)、[`grep`](../spec/tools/T-002-tool-grep.md)、[`write`](../spec/tools/T-003-tool-write.md)；事件见 [05 §2](../spec/dsl/05-data-metadata.md)。

## 1. 场景一句话

从 `files.json` 读一批文件路径，逐个统计 `TODO` 命中行数，拼成一份纯文本报告写入 `report.txt`，最后发一条 `report_ready` 事件。这里把顺序、条件、循环、错误处理、批量与白名单串在一起。

## 2. DSL 源码

```rill
# allow: read, json_parse, grep, write
# emit: report_ready
# dsl-version: 1

# 读取清单 + 解析包成一个调用，让 |? 能覆盖整条链路。
# 清单读不到或不是合法 JSON 时，退化为空数组。
fn load_paths() {
    return read "files.json" |> json_parse
}

let paths = load_paths |? json_parse "[]"
let mut report = ""
let mut total = 0

for path in paths {
    if path == "" {
        continue
    }
    if path == "STOP" {
        break
    }

    # 单个文件读不到时降级为空文本；grep 空文本返回 []。
    let text = read path |? ""
    let hits = text |> grep "TODO"
    total = total + hits.length

    if hits.length > 0 {
        report = report + path + ": " + hits.length + " todo(s)\n"
    } else {
        report = report + path + ": none\n"
    }
}

write "report.txt" report
emit "report_ready" { "files": paths.length, "total": total }
```

## 3. 逐步语义

**加载期**

1. header 建立 allow 集 `{read, json_parse, grep, write}` 与事件声明 `{report_ready}`。
2. `fn load_paths()` 注册；`read`、`json_parse`、`grep`、`write` 的 arity 都满足。
3. `load_paths |? json_parse "[]"`：左侧是零参函数调用（裸名），右侧是 `json_parse` 调用，结构合法。
4. `read path |? ""`：左侧单个 call，右侧字符串表达式，结构合法。
5. `emit "report_ready"` 的事件名在 `# emit:` 中；payload 是受限 JSON 对象字面量。
6. `paths.length` 是数组内建字段；`total` 是 `number`；`report` 是 `string`。

**执行期**

| 步 | 读到什么 / 返回什么 | 控制流 |
| --- | --- | --- |
| `load_paths` | 成功：`json_array`；失败：可捕获错误 | 失败且可捕获 → `json_parse "[]"`，得到 `[]`，`degraded=1` |
| `for path in paths` | 每轮一个元素的值拷贝 | 非数组 → `for_not_array`，中止 |
| `path == ""` | `bool` | 真 → `continue` |
| `path == "STOP"` | `bool` | 真 → `break` |
| `read path` | `string` | 可捕获失败 → `""`，`degraded=1`；不可捕获 → 中止 |
| `text |> grep "TODO"` | `json_array<string>` | 无命中 → `[]` |
| `hits.length > 0` | `bool` | 真 → 追加「有命中」行；假 → 追加 `none` |
| `report = report + ...` | `string` | 拼接；`number` 按 [D-016](../decisions/D-016.md) 渲染为文本 |
| `write "report.txt" report` | `null` | 写原始 UTF-8 字节，不加引号 |
| `emit "report_ready" {...}` | 无返回值 | fire-and-forget；无订阅方/队列满 → 丢弃并记日志 |

**失败传播**

| 场景 | 结果 |
| --- | --- |
| `files.json` 不存在、非法 JSON、`transient` | `load_paths` 失败且可捕获 → 空数组；报告为空、总数 0、事件仍发出 |
| `files.json` 被 `read` 截断 | `json_parse` 报不可捕获的 `limit`；`|?` 不接，脚本中止 |
| `files.json` 解析成对象/标量 | `json_parse` 成功，但 `for` 报 `for_not_array`；`|?` 不在 `for` 上，脚本中止 |
| 清单元素不是字符串 | `read path` 报不可捕获的 `constraint`；整批中止 |
| 单个文件不存在或内容非法 | `read path |? ""` 接住可捕获错误；该文件记为 `none`，其余继续 |
| `grep` 失败（如非法正则） | `grep` 不在 `|?` 左操作数位置，脚本中止 |
| `write` 失败 | 脚本中止；`write` 不保证原子，可能留下部分内容；`emit` 不执行 |
| `emit` payload 超过 `max_emit_bytes`/深度，或不符合内核 schema | 脚本中止（`limit`/`emit_schema`）；此时报告已经写完 |
| 无订阅方或队列满 | 丢弃并记日志，脚本继续，`ok` 不变 |

- 报告是内存里拼好后一次写出的；没有追加、流式写入或事务。
- `emit` 失败不会回滚 `write`；两条语句是独立的副作用。
- `degraded=1` 只要用过一次 `|?` 右侧；本样例有两处 `|?`。

## 4. 如果由 LLM 生成：prompt 大意

```text
读取 files.json，得到一批文件路径。
对每个路径：
- 空字符串跳过；遇到 STOP 停止；
- 读取文件，统计包含 TODO 的行数，累加到总数；
- 命中数大于 0 时在报告里写 "path: N todo(s)"，否则写 "path: none"。
把所有行拼成纯文本写入 report.txt，然后发一条 report_ready 事件，
payload 包含文件数和总命中数。
单个文件读不到时按空内容继续；路径越界、策略拒绝、资源上限不要兜底。
只使用 read、json_parse、grep、write；事件名先写进 # emit:。
不要写 while、par、递归、通用对象/数组字面量；调用用空格实参；开头写 # allow:。
```

## 5. 这个样例暴露的空白

- **EX-01（高）**：仍然依赖外部 `files.json`；没有目录枚举/`glob`，脚本无法从「一批文件」这个自然语言指令独立生成清单。
- **EX-02（高）**：清单元素类型不可校验；非字符串元素会让 `read path` 报不可捕获的 `constraint`，整批中止。
- **EX-03（高）**：`|?` 只能包单个 call；本样例用 `fn load_paths` 包住「读取 + 解析」，否则 `read` 的失败不会被 `|?` 接住。
- **EX-04（高）**：`null` 不是失败；如果某个键缺失，不能用 `|?` 兜底，只能显式比较 `== null`（本样例没有用到 `get`，但综合脚本很容易踩）。
- **EX-07（中）**：没有 `string.length`、`join`、`format`；报告只能靠 `+` 手工拼，且无法在写盘前检查报告大小。
- **EX-11（中）**：没有通用对象/数组构造；结构化事件只能用 emit 字面量，`json_build` 是可选工具，未注册时调用 `unknown_tool`。
- **EX-12（中）**：`write` 不原子、不能追加；`emit` 失败也不会回滚已写报告。
- **EX-13（中）**：`files.json` 被截断时 `json_parse` 报不可捕获的 `limit`；`|?` 不能把整批清单降级为空数组。
