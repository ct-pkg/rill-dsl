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
    int   requires_approval;
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

## 2. ExecLimits

```ct
struct ExecLimits {
    int max_steps;             // 语句 + 每次循环迭代
    int max_tool_calls;
    int max_fn_depth;
    int max_emit_count;
    int max_output_bytes;      // 单次工具 payload 的最大字节数（不是整个 DslResult）
    int max_emit_bytes;        // 单条 emit payload 序列化后的最大字节数
    int max_payload_depth;     // emit payload 最大嵌套深度
    int timeout_ms;            // 不含审批等待
};
```

- 超限一律 `ok=0`、`error_kind=limit`；`max_emit_bytes`/`max_payload_depth` 的失败位置在 emit 语句。
- rev.1 基线默认值（内核可覆盖）：`max_steps=10000`、`max_tool_calls=200`、`max_fn_depth=8`、`max_emit_count=100`、`max_output_bytes=262144`、`max_emit_bytes=65536`、`max_payload_depth=8`、`timeout_ms=30000`。
- 计数口径：语句执行 +1；循环每次迭代至少 +1；`continue` 不重置；`|?` 右侧执行照常计数。

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
| `unknown_tool` | 调用未注册工具 |
| `tool_not_allowed` | 工具不在 `# allow:` |
| `event_not_declared` | emit 未在 `# emit:` 声明 |
| `unknown_callee` | 调用既非工具也非 `fn` |
| `undefined_name` | 引用未定义名字 |
| `bare_fn_ref` | 有参 `fn` 被当裸名引用 |
| `shadow_tool` | 局部绑定/参数/`fn` 与工具同名 |
| `dup_decl` | 同作用域重复声明 |
| `assign_undefined` | 赋值目标不存在 |
| `immutable_assign` | 对不可变绑定/参数/循环变量/`$` 赋值 |
| `loop_control` | `break`/`continue` 不在 `for` 内 |
| `return_outside_fn` | `return` 不在 `fn` 内 |
| `recursion` | 调用图有环 |
| `arity` | `fn` 实参个数不符 |
| `not_implemented` | `par` 等已保留但 MVP 不实现的语法 |
| `pipe_rhs` | `\|>` 右侧不是调用 |
| `fallback_lhs` | `\|?` 左侧不是单个调用 |
| `dup_key` | emit payload 重复键 |
| `script_changed` | 执行期脚本哈希与加载期不一致 |
| `policy_expansion_unapproved` | 策略扩张未审批 |

### 3.2 运行期 `error_kind`

`not_found`、`invalid_input`、`transient`、`denied`、`constraint`、`approval_required`、`approval_denied`、`approval_stale`、`approval_reused`、`limit`、`revoked`、`internal`、`type`、`emit_schema`、`for_not_array`、`unconstrained_arg`、`condition_not_bool`。

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
