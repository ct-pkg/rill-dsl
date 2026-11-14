# RILL 0.1.0 阶段计划（phase 7–12）

> 本文件续 [rill-0.1.0-phase-plan.md](rill-0.1.0-phase-plan.md)；phase 1–6 留在主文件。

## phase 7：简单语句、尾随块与段输出（Runtime 轨）

**目标**：实现 `simple_stmt` 的完整执行：`[into]` → `[ok]/[error]` → 段输出 → `|>` 下游。

**依赖**：phase 6；phase 3 的 AST；phase 4 的表只读接口。

**产出物**：

- `src/runtime/eval-simple`；
- 段输出轨迹测试；
- `[into]` 失败/`[error]`/多 `[into]` 的执行 golden。

**工作项**：

1. `[into]` 按书写顺序执行，修改 `$`；后续 `[into]` 看到前一个的结果（0.1.1 §4.11）。
2. `[into]` 失败：视为段失败，走用户 `[error]`；无 `[error]` 默认 break；后续 `[into]` 不执行（评审 I-14/R-26）。
3. `[ok]/[error]` 在 `[into]` 之后按 `ok` 触发；`[ok]` 看到最终值，`[error]` 看到错误串（0.1.1 §4.10/§4.11）。
4. 段输出 4 种：成功无 `[ok]`、成功有 `[ok]`、失败无 `[error]`、失败有 `[error]`（评审 I-27/I-28/I-30）。
5. `[into]` 的三种形式：尾随、普通介词、独立 `prep_block_stmt`（评审 I-08/I-09）。
6. `->$x` 与尾随块的书写顺序：先赋值再进入块，还是先块后赋值，按 AST 顺序执行（评审 R-25）。

**退出判据**：

- 4 种段输出各 1 个 golden；
- `[into]` 失败 + 用户 `[error]` 的执行轨迹唯一；
- 多 `[into]` 失败时后续不执行；
- `[ok]` 的 `$` 是最终值，`[error]` 的 `$` 是错误串；
- `|>` 下游只收到 value，`ok` 不向下传。

**不做什么**：不实现 `if/each/parallel` 的控制流，只做单语句。

**已知坑**：评审 I-27/I-28（段覆盖 vs 整条管道）、I-30（`[ok]` 输出通道）、R-08（无介宾语句的 `$`）。

---

## phase 8：管道、`if`、`each`、`break`（Runtime 轨）

**目标**：把单语句组合成管道和控制流；`|>` 只传 value；`if` 用 truthy；`each` 产数组并处理失败；`break` 按场域中断。

**依赖**：phase 7；phase 3 的 AST。

**产出物**：

- `src/runtime/eval-control`；
- 管道/if/each/break 轨迹 golden；
- each 失败元素 `null`、结果数组长度 = 轮数的测试。

**工作项**：

1. `|>`：段间只传 value；下游失败不回溯上游；折行时 `|>` 在前段行尾（0.1.1 §4.6；评审 I-26/I-38）。
2. `if/else-if/else`：条件 `expr` 无尾随块；truthy/falsy；`if` 不参与管道（0.1.1 §4.12）。
3. `each`：`null` → error/零次；数组 → 遍历；非数组 → 单元素一次（0.1.1 §4.13；评审 I-13）。
4. each 每轮 `{value, ok}`：成功元素 = value；失败未处理 = `null`，循环继续；`[error]` 处理且未 break = 处理后 value。
5. each 级 `[ok]`（全部成功）/`[error]`（首个失败）与 `$` 指代（评审 R-09）。
6. `break`：顶层/管道/块三种场域；`break <值> -> $var`；无捕捉则丢弃（0.1.1 §4.15；评审 I-15/I-16）。

**退出判据**：

- 管道 3 段以上，每段 `[error]` 只覆盖本段；
- `if` 的 truthy/falsy 与 `[ok]` 的 `ok` 分离；
- each 空数组 0 次、null 0 次、非数组 1 次；
- 某轮失败后循环继续，结果数组对应位为 `null`；
- `break` 在 `[ok]/[error]` 内只中断当前场域；带值 break 可被外部变量捕捉。

**不做什么**：不实现 `parallel`/`[results]`/`//fn` 调用。

**已知坑**：

- 裸词 value 按 A2 合法：`each $f [in] xs` 可直接作为退出用例，语义为字符串单元素数组；`W-01` 只提示不报错。
- 评审 I-19/C-11：each 每轮是否新作用域；phase 8 必须固定“每轮块实例”并写测试，不能留给实现者。
- 评审 I-24/R-07：`$` 在 each 体内是当前项，不被 `[in]` 的宾语覆盖。

---

## phase 9：`parallel`、`[results]` 与 `//fn` 函数（Runtime 轨）

**目标**：实现并行分支的结果汇合与函数调用；这是 0.1.1 相对旧稿新增的两块，也是评审里争议最多的两块。

**依赖**：phase 8；phase 4 的 map/fn 表。

**产出物**：

- `src/runtime/eval-parallel`、`src/runtime/eval-fn`；
- 分支三态（成功/未处理失败/已处理失败）golden；
- 函数去重参数、默认值、返回值的 golden。

**工作项**：

1. `parallel`：分支内 `$` = 当前分支块输出；分支 `[ok]/[error]` 只覆盖本分支；`[into]` 按分支内顺序（0.1.1 §4.14；评审 R-12）。
2. 结果数组：按源序，长度 = 分支数；成功 = value；未处理失败 = `null`；已处理失败 = 处理后 value（评审 I-18/R-13）。
3. `[results]`：只在 parallel 块级；全部完成后触发一次；`$` = 结果数组；块输出 = `[results]` 的 `$`，未写则默认数组；`[results]` 永远触发，不携带状态字段。
4. `//fn`：按名字精确匹配；参数位 = 模板 `$变量` 去重后首次出现顺序；同名出现处绑同一实参；默认值仅尾部；模板不带尾随块。
5. 调用：`call_stmt := "@" STRING arg* trailing_block* [|> simple_stmt]`；`arg := value`；函数体最后一条语句的段输出为返回值；未声明函数加载期报错（评审 I-49/R-14..R-17）。
6. 多分支同时失败：按源序取第一个失败分支的错误串（0.1.1 §4.14；评审 I-18）。

**退出判据**：

- 分支三态数组顺序与长度正确；
- `[results]` 在非 parallel / 分支内出现时解析期报错；
- 函数去重参数：模板 3 处 `$path` 只收 1 个实参；默认值只允许尾部；中间缺省报错；
- 未声明函数、错误参数个数有稳定错误码；
- 函数返回值为最后一条语句段输出。

**不做什么**：不做真实并发调度/取消；`parallel` 先按“逻辑并行、顺序可观察”实现，调度器留给宿主。

**已知坑**：

- 评审 R-16：返回值“最后一条语句结果或 `$` 最终值”的二选一；phase 9 必须选“最后一条语句段输出”，并在 golden 固化。
- 评审 R-17：函数签名不匹配主语/宾语槽；phase 9 只做名字 + 位置绑定，不把 VerbRegistry 的 SVO 绑定混进来。
- 评审 R-12：分支内 `$` 不是最终数组，避免执行中成环。
- `<` 标记 map 表按 B1 正常：`<r>` 到 `<read>` 的等价用例纳入正常正例，不再放 pending。

---

## phase 10：Shell 宿主能力层（Host 轨）

**目标**：在 Mac 上把 0.1.1 当脚本语言跑起来；实现真实 OS 能力，但不改语法、不改 parser、不改求值规则。

**依赖**：phase 6 的 `Value`/`ExecOutcome`、phase 1 的 `HostCapabilities`/`HostProfile`。

**产出物**：

- `src/host/shell`：`ProcessCapability` / `FsCapability` / `EnvCapability` / `StdioCapability` / `ExitCapability` 的 OS 实现；
- `rill run --profile shell <file>`；
- `testdata/0.1.0/host/shell/`：进程、文件/路径、env、stdin/stdout、退出码五类 fixture；
- `docs/planning/rill-0.1.0-shell-profile.md`：能力清单、manifest/CLI 形态、与 Agent 形态的对照。

**工作项**：

1. **进程调用**：spawn/exec；argv、cwd、env、timeout；捕获 stdout/stderr；返回 `ProcessResult{code, stdout, stderr}`。
2. **文件与路径**：read/write/stat/list（如需）；相对/绝对路径、cwd、`..` 消解、符号链接、权限错误；不把 workspace root 强加给 Shell。
3. **环境变量**：子进程继承/覆盖；读取当前 env；进程级隔离，不做全局可变环境。
4. **标准输入输出**：stdin 作为 `Value`（文本或 `Bytes`）；stdout/stderr 捕获为值；重定向由进程能力表达，不借用 `|>`。
5. **退出码**：成功 0；`ok=false` 且未处理 → 非 0；`[error]` 处理后按宿主策略；只实现映射钩子，不在 DSL 写死数字。
6. **Shell 动词**：注册 `run`/`read`/`write`/`env` 等能力动词；动词名是宿主注册表内容，不是新语法；parser 不感知。
7. **双 profile 一致性**：同一份 fixture 在 shell profile 与 agent profile 下 AST 必须相等；只比较能力结果时标注 host-specific。

**退出判据**：

- 五类能力各有至少 1 个成功 + 1 个失败 fixture；
- `ProcessResult.code/stdout/stderr` 可观察；stdin 文本与二进制各 1 例；
- 顶层未处理失败产生非 0 退出码，具体码由 profile 表给出；
- 同一 fixture 的 AST 与 agent profile 相等；
- 没有 parser/lexer 改动（git diff 不含 phase 2/3 路径）。

**不做什么**：不新增 `|>` 的 OS 管道语义；不把 shell 变量/展开/通配符写进 DSL 语法；不做 Windows；不做信号/流式/PTY。

**已知坑**：

- 0.1.1 §4.6 的 `|>` 是 DSL 值管道，不是 OS 管道；Shell 用户会误用。phase 10 必须在文档和错误提示里区分，OS 管道走 `ProcessCapability`（stdin/stdout）。
- 0.1.1 §4.10 的 `[error]` 只有字符串；退出码/stderr 不能塞进 `$` 字符串，必须走 `ProcessResult`/`ExecOutcome.host_meta`。
- 0.1.1 §4.16–§4.17 的值模型没有二进制/流；phase 10 依赖 phase 6 的 `Bytes/Opaque`，否则只能有损编码。
- 0.1.1 §五.1 “脚本无权声明授权”与 Shell 能力声明冲突；phase 10 用外部 manifest/CLI profile，不改脚本语法（roadmap §3.3.3）。
- 0.1.1 §4.1 的“角色 + 权限”是 Agent 形态；Shell 用 OS 用户，phase 4 的 `principal` 必须允许 role 为空。

---

## phase 11：智能体宿主能力层（Host 轨）

**目标**：把现有工具/角色/limits 映射到同一 `HostCapabilities`，证明两个宿主只差能力层。

**依赖**：phase 10 的接口与 Shell 实现、phase 4 的 HostProfile 校验；可与 phase 9 并行。

**产出物**：

- `src/host/agent`：工具注册表 → 能力适配、角色/principal、ExecLimits；
- `rill run --profile agent <file>`（fake 工具）；
- `testdata/0.1.0/host/agent/`：与 Shell 同源的 fixture + agent 专属能力 fixture；
- `docs/planning/rill-0.1.0-host-matrix.md`：五类能力在两种宿主下的形态与差异。

**工作项**：

1. **进程调用**：映射为 `run`/`exec` 工具；不直接 spawn；返回 `{value, ok}`，`ProcessResult` 作为工具值。
2. **文件与路径**：映射为 `read`/`write` 工具；workspace root + path constraint；越界是工具错误，不是 OS 错误。
3. **环境变量**：映射为内核配置/上下文注入；不暴露任意 env 读写。
4. **标准输入输出**：工具返回值、`send`/emit 通道；没有 OS stdin/stdout。
5. **退出码**：不产生 OS 退出码；`ok=false` 映射为工具错误/DslResult；`ExecOutcome.exit_code` 为空或宿主内部码。
6. **角色/limits**：Agent profile 提供 Role/Verb/Type 表与 ExecLimits；Shell profile 的 role 可空。
7. **双 profile 对照**：同一 fixture 两边 AST 相等；能力差异只出现在结果，不出现在语法/AST。

**退出判据**：

- Agent profile 能跑完与 Shell 同源的 fixture；AST 相等；
- 能力矩阵五类各有 Shell/Agent 两列，差异有文字说明；
- `[error]` 仍只拿字符串；结构化错误走 `host_meta`/工具值；
- 没有 parser/lexer 改动。

**不做什么**：不接生产工具/安全策略；不做真实审批/白名单；不实现真实并发调度；不把 agent 的 role 语义带回 parser。

**已知坑**：

- 0.1.1 §4.1 的 role/permission 是 Agent 专属；phase 11 不能把它变成所有宿主的必选。
- 0.1.1 §4.10 的 `[error]` 字符串不足以表达工具错误结构；phase 11 用 `host_meta`，不改 `$` 的规范语义。
- 0.1.1 §五.6 “DSL 不做调用绑定”与函数调用绑定（§4.18）并存；phase 11 只做工具侧绑定，函数绑定仍在 phase 9。

---

## phase 12：CLI、全样例与 golden 集成

**目标**：把 Parser/Runtime/Formatter/Host 串成可运行 CLI，在 Shell 与 Agent 两个 profile 上跑 0.1.1 全样例，给出通过数、host-specific 差异与 pending 清单（本轮为空）。

**依赖**：phase 4、phase 5、phase 9、phase 11。

**产出物**：

- `rill parse` / `rill check` / `rill run --profile shell|agent` / `rill fmt`；
- `docs/planning/rill-0.1.0-acceptance.md`：通过/失败/pending/host-specific 四类清单；
- `docs/planning/rill-0.1.0-host-matrix.md`：五类能力在两种宿主下的验收结果；
- CI 入口 `tools/check-0.1.0.sh --all`；
- 一份“已知限制”清单（生产工具/权限未接、并发未调度、pending 为空）。

**工作项**：

1. CLI 统一参数、退出码、错误输出格式；解析/加载/运行错误分层。
2. 正例端到端运行；负例只跑解析/加载；本轮无 pending，报告显式写 0。
3. 压缩↔展示 round-trip 纳入门禁。
4. 双 profile 对照：同源 fixture 的 AST 逐节点相等；运行结果按能力矩阵比较。
5. 把评审 I-01..I-51 中已闭合的条目对应到至少 1 个 fixture；未闭合/待裁定的列在“已知限制”。
6. 更新 `docs/planning/rill-0.1.0-roadmap.md` 的阶段状态（只改状态，不改范围）。

**退出判据**：

- 全部正例通过；负例全部按预期错误码失败；
- `xfail-pending` 数量为 0（A2/B1 已裁定，roadmap §7）；
- round-trip 全绿；
- 同一 fixture 在 shell/agent profile 的 AST 相等；host-specific 差异全部有记录且不影响语法；
- `tools/check-0.1.0.sh --all` 退出 0；
- 不修改 0.1.1 正文；任何规范改动有 CR 记录。

**已知坑**：

- 报告必须同时给通过数与 pending 数；本轮 pending 为 0，仍需显式写出。
- 旧 `docs/examples/` 不能作为 0.1.1 验收输入；如需借用场景，先改写为 0.1.1 语法并进 `testdata/0.1.0/`。
- Shell 侧是真实 OS 能力，Agent 侧是 fake 工具；phase 12 验证“同一语法/同一 AST”，不宣称两边能力等价，也不验证生产安全策略。
