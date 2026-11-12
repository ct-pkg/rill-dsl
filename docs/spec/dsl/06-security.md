# 06 安全

> 规范版本 `v0.1 rev.1`；状态 `unverified`。依据 D-011、D-012、D-013、D-014。

## 1. 三层白名单

| 层 | 时机 | 内容 | 失败 |
| --- | --- | --- | --- |
| 第一层 注册表 | 内核启动 + 加载 | 工具必须在 DSL 可见 `ToolRegistry` 中 | `E_UNKNOWN_TOOL` |
| 第二层 脚本 header | 加载 | 工具 ∈ `# allow:`，事件 ∈ `# emit:` | `E_TOOL_NOT_ALLOWED` / `E_EVENT_NOT_DECLARED` |
| 第三层 参数 | 每次调用前 | `ParamConstraint` 全部通过 | `E_CONSTRAINT`，handler 不执行 |

- 加载期做第一、二层；执行期做第三层。执行期不得重新计算第一、二层集合（见 §3 快照）。
- 三层都通过才调用 handler；任一层失败都不产生副作用。

## 2. 第二层：header 三态与默认拒绝

`# allow:` 只有三种合法状态 [D-011]：

| 状态 | 有效工具集 | 处理 |
| --- | --- | --- |
| 无 `# allow:` | 空 | 加载拒绝 `E_NO_ALLOW_HEADER`，错误列出可用工具与修法 |
| `# allow: a, b` | `{a, b}` | 正常 |
| `# allow: *` | 注册表全集 | 正常，但必须写入一条审计记录 |

补充规则：

- `# allow:` 后列表为空 → 与无 header 同义，拒绝。
- `# deny:` 单独出现（无 `# allow:`）→ `E_DENY_WITHOUT_ALLOW`；不得静默变成空集。
- `# deny:` 优先于 `# allow:`；`# deny:` 里的工具即使不在 allow 也合法（冗余无副作用）。
- header 由脚本作者自书：默认拒绝阻止的是“无意识授权”和“静默扩大”，不阻止作者显式申请危险工具。外部授权主体（`principal_id`/`grant_set`）未定，见 PENDING P-020。
- `# allow: *` 的审计记录字段：脚本路径、内容哈希、`policy_generation`、有效工具数、时间戳。

## 3. 策略快照

### 3.1 结构

```
PolicySnapshot {
  policy_generation: u64
  allow: set<tool_name>
  deny: set<tool_name>
  emit: set<event_name>
  constraints: map<tool_name, ParamConstraint[]>
  constraint_versions: map<tool_name, u32>
  handlers: map<tool_name, (handler_id, version)>
}
```

- 快照不可变；一次 `dsl_exec` 全程只读同一代 [D-012]。
- 加载期集合校验与执行期参数校验使用同一代；不得一边用旧 allow、一边用新 constraint。

### 3.2 热更新

1. 热更新 = 构建新快照 + 原子替换指针；只影响**后续**加载。
2. 进行中的执行不换快照；内核可在“下一次工具调用边界”强杀，返回 `ok=0`、`error_kind=revoked`，已完成步骤的返回值保留。
3. 强杀不打断 handler 内部；边界是“准备发起下一次工具调用之前”。
4. 脚本内容哈希必须等于加载校验时的哈希，否则 `E_SCRIPT_CHANGED`。
5. 策略**扩张**（加工具、放宽约束、加事件）必须有审批记录，否则拒绝加载 `E_POLICY_EXPANSION_UNAPPROVED`；**收缩**只需审计日志。
6. 每次热更新写一条 diff：`gen=N added=[...] removed=[...]`。

## 4. 审批

- 审批 100% 在内核；DSL 没有 `approve` 语句、没有 `# approval:` header、没有审批表达式 [D-013]。
- DSL 侧唯一接口是 `ToolDef.requires_approval`。
- 审批对象：

```
(policy_generation, tool_name, canonical_args_hash, nonce)
```

- 执行前以常量时间复核；参数变化 → `E_APPROVAL_STALE`；重放 → `E_APPROVAL_REUSED`；两者 handler 都不得执行。
- 审批拒绝 → `ok=0`、`error_kind=approval_denied`；需要审批而未获批准 → `approval_required`。脚本不能捕获这两类错误。
- 审批等待不计入 `ExecLimits.timeout_ms`；结果回显 `approval_wait_ms`。
- 同一次执行内按 `(tool, canonical_args_hash)` 缓存审批结果，循环内不重复弹窗。
- 审批理由由内核生成，不接受脚本提供的字符串。
- 无主体时审批只绑定工具与参数，不代表“谁”批准；该缺口见 PENDING P-020。

## 5. 第三层：参数约束分档

### 5.1 路径

工具声明 `path` 类参数时，必须同时满足：

1. 判定对象是解析后的绝对路径（`realpath` 或等价物）。
2. 界内 = 等于 root，或以 `root + "/"` 为前缀；不得用裸字符串前缀（防止 `/workspace-evil`）。
3. 写不存在的文件：解析父目录 realpath，校验 basename 不是 symlink。
4. 判定与打开同源：`openat` 拿 fd，或逐段 `O_NOFOLLOW` 打开；handler 接收已校验的 fd/路径，不得再解析原始字符串。
5. `..` 在 open 前已被消解，不得依赖字符串替换。

夹具（必须全拒/全允）：`/workspace/../../etc/passwd` 拒、`/workspace/link→/etc` 拒、`/workspace/link→/workspace/sub` 允、`/workspace/new.txt` 允、`/workspace-evil/x` 拒。

### 5.2 命令

- exec 类工具参数是 `argv: array<string>`；不存在 `shell: true` 一类开关；不经 shell 解释。
- `argv[0]` 必须是绝对路径且与白名单精确相等（`CONSTRAINT_ARGV0_EXACT`）。
- 额外参数受 `CONSTRAINT_ARGV_PREFIX` / 正则黑名单约束。
- `sh -c`、`bash -c`、`env`、`xargs` 只能出现在专门的高危工具中，且该工具必须 `requires_approval`。
- 管道、重定向、通配符展开不属于 MVP 的 exec 能力。

### 5.3 域名

- host 规范化：小写、punycode、去尾点。
- 匹配按标签边界：精确相等或 `*.example.com` 后缀；禁止子串匹配。
- 仅 `https`；端口必须显式声明；禁止 userinfo；`file://`/`gopher://` 拒绝。
- 重定向逐跳复核，跳数上限必填；DNS 解析一次并钉住结果，不再二次解析；禁止代理自动跟随。

### 5.4 emit 与双通道

- `max_emit_bytes`、`max_payload_depth` 必须落实（[05 §2](05-data-metadata.md)）。
- 约束必须覆盖 `args_json` 与 `ctx_json` 两条通道；隐式 `$` 必须有参数名与约束绑定，否则 `E_UNCONSTRAINED_ARG`。
- args JSON 只解析一次；重复键 → `E_DUP_KEY`。约束看到的对象与 handler 入参是同一份规范化结果。

### 5.5 分档

| 项 | rev.1 状态 |
| --- | --- |
| 路径 canonical + 组件边界 + 父目录 + 打开同源 | 必做 |
| argv + 禁 shell + `argv[0]` 绝对路径 | 必做 |
| 域名规范化 + 逐跳重定向 + DNS 钉住 | 必做 |
| emit 字节/深度上限 + 事件 schema 选入 + `external_egress` | 必做 |
| 双通道约束 + 单次解析 + 重复键 | 必做 |
| 跨 exec payload taint | deferred（P-021） |
| 外部授权主体 `grant_set` | deferred（P-020） |

## 6. 边界：Rill 在 agent 运行时中的位置

**内核所有**：主循环、模型调用、上下文压缩、记忆、自修复、审批、调度、工具注册与策略、订阅方注册。

**DSL 所有**：单次执行的语法与语义（加载、求值、调用、事件发布）。

归属规则（一条，机械可判）：**任何需要“跨语句持久状态”或“挂起后恢复”的能力归内核**。审批、并行调度、重试循环、记忆读写因此全部不在 DSL。

## 7. 验收锚点

- [S-013](../S-013-default-deny.md)、[S-014](../S-014-allow-star-audit.md)、[S-015](../S-015-policy-snapshot.md)、[S-016](../S-016-approval.md)、[S-017](../S-017-path-constraint.md)、[S-018](../S-018-command-domain.md)。
