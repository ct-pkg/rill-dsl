# 05 数据与事件

> 规范版本 `v0.1 rev.1`；状态 `unverified`。依据 D-008、D-006、D-014。

## 1. 截断元数据

### 1.1 值表示

运行时值由两部分组成：

```
value := (payload, meta)
payload ∈ null | bool | number | string | json_object | json_array
meta    := { truncated: bool, original_size: number }
```

- `payload` 是表达式、管道、实参、emit payload 看到的值。
- `meta` 是侧车，不进入 `payload`，也不进入工具边界。
- 工具返回值 `ToolResult`：`value_json`、`truncated`、`original_size`、`error_kind`。

### 1.2 工具边界

- handler 与工具参数只看到 `payload`；任何工具都不可能收到“带 meta 的包装值” [D-008]。
- 字段访问、索引、相等比较、算术、emit 序列化都只作用于 `payload`（侧车伪字段 `truncated`/`original_size` 除外，见 §1.3）。
- `let`、管道、`into`/`$`、`fn` 返回、`|?` 胜出分支都携带完整 `(payload, meta)`。

### 1.3 读取

| 写法 | 结果 |
| --- | --- |
| `x.truncated` | 先读 `meta.truncated`；若 `payload` 是对象且自有同名键，仍以 `meta` 为准 |
| `x.original_size` | 同上，读 `meta.original_size` |
| `get "truncated" x` | 读 `payload` 自带的 `truncated` 键（逃逸写法，普通工具调用） |
| `x.value` | 不特殊处理；按普通字段访问，通常是 `null` |

- 伪字段对六类 payload 都合法：`truncated` 返回 `false`/`true`，`original_size` 返回本值序列化字节数（不是 `0`），都不返回 `null`（`meta` 总有值）。
- 读取伪字段必须先分组：`(read "big").truncated`；`read "big".truncated` 是 `read("big".truncated)`。
- 对象 payload 自身含 `truncated` 键时，字段访问返回 `meta` 值；要业务值必须用 `get "truncated" x`。
- `get` 只做**单键**查找：`get "server.port" x` 查的是名为 `server.port` 的键，不会拆成 `server` → `port`。v0.1 的点分路径语义已废弃（未被 rev.1 沿用）；已知路径用字段访问 `x.server.port`，动态嵌套键串联 `get "port" (get "server" x)`。

### 1.4 传播与粘性

```
result.truncated     = 本次调用被截断 || 任一实参的 meta.truncated
result.original_size = 本次被截断 ? 切前字节数
                     : 任一实参 truncated ? 该实参 original_size 的最大值
                     : 本值序列化字节数
```

- 粘性理由：`read` 被截断后再 `grep`，若下游丢失标记，agent 会把“没搜到”当成“不存在”，这是可证明的假阴性 [D-008]。
- `original_size` 单位为 UTF-8 字节，与 `ExecLimits.max_output_bytes` 同口径。
- **两条分支口径不同，不可互推**：截断分支取工具切之前的**原始内容字节**；未截断分支取该值 **JSON 序列化后**的字节。对 `string` 差异最明显——未截断时含 JSON 引号与转义（`"a\nb"` 计 6 字节），截断时不计引号（原始内容 3 字节）。因此不能用未截断的 `original_size` 反推截断前大小，反之亦然；需要字符串原始长度时由工具返回，DSL 不提供换算。
- 截断只由工具产生；DSL 没有 `limit N` 语法。

## 2. emit 事件

### 2.1 语义

- `emit "name" payload` 序列化 payload（深拷贝）后交给事件总线，fire-and-forget：不等待、不阻塞、不关心订阅方。
- 事件名必须在 `# emit:` 列表中声明；未声明 → 加载期 `E_EVENT_NOT_DECLARED`。
- 无订阅方 → 丢弃并记日志，脚本不受影响；队列满 → 丢弃并记日志。
- 事件总线发布不是工具调用，不参与 allow/deny，也不受 `max_tool_calls` 限制；受 `max_emit_count` 限制。
- emit 不返回成功的布尔值；脚本不能据此分支。

### 2.2 上限与 schema

- `max_emit_bytes`：单条 payload 序列化后的最大字节数；默认 `65536`；超限 → `ok=0`、`error_kind=limit`，脚本可见，**不得静默丢弃** [D-014]。
- `max_payload_depth`：**通用** JSON payload 深度上限，emit payload 与工具返回 payload 共用；默认 `8`，按对象/数组嵌套层数计（字符串内的括号不计）。emit 侧超限 → `ok=0`、`error_kind=limit`，失败位置在 emit 语句；工具结果超限 → `limit`，失败位置在调用语句 [D-014]。
- 上限口径统一见 [07 §2](07-runtime.md)：输入上限 `max_input_bytes`（默认 `262144`）用于工具调用，不属于 emit。
- payload schema 由**内核配置**按事件名提供，**MVP 不做脚本语法**：脚本 header 没有 schema 声明，也没有 `additionalProperties` 开关。内核声明 schema 后，缺字段或类型不符 → `E_EMIT_SCHEMA`；未声明的事件不校验。多余顶层字段默认允许，由订阅方自行裁剪 [D-014]。
- `external_egress`：**内核事件注册属性**，按事件名配置，不是脚本 header；脚本不能自行把事件提升为可外发。未标记的事件不得投递给外部 webhook，只能进进程内订阅方。

### 2.3 订阅方

- 订阅方注册由内核配置控制，不在 DSL 脚本内。
- 订阅方可以是同步 C 函数、独立上下文里的 DSL 脚本、外部 webhook；三者的失败都不得回灌到发布方（fire-and-forget）。
- 订阅方派生执行的策略快照取点不属于本卷（P-014 事件因果链仍未拍板）。

## 3. 验收锚点

- [S-009](../S-009-truncation.md)、[S-019](../S-019-emit-limits.md)。
- 夹具：侧车不泄漏 1 例、伪字段优先 1 例、`get` 逃逸 1 例、粘性 2 例、字节口径 1 例；emit 超限 2 例、schema 2 例、`external_egress` 1 例。
