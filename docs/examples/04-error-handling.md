# 样例 04：错误处理（可捕获回退，不可捕获终止）

> 状态：`unverified`。本样例按 [规范 v0.1 rev.1](../spec/dsl/README.md) 手工推导，仓库没有解释器，**未运行**。
> 依赖工具：[`read`](../spec/tools/T-001-tool-read.md)、[`json_parse`](../spec/tools/T-004-tool-json-parse.md)、[`get`](../spec/tools/T-005-tool-get.md)、[`write`](../spec/tools/T-003-tool-write.md)。

## 1. 场景一句话

先读 `config.json` 并解析；如果这条「读取 + 解析」链路发生可捕获错误，就回退到 `config.default.json`；两份都失败则终止。拿到配置后用 `into` 绑定 `$`，读取端口并写盘。

## 2. DSL 源码

```rill
# allow: read, json_parse, get, write
# dsl-version: 1

# 把「读取 + 解析」包成一个调用，才能让 |? 覆盖整条链路。
fn load_config(path) {
    return read path |> json_parse
}

# 左侧是可捕获失败时，执行右侧；degraded 置 1。
let cfg = load_config "config.json" |? load_config "config.default.json"

# into 把 cfg 绑定为 $；get 声明 accepts_context，
# 显式实参 1 个 < 形参 2 个，所以自动注入 $。
cfg into {
    let port = get "port"

    # 缺键返回 null，不是错误；|? 不会接住它，必须显式判断。
    if port == null {
        write "port.txt" "8080"
    } else {
        write "port.txt" port
    }
}
```

## 3. 逐步语义

**加载期**

1. 有效工具集 `{read, json_parse, get, write}`。
2. `fn load_config(path)` 注册为脚本函数；`read path` 与 `json_parse` 的 arity 都满足。
3. `load_config "config.json" |? load_config "config.default.json"`：`|?` 左侧是单个 `call`，右侧也是 `call`，结构检查通过（[04 §2](../spec/dsl/04-pipeline-errors.md)）。
4. `cfg into { ... }` 是 `expr into block`；`$` 在块内绑定，块外没有 `$`。
5. `get "port"` 在 `into` 内、`get` 声明 `accepts_context`、显式实参 1 < 固定形参 2，三个条件同时成立，注入 `$`；最终实参是 `["port", $]`。

**执行期**

| 步 | 读到什么 / 返回什么 | 控制流 |
| --- | --- | --- |
| `load_config "config.json"` | 成功：解析后的六类值之一；失败：一个 `error_kind` | 失败且可捕获 → 执行右侧 |
| 右侧 `load_config "config.default.json"` | 成功：默认配置；失败：错误继续向外 | 只有左侧失败且可捕获才执行；右侧不接收左侧的管道值 |
| `cfg into { ... }` | `$` 绑定为 `cfg` 的完整值（payload + meta） | 块内只读；块结束恢复外层（这里没有外层 `$`） |
| `get "port"` | 命中返回该值；缺键、`$` 非对象 → `null` | 不报 `not_found`；`|?` 不触发 |
| `port == null` | `bool` | 为真走默认 8080，否则写实际值 |
| `write "port.txt" ...` | `null` | `write` 不声明 `accepts_context`，所以必须显式传 `port` |

**错误传播**

| 错误类别 | `|?` 是否捕获 | 本样例结果 |
| --- | --- | --- |
| `not_found`（文件不存在）、`invalid_input`（JSON 非法）、`transient`（可重试 I/O）、`type`（值运算类型错） | 是 | 左侧失败 → 执行默认配置；`degraded=1` |
| `constraint`（路径越界、参数值不合法）、`denied`（策略/OS 拒绝）、`limit`、`approval_*`、`revoked`、`script_changed`、`internal` | 否 | 立即中止；默认配置不会执行 |
| 加载期错误（`unknown_tool`、`tool_not_allowed`、`arity`、`fallback_lhs` 等） | 否 | 脚本根本不执行 |
| `null` | — | 不是失败；不会触发 `|?` |

- 左侧成功：右侧不执行，`degraded=0`。
- 左侧失败且可捕获：右侧执行，取右侧值，`degraded=1`。
- 右侧失败：错误继续向外，`ok=0`；诊断同时给出两侧位置（[04 §2](../spec/dsl/04-pipeline-errors.md)）。
- 左侧失败但不可捕获：不执行右侧，`ok=0`，`degraded=0`。
- 脚本无法读取错误对象或 `error_kind`；`|?` 只产生值（[04 §2.7](../spec/dsl/04-pipeline-errors.md)）。

**两个反例（故意不可加载 / 不可回退）**

```rill
# 反例 A：分组后的管道不是单个 call → 加载期 fallback_lhs。
# allow: read, json_parse

let cfg = (read "config.json" |> json_parse) |? null
```

```rill
# 反例 B：路径越界是 constraint，不可捕获；右侧不会执行。
# allow: read

let cfg = read "../../etc/passwd" |? read "config.default.json"
```

反例 B 的期望错误形状（[07 §4](../spec/dsl/07-runtime.md)）：

```text
src/run.rill:4:11: error: tool 'read' rejected path '../../etc/passwd'.
  Constraint: path must resolve under '/workspace/'
  Hint: use a path under '/workspace/'.
```

## 4. 如果由 LLM 生成：prompt 大意

```text
先读 config.json 并解析成配置对象；如果读取或解析失败，改用 config.default.json。
两份都失败就终止，不要继续执行。
拿到配置后读取 port 字段并写入 port.txt；如果 port 缺失，写 8080。
只使用 read、json_parse、get、write。
读取 + 解析必须包成一个函数，这样 |? 才能覆盖整条链路。
不要用 try/catch；不要试图读取错误对象。
```

## 5. 这个样例暴露的空白

- **EX-03（高）**：`|?` 只能包住单个 call，`read ... |> json_parse |? ...` 不会捕获 `read` 的失败；必须像本样例一样用 `fn` 包装。并且 `|?` 只产生值，脚本无法按 `error_kind` 分支。
- **EX-04（高）**：`get` 缺键返回 `null`，而 `null` 不是失败，`|?` 不会接住；语言没有 `??` 或「缺键即失败」的统一写法。
- **EX-10（中）**：`into` 是语句，块的值被丢弃；本样例只能用 `into` 注入 `$`，不能把块内计算结果作为表达式返回。
- **EX-13（中）**：如果 `config.json` 被 `read` 截断，`json_parse` 会在 handler 之前报不可捕获的 `limit`，默认配置不会执行；要兜住必须先判断 `(read "config.json").truncated` 或调大 `max_output_bytes`。
