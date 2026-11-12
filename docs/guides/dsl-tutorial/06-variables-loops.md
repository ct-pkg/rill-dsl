# 06 变量与循环

> 状态：`unverified`；依据 `docs/spec/dsl/03-semantics.md` §3–§4 与 D-009。非规范性文档。

## 1. `let` 不可变，`let mut` 可变

```rill
# allow: write

let x = 1
let mut y = 0
y = y + 1
write "y.txt" y
```

| 写法 | 含义 |
| --- | --- |
| `let x = expr` | 新建不可变绑定 |
| `let mut y = expr` | 新建可变绑定 |
| `y = expr` | 只写入当前函数帧内已存在且为 `mut` 的绑定 |

反例与判据：

| 反例 | 结果 |
| --- | --- |
| `let x = 1` 后 `x = 2` | `immutable_assign`，Hint 提示 `let mut x = ...` |
| `n = 1`（没有 `let`） | `assign_undefined`；赋值只存不建名 |
| 函数参数 `p = 1` | `immutable_assign`；参数不可变 |
| `for` 变量 `item = 1` | `immutable_assign`；每轮 item 是不可变值拷贝 |
| `$ = 1` | `immutable_assign`；`$` 只读 |
| `if x = 1 { ... }` | `syntax`，Hint 提示 `==`；赋值是语句，不是表达式 |

没有 `+=`、`--`、`++`。`x = x + 1` 才是合法写法。

## 2. `for`：有界迭代

```
for IDENT in expr block
```

- `expr` 必须是 `json_array`；否则运行时 `for_not_array`。
- 空数组执行 0 次。
- item 是每轮的不可变值拷贝；要改就 `let mut v = item`。
- 每次迭代至少计 1 步；`continue` 不重置步数；超过 `max_steps` → `limit`。

```rill
# allow: read, grep, write

let lines = read "log.txt" |> grep "retry"
let mut count = 0
for line in lines {
    count = count + 1
}
write "count.txt" count
```

- `lines` 来自 `grep`，是 `json_array`。
- `count` 在循环外声明为 `mut`，循环内累加；循环结束后仍可见。

反例：在循环体内重新 `let` 同名变量：

```text
let mut count = 0
for line in lines {
    let count = count + 1
}
```

每轮新建一个内层 `count`，外层不变；脚本会成功退出但结果是 0。正确写法是上面的 `count = count + 1`。

## 3. `break` 与 `continue`

- `break` 结束最近一层 `for`。
- `continue` 进入下一轮。
- 两者只能出现在 `for` 块内（可以嵌在 `if` 里），不能跨 `fn` 边界。
- 出现在其他位置 → 加载期 `loop_control`。

```rill
# allow: read, grep, write

let lines = read "log.txt" |> grep "retry"
let mut kept = 0
for line in lines {
    if line == "SKIP" {
        continue
    }
    if line == "STOP" {
        break
    }
    kept = kept + 1
}
write "kept.txt" kept
```

## 4. 没有 `while`

rev.1 没有 `while`。`while true { ... }` 会报 `syntax`（`while` 只是普通标识符，后面跟块不成立）。

替代写法：

| 需求 | 写法 |
| --- | --- |
| 处理一批已知结果 | `for item in arr { ... }`，`arr` 来自工具结果 |
| 等待/轮询 | 让工具提供 `timeout`/`interval` 参数，一次调用内完成等待 |
| 失败重试 | 交给内核重试；脚本用 `\|?` 选择兜底值 |
| 提前结束 / 跳过某项 | `break` / `continue` |

```rill
# allow: read, grep

let lines = read "log.txt" |> grep "retry"
for line in lines {
    if line == "done" {
        break
    }
}
```

不要用 `for` 模拟无界轮询：循环次数仍受 `max_steps` 约束，超限返回 `ok=0`、`error_kind=limit`。

## 5. 数组只能来自工具结果

rev.1 没有数组字面量。`for` 的集合必须来自工具返回值、字段访问或已有绑定：

```rill
# allow: read, grep, write

let lines = read "log.txt" |> grep "error"
for line in lines {
    write "last-error.txt" line
}
```

`[1, 2, 3]` 只在 emit payload 中合法，不能出现在普通表达式或 `for` 的集合位置。

## 6. `par` 是保留字

`par` 不能作工具名、变量名、函数名、字段名或参数名。脚本任何位置出现 `par` 都在加载期报 `not_implemented`：

```text
par {
    write "a.txt" "a"
}
```

Hint：并行由内核调度，移除 `par`。`let par = 1` 同样是 `not_implemented`；工具注册名为 `par` 则是 `reserved_name`。
