# B3 安全与边界 — 裁判判决

- battle：B3
- judge：EDITOR
- 立案依据：AGENTS.md §7.2 B-5
- 审理对象：`battle/B3/seats/advocate.md`、`challenger.md`、`pragmatist.md`
- 基线：`rill-dsl` HEAD `033e5860406b91bbf226a5aa42a1818d520d28c0`；`ct-lang` 当前 HEAD `6c21f26d505fff782d4f51e4d20a95f6710794f8`
- 范围：缺省授权、热更新 | 快照 vs 实时、审批归属、参数约束强度

---

## 1. 争点

| ID | 争点 | 席位分歧 |
| --- | --- | --- |
| B3-1 | `# allow:` 缺省默认拒绝还是继承注册表 | 主张席默认拒绝 + `*` 逃生舱；反证席默认拒绝 + 外部 `grant_set`；成本席默认拒绝并要求 deny-only 报错。三席在“默认拒绝”上收敛，差异在“谁能授权” |
| B3-2 | 白名单热更新：快照 vs 实时 | 主张席与成本席选不可变快照；反证席接受快照但要求补 handler 身份、脚本哈希、扩张审批、强杀 |
| B3-3 | 审批放内核还是 DSL | 三席一致内核；反证席要求审批绑定规范化参数哈希与主体 |
| B3-4 | 参数约束强度 | 主张席要求行为级硬化（canonical 路径 + fd 复核、argv、域名规范化、emit 上限）；反证席给出更长的绕过清单并要求更严；成本席主张只先写“argv[0] + 禁 shell + 浅校验”，realpath/TOCTOU 与完整 schema 本期不主张 |

---

## 2. 判据（逐条）

| 争点 | # | 判据 | 判定方式 |
| --- | --- | --- | --- |
| B3-1 | J1 | “缺省”在规范中只有一个表述 | 文本唯一性 |
| B3-1 | J2 | headerless 脚本在**加载期**被拒，错误含位置/可用工具/修法 | 夹具定义 |
| B3-1 | J3 | 规范内示例零误伤；存量脚本迁移成本可核 | 计数 |
| B3-1 | J4 | 逃生舱显式且可审计 | 规则 |
| B3-1 | J5 | `# deny:` 单独出现不得静默变成空集 | 规则 |
| B3-2 | J6 | 一次 `dsl_exec` 的加载期与执行期看到同一代策略 | 快照 |
| B3-2 | J7 | 新策略只对后续加载生效；在飞执行可被有界中止 | 规则 |
| B3-2 | J8 | 工具 handler 身份、脚本内容在本次执行内稳定 | 绑定 + 哈希 |
| B3-2 | J9 | 策略扩张需审批，收缩可只审计 | 规则 |
| B3-3 | J10 | 语法面零审批（无关键字/无 header/无表达式） | 文法 + grep |
| B3-3 | J11 | 审批对象绑定到具体调用参数，不能“批准一次=批准全部” | 审批对象 |
| B3-3 | J12 | 审批等待不计入 `timeout_ms` | 接口 |
| B3-3 | J13 | 边界可机械判定（一条归属规则 + 两张清单） | 规则 |
| B3-4 | J14 | 路径约束不可被 `..`、symlink、兄弟目录绕过 | 夹具五件套 |
| B3-4 | J15 | 命令白名单不依赖 shell 字符串 | argv 模型 |
| B3-4 | J16 | 域名白名单不可被后缀/userinfo/重定向/DNS 重绑定绕过 | 夹具 |
| B3-4 | J17 | emit payload 有字节与深度上限，超限是脚本可见错误 | 接口 + 规则 |
| B3-4 | J18 | 约束覆盖 `args_json` 与 `ctx_json` 两条通道；单次解析 | 规则 |

---

## 3. 主张书（claim.md 索引）

未落盘 `claim.md`；主张以 `seats/advocate.md` 为准（§3–§6 逐条判据 C1.1–C4.6、§7 落点清单）。

## 4. 反证清单（counter.md 索引）

未落盘 `counter.md`；反证以 `seats/challenger.md` 为准（§1 三层断点、§2–§5 攻击矩阵、§6 失效层分布、§7 反向锚点）。

## 5. 出证（核实命令 / 输出 / 环境）

```
$ cd /Users/samxx/trae-ws/rill-dsl && sed -n '55p;205,214p;219p;224p;226,229p;231,243p;249p;252,266p;288,295p;508,512p' docs/design/dsl-spec-v0.1.md
头部元数据在脚本开头，可选。缺省时继承内核默认策略。
5. 三层白名单
5.1 第一层：注册表级（内核启动时确定）
只有注册进 DSL 可见 ToolRegistry 的工具，脚本才能调用。不在注册表的工具，脚本里写出来会报 unknown tool。
（ct 代码块略）
# allow: read, grep, write
· # allow: 缺省时继承注册表级白名单。
· # deny: 优先级高于 allow。
· # emit: 声明脚本能发的事件名，emit 未声明的事件加载时报错。
加载时校验：AST 里调用的工具 ⊆ allow 列表，AST 里 emit 的事件 ⊆ emit 列表。不通过则拒绝加载。
5.3 第三层：参数级（工具 schema 定义）
每个工具可声明参数约束，解释器在调用 handler 前检查：
（ParamConstraint 代码块略）
约束类型：路径前缀、命令白名单、域名白名单、正则黑名单、数值范围。不通过则拒绝调用，handler 不执行。
（三层关系代码块略）
struct ExecLimits { max_steps / max_tool_calls / max_fn_depth / max_emit_count / max_output_bytes / timeout_ms }
· 向后兼容是硬约束：新语法增量添加，旧脚本不写新语法照常跑。
· 热更新：脚本文件监听 + 加载校验 + 原子替换 + 自动回滚。白名单配置热更新需人工审批或审计日志。

$ cd /Users/samxx/trae-ws/rill-dsl && grep -c '缺省时继承注册表级白名单' docs/design/dsl-spec-v0.1.md
1
$ find . -type f \( -name '*.rill' -o -name '*.dsl' \) -not -path './.git/*' | wc -l
0
$ grep -rn 'tool_registry_add' --include='*.md' docs | wc -l
3
$ grep -rn 'tool_registry_add' --include='*.md' . | awk -F: '{print $1}' | sort | uniq -c
   2 ./battle/B3/seats/advocate.md
   1 ./battle/B3/seats/pragmatist.md
   3 ./docs/design/dsl-spec-v0.1.md
$ grep -n '^示例 ' docs/design/dsl-spec-v0.1.md
353/365/377/396/408: 示例 1..5（共 5 个）
$ grep -n '^# allow:' docs/design/dsl-spec-v0.1.md
219, 356, 368, 380, 399, 411

$ cd /Users/samxx/trae-ws/ct-lang && sed -n '1639,1641p' selfhost/ct-ast/frontend/module/Module.h.ct
   `-I ./x`, `a/../b`, or a symlinked root. `realpath` needs the path to exist,
   which import roots and resolved units do; when it fails we keep the spelling
   we were given rather than inventing one.

$ cd /Users/samxx/trae-ws/ct-lang && sed -n '695p;701,721p' selfhost/ct-ast/tool/pkg/Pkg.h.ct
        return system("git --version >/dev/null 2>&1") == 0;
    int sh_quote(const char *s, char *out, size_t cap)
    ...
            w = snprintf(full, sizeof full, "%s > %s 2>/dev/null", cmd, qo);
        return system(full);
```

核实结论：

| 席位声称 | 核实结果 |
| --- | --- |
| 主张席 F1/F2/F3/F4/F7/F8/F9/F10 的 v0.1 行号 | 逐行一致，**成立** |
| 主张席 F5 仓库零 `.rill`/`.dsl` | 计数 0，**成立** |
| 主张席 F6 “§8 **六个**示例全部自带 `# allow:`（356/368/380/399/411）” | **部分失败**：§8 只有 **5 个**示例；`# allow:` 在 §8 出现 5 次（356/368/380/399/411），第 6 次在 §5.2 代码块 L219。结论“示例不误伤”成立，计数错误 |
| 主张席 E1 第 3 行 `grep tool_registry_add *.md = 3` | 在 `docs/` 下为 3，**成立**；全仓现为 6，因席位文件自身命中 3 次（其中本席 2 次、成本席 1 次）。这是计数口径差，不是伪造 |
| 主张席未记录 HEAD sha | 自认；已由本判决补钉 `033e586…` |
| 反证席 F11 CT `realpath` 要求路径存在 | 原文一致，**成立** |
| 反证席 F12 CT 用字符串 `system()` 跑 git 并为引号逃逸写 `sh_quote` | 原文一致，**成立** |
| 反证席 §7 “无 import、无一等函数、无 eval” | 与 v0.1 §9 L427/L430 一致，**成立** |
| 成本席“全仓只有 11 个 `.md`” | 其运行时刻可成立；当前为 20（新增 battle 席位），属**时效性事实**，不影响结论 |
| 成本席“`while≈300/重试≈400/截断≈300/错误升级≈200` 引用” | **未核实**：无锚点 |
| 三席的 LLM 漏 header 率、`*` 占比、TOCTOU 成本（150–250 行） | **未核实**（无实现、无实测） |

E1 继承：

| 席位 | E1 状态 |
| --- | --- |
| 主张席 | 有 3 条文档级命令与输出（`grep -c`、`find`、`grep`），自认无运行期证据、无 HEAD sha |
| 反证席 | **无 E1**，自认“本仓 E1 不可能满足”，全部为条文推导 |
| 成本席 | **无 E1**，E4 为 pre-code 估算 |

---

## 6. 判决（逐条）

| 争点 | verdict | 采纳方案 | 决策记录 |
| --- | --- | --- | --- |
| B3-1 | **upheld**（默认拒绝） | 三态写死：无 header = 拒绝；`# allow: a,b` = 该集合；`# allow: *` = 注册表级等价且必审计。`# deny:` 单独出现 = 加载错误。`# deny:` 仍优先。保留“header 由脚本作者自书”的诚实边界 | D-011 |
| B3-2 | **upheld**（快照） | 不可变 `PolicySnapshot`（policy_gen、allow/deny/emit、约束版本、handler 身份）；一次执行只读同代；热更新换指针、只影响后续加载；下一次工具调用边界强杀；结果回显 `policy_generation`；脚本内容哈希校验；扩张需审批、收缩只审计 | D-012 |
| B3-3 | **upheld**（内核） | DSL 零审批语法；`ToolDef.requires_approval`；审批对象绑定 `(policy_gen, tool, canonical_args_hash, nonce)`，执行前复核，stale/reused 报错；等待不计超时；同次执行按 `(tool,args-hash)` 缓存；边界节 + 一条归属规则 | D-013 |
| B3-4 | **upheld（分档，部分 deferred）** | 必做：路径 canonical + 组件边界 + 父目录解析 + 打开同源复核；argv + 禁 shell + `argv[0]` 绝对路径；域名规范化 + 逐跳重定向复核 + DNS 单次解析；emit 字节/深度上限 + 事件 schema 选入 + `external_egress`；`args_json`/`ctx_json` 双通道覆盖；单次解析、重复键报错。不做：默认严格 JSON Schema（`additionalProperties:false`）。deferred：跨 exec payload taint、主体/`grant_set` 模型 | D-014 |
| 交界 | **undecidable** | 外部授权主体（`grant_set` + `principal_id`）与跨 exec taint | 不写决策记录；见 §9 |

---

## 7. 生效范围

- 约束下一版规范 §5（三层白名单）、§6.1（`ToolDef`）、§6.3（`ExecLimits`）、§6.4（事件总线）与新增“Rill 在 agent 运行时中的位置”一节。
- 不含：并行调度、重试形态、截断语法（分别由 D-009/D-007/D-008 定）。
- 不含：外部授权主体模型与 taint 传播（undecidable，见 §9）。
- 范围外不得引用本判决宣称“安全已验收”。

## 8. 理由（逐条对应判据）

**B3-1**：J1/J2 由“默认拒绝”三态直接满足；J3 有可复核实证：仓库 `.rill`/`.dsl` 计数 0，§8 五个示例全部自带 `# allow:`（L356/368/380/399/411），迁移成本为零。J4 由 `# allow: *` + 审计记录满足。J5 采纳成本席：`# deny:` 单独出现若静默变成空集，是“加载成功但什么都不能用”的最坏误伤，必须报 `# allow:` 缺失。反方最强论点是“改默认值违反 §13 向后兼容硬约束（L510）”；该论点不成立：兼容义务的载体是已存在脚本，实测为 0，且 §13 约束的是“旧脚本不写新语法照常跑”，在首个实现发布前确定安全默认值不属于行为变更。反证席的“header 自授权”我采纳为**诚实边界**写入规范：默认拒绝只阻止无意识授权与静默扩大，不阻止作者显式申请危险工具；真正的修复需要外部授权主体，该部分判 undecidable。

**B3-2**：J6/J7 上，实时查存在两类可推导的缺陷：加载期允许、执行期收紧导致脚本中途失败（半成品状态，R4 只保证块中止不保证回滚）；以及约束版本漂移——加载时 `/workspace`、执行中被放宽为 `/`，脚本获得加载期未审权限（反证席 §3.1/§3.2）。快照把这两类竞态变成“新的加载看新策略、在飞执行看旧策略”，是唯一能同时满足 J6/J7 的结构；成本席的“不可变 Policy 指针交换 40–60 行”给出了最低成本实现。J8 采纳反证席：只做快照不够，工具名在加载期是静态字面量，但 handler 指针可被替换，必须绑定 `(name, generation, handler_id)` 并校验脚本 AST 哈希（`E_SCRIPT_CHANGED`）。J9 采纳反证席的扩张/收缩区分：加工具、放宽约束、加事件是扩张，必须审批；收缩可只写审计，避免“或”字把扩张也放行。反方最强论点是“撤销必须即时，快照等于策略失效”；不成立：即时撤销与“加载-执行原子一致”不可兼得，用“下一次工具调用边界强杀”把延迟从最长 `timeout_ms` 压到一次调用，且选择权在内核而非脚本。

**B3-3**：J10 三席一致；J13 由“跨语句持久状态或挂起后恢复归内核”这一条归属规则满足，审批恰好命中两者。J11 是反证席对主张席的实质补强：工具级审批只暂停不缩小能力，批准一次 `write` 不覆盖任意参数，故审批对象必须含规范化参数哈希与 nonce，执行前常量时间复核，stale/reused 分别报错。J12 由“等待不计入 `timeout_ms`”满足，否则审批延迟会把正常任务判超时。反方最强论点是“内核审批对模型不透明、逐次审批耗尽耐心”；不成立：透明度用 `ToolDef.description` + 首次拒绝文案，耐心用同次执行的 `(tool,args-hash)` 缓存与内核批量授权解决，两者都属内核配置，反而证明不该进 DSL。主体 `principal_id` 与外部 `grant_set` 判 undecidable（见 §9），因为它要求改 `dsl_exec` 签名且无用户拍板；没有主体时审批退化为“对工具名批准”，这一点必须写进规范，不能宣称审批解决了越权。

**B3-4**：J14–J18 是“白名单必须可执行，不能是形容词”。主张席与反证席在攻击面上一致，分歧在成本席的“本期不主张”。我按“必做/不做/deferred”三分：

- 路径：只做字符串前缀可被 `/workspace/../../etc/passwd`、`/workspace-evil/x`、指向 `/etc` 的 symlink 三路绕过（反证席 P-1/P-2/P-3 与主张席 §6.1 同向），且 CT 的 `realpath` 要求路径存在（`Module.h.ct:1639`），写新文件必须解析父目录。故 canonical + 组件边界 + 父目录解析是**最低可主张**；再要求“判定与打开同源”才能堵 TOCTOU。成本席的“本期不主张 TOCTOU 硬化”我拒绝，理由：节点 J14 的判据一旦不含打开时复核，规范写“路径前缀”就是虚假安全；正确做法是规定**可观测行为**（夹具 P-1..P-5 全拒），实现可选 `openat` 或 `O_NOFOLLOW`，不绑死实现。
- 命令：三席一致支持 argv + 禁 shell + `argv[0]` 绝对路径，成本席称其为“唯一更便宜且更好”的选项；CT 自身用字符串 `system()` 并专写 `sh_quote`（`Pkg.h.ct:695,701-721`）正是“名字白名单盖不住参数面”的现成反例，故采纳。
- 域名：反证席 D-1..D-8 的攻击全部成立且规范化成本低（成本席估 15–30 行），采纳规范化、逐跳重定向复核、DNS 单次解析、禁代理。
- emit：`max_output_bytes` 明写“单次工具结果”（L292），不覆盖 emit；深拷贝放大（L194）成立，故新增 `max_emit_bytes`/`max_payload_depth`，超限返回 `ok=0, error_kind=limit`，不得静默丢事件。事件 schema 采用“逐事件选入”，拒绝默认 `additionalProperties:false`（成本席：会把 LLM 常见多余字段变成重试，负收益）。
- 双通道：反证席 §5.5 指出 `ctx_json` 没有参数名，约束引擎看不到 `$`，这是真实缺口，故要求约束覆盖两条通道，隐式 `$` 必须有名字与约束绑定。
- 重复键：`:158` 只做浅校验，约束取第一份、handler 取最后一份会导致“校验对象 ≠ 执行对象”，采纳单次解析 + `E_DUP_KEY`。
- taint：反证席 C8 需要能力标签模型，规范无主体也无 taint 设计，判 undecidable，不写成规则。

## 9. 失效条件与 undecidable 的重开条件

| 项 | 状态 | 重开条件 |
| --- | --- | --- |
| 默认拒绝 | 失效条件：出现任一外部方按 v0.1 写的 headerless 脚本需要继续运行；或实测 LLM 漏 header 率高到每次任务多 ≥2 次往返 | 重开 B3-1，评估“告警过渡 + `# dsl-version` 分支”，不得直接恢复“继承注册表”为缺省 |
| 快照 | 失效条件：运维要求撤销必须即时生效，且强杀实现成本高于“实时查 + 每步重校验” | 重开 B3-2（C2.1/C2.3 让位），但必须保留 handler 身份与脚本哈希绑定 |
| 审批在内核 | 失效条件：出现必须“执行中阻塞等待人工确认”的真实流程 | 重开 B3-3，评估 `approval_required` + 内核重跑，而不是 DSL 内暂停 |
| 参数硬化 | 失效条件：workspace 为 symlink 挂载且无法在根上解析，导致五件套系统性误杀 | 重开路径规则，但“解析后仍在界内即可”的口径不变，不得退回字符串前缀 |
| 主体 / `grant_set`（undecidable） | 需要 `dsl_exec` 增加 `principal_id` 与外部授权集，属内核接口变更且无用户拍板 | 重开条件：首次多租户部署，或内核接口 CR 明确 `dsl_exec` 主体字段；届时按“header 是能力请求、外部集是授予”重建 B3-1 |
| 跨 exec payload taint（undecidable） | 需要能力/污点标签模型，规范无主体、无标签 | 重开条件：启用外部 webhook 订阅方，或发生一次“低权脚本经事件把数据送入特权工具”的事件 |

## 10. 影响面

| 对象 | 影响 |
| --- | --- |
| 决策记录 | 新增 D-011..D-014；主体/taint 不建记录 |
| PENDING | P-005、P-006、P-015 定稿；新增 P-020（外部授权主体）、P-021（跨 exec taint）为 pending |
| 接口 | `ToolDef` 增 `requires_approval`；`dsl_exec` 增策略快照与 `policy_generation` 回显（主体字段待定）；`DslResult` 增 `error_kind`/`degraded`/`policy_generation` |
| 门禁 | M8 需补：headerless 拒绝、deny-only 报错、`*` 审计、快照跨代、强杀、路径五件套、argv 拒绝、域名八例、emit 超限、双通道、重复键 |
| 版本号 | 无产品版本号，不 bump |
| ct-lang | `realpath` 要求路径存在、字符串 `system()` 两个事实用于反证，不作为“复用 CT 安全能力”的依据 |
