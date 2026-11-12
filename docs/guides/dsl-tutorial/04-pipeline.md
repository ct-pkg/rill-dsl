# 04 数据流：管道与降级

> 状态：`unverified`；依据 `docs/spec/dsl/04-pipeline-errors.md` 与 D-007、D-010。非规范性文档。

## 1. `|>`：把左边的值追加到右边调用

```
a |> f b        =  f(b, a)
a |> f b |> g   =  g(f(b, a))          # 左结合
x |> grep "pat" =  grep("pat", x)      # grep arity=2；管道值补到第 2 位
```

- 管道值**追加**在显式实参之后，不替换、不插队。
- 管道只追加实参，不改变工具 arity：`x |> read "p"` 得到 2 个实参，`read` arity=1 → `constraint`。写管道时右侧工具的形参个数必须能容纳管道值。
- 左侧是任意 `expr`；右侧必须是一个**可调用节点**：`call`，或加载期解析为零参调用的裸 `IDENT`，允许分组。
- 右侧不是调用 → 加载期 `pipe_rhs`，Hint 提示「管道右侧必须是调用」。

```rill
# allow: read, grep, write

let hits = read "src/main.c" |> grep "TODO"
write "todo.json" hits
```

`hits` 的求值顺序：先 `read("src/main.c")` 得到 `text`，再 `grep("TODO", text)`。

等价显式写法：

```rill
# allow: read, grep, write

let hits = grep "TODO" (read "src/main.c")
write "todo.json" hits
```

## 2. `|?`：调用级降级

`|?` **高于** `|>`：

```
a |> f b |? g c     =  a |> (f b |? g c)
read "p" |? read "f" |> parse
                    =  (read "p" |? read "f") |> parse
```

- 左侧必须是**单个可调用节点**（`call`，或零参裸名，可分组）；不是 → 加载期 `fallback_lhs`。
- 失败单元 = 该 call 的整次求值：实参求值失败、约束拒绝、handler 失败都算；更早的管道阶段失败不算。
- 左侧成功 → 右侧不执行。
- 左侧失败且错误可捕获 → 执行右侧，取右侧值，并置 `degraded=1`。
- 右侧独立求值，不接收左侧管道值；右侧失败则错误继续向外。
- 多个 `|?` 左结合：`a |? b |? c` = `(a |? b) |? c`。

```rill
# allow: read, json_parse

let cfg = read "primary.json" |? read "fallback.json" |> json_parse
```

解析为 `(read "primary.json" |? read "fallback.json") |> json_parse`：

| 场景 | 结果 |
| --- | --- |
| `primary.json` 读取成功 | 直接 `json_parse`；右侧 `read` 不执行，`degraded=0` |
| `primary.json` 不存在（`not_found`） | 读 `fallback.json`，再 `json_parse`；`degraded=1` |
| 两个都读不到 | 第二次失败继续向外，`ok=0` |
| 文件读到但不是合法 JSON | `json_parse` 的 `invalid_input` **不在** `\|?` 左侧失败单元内，`ok=0` |

## 3. 哪些错误可被捕获

| 类别 | `error_kind` | `\|?` 捕获 |
| --- | --- | --- |
| 结果不存在 | `not_found` | 是 |
| 输入不合法 | `invalid_input` | 是 |
| 瞬时失败 | `transient` | 是 |
| 策略拒绝 | `denied` | 否 |
| 参数越界/形状不符 | `constraint` | 否 |
| 审批 | `approval_required` / `approval_denied` | 否 |
| 资源上限 | `limit` | 否 |
| 策略撤销/脚本变更 | `revoked` / `script_changed` | 否 |
| 内核内部错误 | `internal` | 否 |
| 加载错误 | `load` | 否（加载阶段根本不执行） |

两条容易误判的规则：

- **`null` 是值，不是失败**：缺键、越界返回 `null`，不会触发 `|?`。
- **不可捕获错误即使出现在 `|?` 左侧，也照常中止块**。这是安全要求：`denied`、`constraint`、`limit` 不能被静默改写成正常结果。

```rill
# allow: read

let text = read "/workspace/../../etc/passwd" |? "fallback"
```

路径越界产生 `constraint`，不可捕获；`|?` 不会执行右侧，整个执行 `ok=0`。

## 4. 没有 try/catch

- 运行时失败是控制信号，不是值：不能存变量、比较、当参数。
- 唯一消费者是 `|?`，且只消费它左侧那一个 call 的信号。
- 没有块级恢复；没有「失败后继续执行同块下一条语句」。
- `|?` 不回滚已发生的副作用；需要补偿由工具提供。

反例：把整段管道包起来当 `try/catch`：

```text
let cfg = (read "a.json" |> json_parse) |? null
```

左侧是分组管道，不是单个 call → 加载期 `fallback_lhs`。正确做法是用 `fn` 包成一个调用：

```rill
# allow: read, json_parse

fn load_config() {
    return read "a.json" |> json_parse
}

let cfg = load_config |? null
```

## 5. `degraded` 怎么读

`degraded` 不在脚本里，脚本不能读它。它是 `DslResult` 的字段，由调用方（内核）读取：

| 值 | 含义 |
| --- | --- |
| `0` | 本次执行没有使用过 `|?` 右侧 |
| `1` | 至少有一次 `|?` 右侧接管 |

`ok=1 && degraded=1` 表示「执行成功，但至少一步走了兜底」。调用方必须能区分「全部正常」与「全部走兜底」，否则 agent 会把兜底结果当成真实结果。

## 6. 失败行为速查

| 场景 | 行为 | `ok` |
| --- | --- | --- |
| 普通调用失败 | 中止当前块，信号向外 | 0 |
| `\|?` 左侧可捕获失败 | 不中止，执行右侧 | 1 |
| `\|?` 左侧不可捕获失败 | 中止当前块 | 0 |
| `\|?` 右侧失败 | 中止当前块，诊断含两侧位置 | 0 |
| `if` 条件失败/非 `bool` | 中止包含该 `if` 的块 | 0 |
| `for` 集合非数组 | 中止，`for_not_array` | 0 |
| 循环体失败 | 中止 `for` 块，不继续下一轮 | 0 |
| emit 超限 | 中止，`limit` | 0 |
| 步数/调用数/超时/深度超限 | 中止整个执行，`limit` | 0 |
| 策略在调用边界撤销 | 中止，`revoked` | 0 |

块中止时，块内此前完成的工具副作用保留。
