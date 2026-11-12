# 10 错误与限制

> 状态：`unverified`；依据 `docs/spec/dsl/07-runtime.md` 与 D-010、D-015。非规范性文档。

## 1. 错误格式

所有错误（加载与运行）使用同一格式：

```
<path>:<line>:<col>: error: <message>
  <label>: <detail>
  Hint: <hint>
```

- `<path>` 是传给 `dsl_exec` 的脚本标识；没有路径时用 `<script>`。
- 行列 1 基，`col` 按 UTF-8 字节计。
- `message` 单行英文，不超过 120 字符。
- 第二行按类别出现：`Allowed tools:`、`Declared events:`、`Constraint:`、`Available:`。
- `Hint:` 必须存在，且给出可直接照做的修法。
- 同一次失败只报第一个错误，不做多错误聚合。

示例：

```
src/run.rill:3:10: error: '$' used outside 'into' block.
  Hint: wrap the expression in 'into { ... }' to bind '$'.
```

```
src/run.rill:4:1: error: cannot assign to immutable binding 'count'.
  Hint: declare it with 'let mut count = 0'.
```

## 2. 加载期 `error_kind`

加载错误发生在解析或静态检查阶段，任何工具都不执行。规范正文用 `E_*` 名称描述，`DslResult.error_kind` 使用小写枚举值。

| 家族 | `error_kind` | 触发 |
| --- | --- | --- |
| 词法/文法 | `syntax` | 未闭合定界符、非法 token、空括号、逗号调用 |
| header | `reserved_name`、`dup_header`、`no_allow_header`、`deny_without_allow`、`version` | 关键字作名字、header 重复、缺 allow、deny 单独出现、版本非 1 |
| 名字解析 | `unknown_tool`、`tool_not_allowed`、`event_not_declared`、`unknown_callee`、`undefined_name`、`bare_fn_ref`、`shadow_tool`、`dup_decl` | 未注册/未授权工具（含可选的 `json_build` 未注册）、未声明事件、未知调用、未定义名字、有参 fn 裸引用、遮蔽工具名、重复声明 |
| 赋值/控制 | `assign_undefined`、`immutable_assign`、`loop_control`、`return_outside_fn` | 赋值目标不存在、改不可变绑定、break/continue 在 for 外、return 在 fn 外 |
| 函数/调用 | `recursion`、`arity` | 调用图成环、`fn` 或固定 arity 工具的实参个数不符 |
| 管道 | `pipe_rhs`、`fallback_lhs` | `\|>` 右侧不是调用、`\|?` 左侧不是单个 call |
| emit | `dup_key` | payload 重复键 |
| 执行一致性 | `script_changed`、`policy_expansion_unapproved` | 脚本哈希变化、策略扩张未审批 |
| 保留语法 | `not_implemented` | `par` 等已保留但 MVP 不实现的语法 |

## 3. 运行期 `error_kind`

| 家族 | `error_kind` | `\|?` 捕获 |
| --- | --- | --- |
| 工具结果 | `not_found`、`invalid_input`、`transient` | 是 |
| 策略/值约束 | `denied`、`constraint`、`unconstrained_arg` | 否 |
| 审批 | `approval_required`、`approval_denied`、`approval_stale`、`approval_reused` | 否 |
| 资源/生命周期 | `limit`、`revoked` | 否 |
| 值运算 | `type`、`for_not_array`、`condition_not_bool` | 否 |
| emit | `emit_schema` | 否 |
| 兜底 | `internal` | 否 |

未知的 `error_kind` 一律按 `internal` 处理，不可捕获。`constraint` 只覆盖值层（类型、路径等）；实参个数不符已在加载期报 `arity`，不进入运行时。空结果不是错误：`grep` 无匹配是 `[]`、`read` 空文件是 `""`、`get` 缺键是 `null`、`json_parse ""` 是 `invalid_input`；`[]` 与 `null` 不等价，判空用 `.length > 0`。

## 4. `ExecLimits`

| 字段 | 默认 | 含义 |
| --- | --- | --- |
| `max_steps` | 10000 | 语句 + 每次循环迭代 |
| `max_tool_calls` | 200 | 工具调用次数 |
| `max_fn_depth` | 8 | 函数调用深度 |
| `max_emit_count` | 100 | emit 条数 |
| `max_output_bytes` | 262144 | 单次工具 payload 的最大字节数（不是整个 `DslResult`） |
| `max_input_bytes` | 262144 | 单次调用 `args_json` 与 `ctx_json` 序列化字节数之和 |
| `max_emit_bytes` | 65536 | 单条 emit payload 序列化后的最大字节数 |
| `max_payload_depth` | 8 | 任何 JSON payload（工具结果 + emit）最大嵌套深度 |
| `timeout_ms` | 30000 | 执行超时，不含审批等待 |

计数口径：

- 每执行一条语句 +1；每次循环迭代至少 +1（空体也算）。
- `continue` 不重置计数；`break` 正常结束。
- `|?` 右侧执行照常计数。
- 审批等待不计入 `timeout_ms`，单独回显 `approval_wait_ms`。
- `max_input_bytes` 口径：`args_json` 与 `ctx_json` 各自序列化后的 UTF-8 字节数之和；`ctx_json` 未注入按 0 计。超限 → `limit`，handler 不执行。

超限一律 `ok=0`、`error_kind=limit`，中止整个执行；已完成步骤的副作用保留。

## 5. `max_output_bytes`、`max_input_bytes` 与截断

| 工具类型 | 超限行为 |
| --- | --- |
| `read`、`grep` | 截断 payload，置 `truncated=1`，`original_size` 为切前字节数；不是错误 |
| `json_parse`、`get`、`json_build` | 不能返回半截 JSON → `limit`，不可捕获 |

上游结果被截断后作为 `requires_complete_input=1` 工具的实参 → `limit`，handler 不执行；不得降为 `invalid_input`。`max_input_bytes` 超限同样 → `limit`，handler 不执行；`write` 的文件不动。

截断结果不加省略号或标记；截断事实只在侧车。`truncated` 是粘性的：上游截断后，下游即使未截断，结果仍为 `truncated=true`。

## 6. `DslResult` 字段

| 字段 | 含义 |
| --- | --- |
| `ok` | `1` 成功，`0` 失败 |
| `value_json` | 最后一条 `expr_stmt` 的值；`ok=0` 时为 `null` |
| `error_msg` | 错误文本，成功时为 `null` |
| `error_kind` | 失败类别，成功时为 `null` |
| `error_line` / `error_col` | 失败位置，1 基 |
| `degraded` | `1` 表示至少用过一次 `|?` 右侧 |
| `policy_generation` | 本次执行使用的策略代 |
| `approval_wait_ms` | 审批等待耗时 |

注意：`let` 与 `emit` 是语句，不是 `expr_stmt`；`write` 是调用表达式语句，会作为 `expr_stmt` 贡献 `null`。只有最后一条表达式语句的值进入 `value_json`。

## 7. 读错误时的顺序

1. 看 `error_kind`：是加载错误还是运行错误，是否可被 `|?` 捕获。
2. 看 `error_line` / `error_col`：定位到具体 token 或调用。
3. 看 `Hint:`：按提示改；没有修法时规范要求写 `Hint: see <section>`。
4. 看 `degraded`：`ok=1` 但 `degraded=1` 表示结果来自兜底，不是全部正常。
