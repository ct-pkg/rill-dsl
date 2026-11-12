# T-005 工具 `get`

- **状态**：`unverified`
- **决策**：[D-007](../../decisions/D-007.md)、[D-008](../../decisions/D-008.md)、[D-014](../../decisions/D-014.md)
- **规范**：[03 §6/§8](../dsl/03-semantics.md)、[05 §1.3](../dsl/05-data-metadata.md)、[07 §1](../dsl/07-runtime.md)
- **契约总则**：[README](README.md) §2–§6
- **里程碑**：M5（`$` 注入）
- **工具名**：`get`（非关键字）
- **arity**：2 个固定位置参数 `key`、`obj`；required：`key`、`obj`
- **accepts_context**：**是**（本目录唯一）
- **返回值**：六类值之一，或 `null`
- **截断**：不截断

## 1. 输入

```
get "truncated" x               # D-008 的逃逸写法：读 payload 自带的 truncated 键
get "port" cfg
$ |> get "port"                 # = get("port", $)
```

`args_json`：

```
["truncated", <x 的 payload>]
```

- `key` 必须是 `string`；`obj` 接受任意六类 payload。实际实参个数 ≠ 2 → 加载期 `arity`；`key` 非 `string` → `constraint`；两者 handler 都不执行。
- `key` 是**单个键**，不是点分路径：`get "server.port"` 查的是名为 `server.port` 的键，不会拆成 `server` → `port`。嵌套的动态取值要串联：`get "port" (get "server" cfg)`。
- `obj` 为 `json_object` 且存在该键 → 该值；缺失、`obj` 不是对象（含数组、标量、`null`）→ `null`。不报 `not_found`。
- 与字段访问的分工：`x.k` 是语法层字段访问，`truncated`/`original_size` 先读侧车；`get` 永远只读 payload 自带的键，是逃逸通道（[05 §1.3](../dsl/05-data-metadata.md)、[D-008](../../decisions/D-008.md) 第 4 条）。

### `$` 注入矩阵

`get` 的 `m=2`、`accepts_context=true`，注入规则见 [README](README.md) §3：

| 调用 | 显式 | 管道 | `n` | 注入 | 最终 args |
| --- | --- | --- | --- | --- | --- |
| `get "k"`（`into` 内） | 1 | 0 | 1 | 是（1<2） | `["k", $]` |
| `get "k" $` | 2 | 0 | 2 | 否 | `["k", $]` |
| `$ \|> get "k"` | 1 | 1 | 2 | 否 | `["k", $]` |
| `get "k" obj` | 2 | 0 | 2 | 否 | `["k", obj]` |
| `get "k"`（`into` 外） | 1 | 0 | 1 | 否（无 `$`） | `["k"]` → `arity`（加载期） |

`$ |> get "k"` 与 `get "k"` 在 `into` 内得到同一组实参：管道值已经补足第 2 位，不再叠加注入。这正是 [D-007](../../decisions/D-007.md) 第 6 条“按形参位注入，不是总是追加”的落点。

## 2. 输出

- payload：命中值为任意六类之一；未命中为 `null`。
- `truncated=0`；`original_size` = 返回值的序列化字节数（`null` 为 `4`）。
- 不截断：返回值序列化超过 `max_output_bytes` → `limit`。子值太大时不能切半截 JSON。
- 不复制、不合并侧车：`get` 只返回 payload；即使 `obj` 的侧车 `truncated=true`，返回值的 `truncated` 由运行时按粘性规则归并（[05 §1.4](../dsl/05-data-metadata.md)），不是 handler 行为。

## 3. 失败语义

| 场景 | `error_kind` | handler | `\|?` 捕获 |
| --- | --- | --- | --- |
| 实际实参个数（含管道与 `$`）≠ 2 | `arity`（加载期） | 不执行 | 否 |
| `key` 非 `string` | `constraint` | 未执行 | 否 |
| 返回值序列化 > `max_output_bytes` | `limit` | 执行并失败 | 否 |
| `max_tool_calls`/`timeout_ms` 超限、策略强杀 | `limit`/`revoked` | 边界检查 | 否 |
| 未归类 | `internal` | — | 否 |

- **缺键不是错误**：返回 `null`，`ok=1`，`|?` 不触发。这与 [03 §8](../dsl/03-semantics.md) 字段访问“缺键返回 `null`”一致。
- **不产生 `unconstrained_arg`**：隐式 `$` 在 schema 中有具名槽 `obj`，参与同一套浅校验；没有路径/域名类第三层约束不等于“未约束”。解释见 [README](README.md) §6。
- 不产生 `not_found`/`invalid_input`/`transient`/`denied`：纯值操作，无 I/O。

## 4. 参数约束

| 参数 | 约束类 | 档位 | 本期 |
| --- | --- | --- | --- |
| arity=2 | 加载期 `arity`（`params_schema` 长度） | 必做 | 声明 |
| `key` 的 `string` 类型 | 运行期 schema 浅校验 | 必做（[03 §6](../dsl/03-semantics.md)） | 声明 |
| `obj`（含隐式 `$`） | schema 具名槽，接受任意 payload；`args_json` 与 `ctx_json` 都过同一套校验 | 必做（D-014 §5.4 双通道） | 声明 |
| `obj` | 路径 / argv / 域名 / emit 类 | 不适用 | 不声明 |

## 5. 验收命令与阈值

- **命令**：`尚未落盘`。
- 计划：M5 `tools/check.sh m5-into-fn` 跑注入矩阵；M2 `m2-load` 跑加载期 `arity`；M6 `m6-events` 跑逃逸。
- **阈值**：
  - 注入矩阵 5 行逐行断言最终 `args_json`；`into` 外 `get "k"` 必须报加载期 `arity`；
  - D-008 逃逸 1 例：`get "truncated" r` 读 payload 键，与 `r.truncated` 读侧车结果不同；
  - 缺键/非对象 3 例（缺键、数组、标量）均返回 `null`，`ok=1`，`|?` 未触发；
  - `unconstrained_arg` 计数 0。

## 6. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 逃逸写法 | [05 §1.3](../dsl/05-data-metadata.md) L29-L39、[D-008](../../decisions/D-008.md) L51 | 规范 + 决策 |
| 注入规则 | [03 §6](../dsl/03-semantics.md) L57-L72、[D-007](../../decisions/D-007.md) L58 | 规范 + 决策 |
| 字段/索引语义 | [03 §8](../dsl/03-semantics.md) L83-L85 | 规范正文 |
| `accepts_context` 字段 | [07 §1](../dsl/07-runtime.md) L15-L23 | 规范正文 |
| 与旧文的差异 | `docs/design/dsl-spec-v0.1.md` L143-L145 | 历史输入（**未被 rev.1 沿用**） |

### 与旧文的差异

`v0.1` 的 `get "server.port"` 把字符串当点分路径。rev.1 没有采纳该语义：`$.server.port` 已由字段访问承担（[08 §2](../dsl/08-examples.md) L27-L28），`get` 在 [D-008](../../decisions/D-008.md) 中被重新定义为“读 payload 自带键”的逃逸通道。因此本条目只定义单键查找；点分路径不实现，也不作为兼容别名保留。
