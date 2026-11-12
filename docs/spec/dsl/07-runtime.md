# 07 运行时、错误与版本

> 规范版本 `v0.1 rev.1`；状态 `unverified`。依据 D-010、D-012、D-013、D-014、D-015。

## 1. 内核接口

```ct
struct ToolResult {
    char *value_json;      // payload；失败时为 NULL
    int   truncated;       // 0/1
    long  original_size;   // UTF-8 字节
    char *error_kind;      // NULL = 成功；见 §3
};

struct ToolDef {
    char *name;
    char *description;     // 给 LLM 看
    char *params_schema;   // 固定位置形参个数与类型；可变长为 NULL
    int   accepts_context; // 是否接受隐式 $
    char *context_param;   // $ 注入的具名形参槽；accepts_context=0 时为 NULL
    int   requires_approval;
    int   requires_complete_input; // 1 = 任一实参 meta.truncated=1 时拒绝执行（limit）
    ParamConstraint *constraints;
    ToolResult (*handler)(char *args_json, char *ctx_json);
};

struct DslResult {
    int   ok;
    char *value_json;
    char *error_msg;
    char *error_kind;
    int   error_line;          // 1 基
    int   error_col;           // 1 基，按 UTF-8 字节计
    int   degraded;            // 至少用过一次 |? 右侧
    unsigned long policy_generation;
    long  approval_wait_ms;
};

DslResult dsl_exec(const char *source, int len, ToolRegistry *reg,
                   EventBus *bus, ExecLimits *limits,
                   PolicySnapshot *policy_in);
```

- `policy_in == NULL`：内核按当前配置构建快照；非 NULL：只读该快照（调用方负责生命周期）。
- 一次 `dsl_exec` 只产生一个 `DslResult`；脚本不能嵌套调用 `dsl_exec`。
- `DslResult.value_json` 是**最后一条 `expr_stmt`** 的值；没有 `expr_stmt` 时为 `null`。
- `requires_complete_input=1` 的工具：任一实参 `meta.truncated=1` 时，运行时在调用 handler 之前失败，`error_kind=limit`（见 §3.2）。这类工具不能用半截输入产出结果。
- `accepts_context=1` 必须给出 `context_param`（具名形参槽，如 `get` 的 `obj`），且该名必须在 `params_schema` 中；缺失或名字不在 schema → 注册期拒绝。注入 `$` 时该槽没有绑定任何约束 → 运行期 `unconstrained_arg`（[D-014](../../decisions/D-014.md) 第 5 条）。
- `json_build` 是**可选工具**：内核可以不注册；未注册时脚本对它的调用按普通未注册工具处理，加载期 `unknown_tool`。可选不等于放行，`# allow:` 与参数约束照常适用。

## 2. ExecLimits

```ct
struct ExecLimits {
    int max_steps;             // 语句 + 每次循环迭代
    int max_tool_calls;
    int max_fn_depth;
    int max_emit_count;
    int max_output_bytes;      // 单次工具 payload 的最大字节数（不是整个 DslResult）
    int max_input_bytes;       // 单次工具调用输入序列化后的最大字节数
    int max_emit_bytes;        // 单条 emit payload 序列化后的最大字节数
    int max_payload_depth;     // 任何 JSON payload 的最大嵌套深度（工具结果 + emit）
    int timeout_ms;            // 不含审批等待
};
```

- 超限一律 `ok=0`、`error_kind=limit`。失败位置：`max_output_bytes`、`max_input_bytes`、工具结果深度超限在调用语句；`max_emit_bytes`、emit payload 深度超限在 emit 语句。
- rev.1 基线默认值（内核可覆盖）：`max_steps=10000`、`max_tool_calls=200`、`max_fn_depth=8`、`max_emit_count=100`、`max_output_bytes=262144`、`max_input_bytes=262144`、`max_emit_bytes=65536`、`max_payload_depth=8`、`timeout_ms=30000`。
- 计数口径：语句执行 +1；循环每次迭代至少 +1；`continue` 不重置；`|?` 右侧执行照常计数。
- `max_input_bytes` 口径：一次工具调用的输入总量 = `args_json` 与 `ctx_json` 各自序列化后的 UTF-8 字节数之和；`ctx_json` 未注入时按 0 计。单参数字节数不会超过总量，因此任一实参超限必然使本次调用超限。
- 两个通道**互斥**：`args_json` 只放显式实参（书写序）与管道值；`ctx_json` 只放注入的 `$`，未注入时为 NULL。同一个值不会同时出现在两个通道，注入不会重复计入总量。
- `max_payload_depth` 口径：按对象/数组嵌套层数计，字符串内部的括号与转义不计；工具返回 payload 与 emit payload 共用同一上限。

## 3. 错误类别

### 3.1 加载期 `error_kind`

| `error_kind` | 触发 |
| --- | --- |
| `syntax` | 词法/文法错误，含未闭合定界符、非法 token |
| `reserved_name` | 工具名是关键字或保留字 |
| `dup_header` | 同一 header 键重复 |
| `no_allow_header` | 无 `# allow:` 或列表为空 |
| `deny_without_allow` | 只有 `# deny:` |
| `version` | `# dsl-version:` 不是 `1` |
| `unknown_tool` | 调用名既不在工具注册表，也不在脚本 `fn`（加载期名字解析的唯一失败点） |
| `tool_not_allowed` | 工具不在 `# allow:` |
| `event_not_declared` | emit 未在 `# emit:` 声明 |
| `undefined_name` | 引用未定义名字 |
| `bare_fn_ref` | 有参 `fn` 被当裸名引用 |
| `shadow_tool` | 局部绑定/参数/`fn` 与工具同名 |
| `dup_decl` | 同作用域重复声明 |
| `assign_undefined` | 赋值目标不存在 |
| `immutable_assign` | 对不可变绑定/参数/循环变量/`$` 赋值 |
| `loop_control` | `break`/`continue` 不在 `for` 内 |
| `return_outside_fn` | `return` 不在 `fn` 内 |
| `recursion` | 调用图有环 |
| `arity` | `fn` 或固定 arity 工具的实际实参个数（含管道值与 `$` 注入）与形参个数不符；`json_build` 收到奇数个实参（契约要求键值成对，静态可算） |
| `not_implemented` | `par` 等已保留但 MVP 不实现的语法 |
| `pipe_rhs` | `\|>` 右侧不是可调用节点（call、零参调用裸名、首操作数是可调用节点的 fallback 链） |
| `fallback_lhs` | `\|?` 链的最左操作数不是单个调用 |
| `dollar_outside` | `$` 出现在任何 `into` 块之外 |
| `policy_expansion_unapproved` | 策略扩张未审批 |

`unknown_callee` 已并入 `unknown_tool`：加载期名字解析只有一个失败点——名字既不在工具注册表也不在脚本 `fn`。拆成两个 kind 会让同一条调用因注册状态不同而换类别，且没有独立判据；`unknown_tool` 的 Hint 同时提示检查工具名与函数名。

### 3.2 运行期 `error_kind`

`not_found`、`invalid_input`、`transient`、`denied`、`constraint`、`approval_required`、`approval_denied`、`approval_stale`、`approval_reused`、`limit`、`revoked`、`script_changed`、`internal`、`type`、`emit_schema`、`dup_key`、`for_not_array`、`unconstrained_arg`、`condition_not_bool`。

- `script_changed` 是运行期检查：执行期脚本哈希与加载期不一致时，在下一次工具调用边界失败（[D-012](../../decisions/D-012.md)）。
- `dup_key` 是**参数协议级**重复键：`args_json`/`ctx_json` 中出现同名键，解析即失败，handler 不执行（[D-014](../../decisions/D-014.md) 第 6 条）。
- 三种“重复键”语义分开：协议级 → `dup_key`（运行时，handler 之前）；业务 JSON 文本里的重复键 → `invalid_input`（handler 解析时）；`json_build` 的重复键 → `invalid_input`（handler 构造时）。

- `limit` 覆盖两类：① `ExecLimits` 任一计数超限；② `requires_complete_input=1` 的工具收到被上游截断的实参（`meta.truncated=1`）。第 ② 类由运行时在 handler 之前判定，handler 不执行。
- 半截输入**不得**降为可捕获的 `invalid_input`：截断是上游资源上限造成的，脚本若能用 `|?` 兜底，就会把不完整数据当正常结果继续处理。需要全量输入时，脚本应调大 `max_output_bytes` 或改用分页工具。
- `invalid_input` 只用于**完整**输入的内容不合法，判定者是 handler：编码、JSON 语法、正则、`json_build` 的键不是 `string`、重复键。
- `constraint` 只用于**值层**：实参值不满足 `ParamConstraint` 或 schema 浅校验。个数（含 `json_build` 的键值成对性）已在加载期报 `arity`，不进入运行时。

## 4. 错误格式

所有错误（加载与运行）使用同一格式：

```
<path>:<line>:<col>: error: <message>
  <label>: <detail>
  Hint: <hint>
```

- `<path>` 是传给 `dsl_exec` 的脚本标识；没有路径时用 `<script>`。
- 行列 1 基；`col` 按 UTF-8 字节计。
- `message` 一行、英文、不超过 120 字符；必须能独立说明“哪里错了”。
- 第二行按类别出现：`Allowed tools:`、`Declared events:`、`Constraint:`、`Available:`。
- `Hint:` 必须给出可直接照做的修法；没有修法时写 `Hint: see <section>`，不得省略。
- 同一次失败只报一个错误（第一个），不做多错误聚合。

示例：

```
src/run.rill:5:10: error: tool 'write' is not allowed by script header.
  Allowed tools: read, grep
  Hint: add 'write' to '# allow:' or use an allowed tool.
```

```
src/run.rill:2:1: error: no '# allow:' header; tools are denied by default.
  Available: read, grep, write, json_parse, get
  Hint: add '# allow: read, grep' (or '# allow: *' with audit) at the top.
```

```
src/run.rill:8:5: error: tool 'read' rejected path '/etc/passwd'.
  Constraint: path must resolve under '/workspace/'
  Hint: use a path under '/workspace/'.
```

```
src/run.rill:3:10: error: '$' used outside 'into' block.
  Hint: wrap the expression in 'into { ... }' to bind '$'.
```

```
src/run.rill:4:1: error: cannot assign to immutable binding 'count'.
  Hint: declare it with 'let mut count = 0'.
```

## 5. 版本策略

- 规范版本仍为 `v0.1`，本轮为 `rev.1`；**不新增其他版本编号**，也不 bump 任何产品版本。
- `# dsl-version:` 在 header 中可选；只接受 `1`，其他值 `E_VERSION` [D-018]。
- 向后兼容：新语法增量添加；旧脚本不写新语法照常跑。rev.1 的默认拒绝发生在首个实现发布前，不属于兼容性破坏（仓库 `.rill`/`.dsl` 计数为 0）。
- 热更新：脚本监听 + 加载校验 + 原子替换 + 自动回滚；策略按 [06 §3](06-security.md) 的快照语义。
- 规范正文的每次改动递增 `rev.N` 并在 [README §3](README.md) 留一行；不移动产品版本号。

## 6. 验收锚点

- [S-020](../S-020-error-format.md)；接口字段由 [S-008](../S-008-capturable-errors.md)、[S-012](../S-012-r4-failure-table.md)、[S-015](../S-015-policy-snapshot.md) 联合验收。
- 本章接口与工具契约 [T-001..T-006](../tools/README.md) 对齐：`requires_complete_input`、`max_input_bytes`、通用 `max_payload_depth`、加载期 `arity` 的落点均在工具条目内给出负例。
