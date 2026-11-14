# RILL 0.1.0 阶段计划

> 配套 [roadmap](rill-0.1.0-roadmap.md)。每个阶段按单人约一周工作量切分；只写工作内容、产出物、退出判据和依赖，不承诺日历。编号是阅读顺序，不是执行顺序；可并行关系见 roadmap「编号说明」。
> 规范依据：[RILL 0.1.1](../RILL-0.1.0.md)；评审依据：`docs/review/`。阶段中的“已知坑”直接来自评审记录，不另行发明。
> 双宿主是硬约束：Parser/Runtime 不感知宿主；Shell 宿主能力单独成 phase 10（不是脚注），Agent 宿主能力成 phase 11；两者共用同一份语法、同一个 parser、同一套 AST。

## phase 1：基线、样例与门禁骨架

**目标**：把“规范文本”变成可重复执行的验证输入；在写任何 parser 之前，先有样例、AST 形态、双宿主能力接口和失败命令。

**依赖**：无。

**产出物**：

- `docs/planning/rill-0.1.0-implementation-decisions.md`：实现语言、仓库落点、CLI 形态、AST 序列化格式、错误码表；
- `docs/planning/rill-0.1.0-host-contract.md`：`HostCapabilities`（process/fs/env/stdio/exit）、`HostProfile`、`ExecOutcome`、`Value::Opaque/Bytes`、`ProcessResult` 的接口与“现在留/可推迟”清单；
- `testdata/0.1.0/positive/`、`negative/`、`pending/`：至少 12 个正例（覆盖 §三 全部语句形态）、10 个负例、0 个 pending 目录（A2/B1 已裁定；目录保留为空）；
- `testdata/0.1.0/host/`：至少 1 个 shell profile fixture、1 个 agent profile fixture，二者源码相同、AST 必须相同；
- `tools/check-0.1.0.sh`：跑 token/AST/运行/round-trip/双 profile 的门禁入口；在实现不存在时退出非 0，并打印“not implemented”；
- `testdata/0.1.0/expected/`：token/AST golden 的空壳与格式说明。

**工作项**：

1. 从 0.1.1 正文逐节抽取样例清单：header、simple_stmt、if、each、parallel、break、call、map、fn、quotes、display。
2. 重写样例，不复用 `docs/examples/` 的旧语法（旧样例使用 `let`/`fn`/`|?`/`# allow:`，不是 0.1.1）。
3. 固定 AST 序列化（节点类型、字段、span 是否入 golden）；固定 token 格式。
4. 建 fake 工具的最小契约：`read` / `write` / `search` / `parse` / `send` / `replace`，只返回可编程的 `{value, ok}`。
5. `pending/` 目录保留为空；A2/B1 已裁定，不再登记裸词或 `<` 标记用例。
6. 冻结双宿主接口：`HostCapabilities`、`HostProfile`、`ExecOutcome`、`ProcessResult`、`Value::Opaque/Bytes`；写清“现在留的口子”与“可推迟项”（roadmap §3.3）。
7. 在 CI 加 parser 纯度检查：phase 2/3 的 import 图不得出现 host/process/fs/role 模块。

**退出判据**：

- `tools/check-0.1.0.sh --list` 能列出全部 fixture，正例/负例/pending 数量达标；
- 每个 fixture 有 `expect` 说明（token/AST/run/error/host）；
- 同一份 host fixture 在 shell/agent 两个 profile 下 AST 相等；
- phase 1 的 lexer 尚未实现时，门禁以“not implemented”失败，而不是静默通过。

**已知坑**：仓库没有 0.1.1 样例集、没有 harness、没有 fake 工具；这一步不能用旧样例冒充。评审 I-01..I-51 中的“样例需要但规范没有”的条目（如 I-37/I-38）在这里转成 fixture 名称，后续阶段逐条销账。0.1.1 正文的宿主冲突（角色/退出码/错误串/二进制值）在 host-contract 中逐条登记，见 roadmap §3.3.3；phase 1 不擅自改规范。

---

## phase 2：词法（Parser 轨）

**目标**：把 0.1.1 源文本切成稳定 token；只做词法，不做 AST、不执行。

**依赖**：phase 1 的 harness、token 格式、CLI 骨架。

**产出物**：

- `src/lexer`（语言按phase 1 选型）；
- `rill tokenize <file>`；
- `testdata/0.1.0/expected/tokens/*.json`；
- 词法错误码表（未闭合引号、非法转义、`E-01` map_entry 标记符非法、`E-02` 动词未闭合、`//` 头歧义等）。

**工作项**：

1. 符号扫描：`<> () [] -> {} $ |> @ ?`、`//`、引号、反斜杠。
2. 关键字：`if` / `else` / `else-if` / `each` / `parallel` / `break`；语句起始位置优先于主语（评审 I-01/I-02/I-03）。
3. `//` 头：按 §3.1 跳过零个或多个空格；`//map{`、`//map {`、`// map {`、`//fn {` 产生 `MAP_HEADER` / `FN_HEADER`；`//map` 无 `{` 为行注释。
4. `map_entry`：块内每行按 `短词 + 第一个非短词字符（标记符）+ 行尾（长词）` 切分，不启动动词扫描；标记符仅 `'` / `` ` `` / `<`；`p'a"b` 切为 `p` / `'` / `a"b`，`r<read` 切为 `r` / `<` / `read`（§3.2）。
5. 引号：单引号纯字面；双引号仅 `\"` `\\`；裸词转义。
6. 零空格扫描：符号即边界；`else-if` 是单个关键字。

**退出判据**：

- 全部 token golden 通过；
- `//map {` 不被当注释；`//map` 无 `{` 被当注释；
- `p'a"b`、`s'my application`、`cfg`configuration`、`r<read` 的切分符合 §3.2；
- `E-01`（非法标记）与 `E-02`（正文未闭合动词）各有 1 个负例；
- 非法输入有稳定错误码和行列号。

**不做什么**：不解析语句结构，不建 map/fn 表，不执行；**不 import 任何宿主模块**（process/fs/env/role/tool），token 层不认识“agent”或“shell”。

**已知坑**：

- `//map` 标记符 `<` 按 B1 行模式处理（roadmap §7.2）：map 块内 `<` 优先作标记符；非法标记报 `E-01`。`<` 标记的 map_entry 与 `<r>` 展开纳入正常正例，不再放 `pending/`。
- 评审 R-18（短词含空格）、R-20（长词前缀）在 phase 2 先以负例固化，不等到 phase 5。
- 双宿主：`//map`、引号、类型前缀的 token 化必须与宿主无关；任何“agent 才用”的 token 不允许出现在 lexer。

---

## phase 3：语法与 AST（Parser 轨）

**目标**：按 §三 产生式构建完整 AST；只解析，不校验注册表、不执行。

**依赖**：phase 2 的 token 流与关键字。

**产出物**：

- `src/parser`；
- `rill parse --dump-ast <file>`；
- `testdata/0.1.0/expected/ast/*.json`；
- 解析错误码（缺 block、`[results]` 误用、`@` 定义出现在正文、map 行结构错误等）。

**工作项**：

1. `program := header* statement*`；`header := map_block | fn_block`。
2. `statement := simple_stmt | prep_block_stmt | if_clause | each_clause | parallel_clause | break_stmt | call_stmt`。
3. `verb_call := [subject] <动词> 宾语 [(状语)] prep_phrase*`：恢复可选主语，覆盖 `if $cfg <contains> debug=true`（评审 I-04/R-24）。
4. `prep_block_stmt := "[" ("into"|"ok"|"error") "]" ($变量 | verb_call) block`：独立形式语句（评审 R-03/I-09）。
5. `prep_phrase*`：支持多个介宾短语（评审 R-01）。
6. `call_stmt := "@" STRING arg* trailing_block* [|> simple_stmt]`，`arg := value`（评审 R-14/R-17）。
7. `parallel_clause := "parallel" "{" branch* "}" ["[results]" block] [|> simple_stmt]`；分支尾随块限 `[ok]/[error]/[into]`（评审 R-02/R-12）。
8. `[into]` 的 `]` 归约：尾随形式 `{`、普通介词、独立形式三分（评审 I-08/I-09）。
9. `trailing_block` 数量：`[ok]` 0..1、`[error]` 0..1、`[into]` 0..N；重复 `[ok]/[error]` 解析期拒绝（评审 I-29/R-05）。

**退出判据**：

- 全部正例 AST golden 通过；
- `each $f [in] xs`、`break done`、`@ "f" bare` 可归约，裸词在 AST 中为字符串值节点；
- `if $cfg <contains> debug=true` 可归约；`@ "f" "a"` 可归约；`[into] $cfg {}` 可归约；`parallel { ... } [results]{} |> ...` 可归约；
- 负例：`[results]` 出现在非 parallel、`@` 定义形状出现在正文、重复 `[ok]`、缺 block，全部有稳定解析错误；
- 每个语句形态至少 1 个 AST golden。

**不做什么**：不做名字/类型/角色校验，不执行，不做展示格式化；**不把“角色/工具/权限”写进 AST 语义**，主语只保留语法槽。

**已知坑**：

- 裸词 value 已按 A2 裁定（roadmap §7.1）：`value := ... | 裸词 | ...`，裸词按 `STRING` 处理；`each $f [in] xs`、`break done`、`@ "name" bare` 纳入正常正例，不再放 `pending/`。
- 评审 R-10（each 头表达式后的尾随块与 body 切分）：`each` 头 `expr` 不含尾随块，后面的第一个 `{` 必须是 body；用 golden 固化。
- 评审 R-25（`->$x` 与尾随块顺序）：AST 必须保留书写顺序，不能在解析期重排。
- 双宿主：`subject` 只解析为 `role | 裸词 | 引号 | $变量` 四种语法形态，不在 AST 里区分“这是 agent 角色还是 OS 用户”；这一步留给 phase 4 的 HostProfile。

---

## phase 4：加载期校验与诊断（Parser 轨）

**目标**：在 AST 之后、执行之前，完成 map/fn 表、名字、默认值、角色/类型前缀的校验；不执行。

**依赖**：phase 3 的 AST 与错误位置。

**产出物**：

- `src/loader`；
- `rill check <file>`；
- `testdata/0.1.0/expected/errors/*.json`（错误码、行/列、消息）；
- `MapTable` / `FnTable` / `VerbTable` / `TypeTable` / `HostProfile` 的数据结构说明（Agent profile 提供角色/工具；Shell profile 提供 OS 用户/路径/进程能力）。

**工作项**：

1. `//map`：短词字符集、标记符合法（非法报 `E-01`）、同块重复短词报错、跨块可见链最近绑定、长词唯一/反向映射（评审 R-21/R-22）。
2. `//fn`：函数名精确匹配、模板 `$变量` 去重顺序、默认值仅尾部、同块重复函数名、未声明函数调用。
3. 调用：`arg := value` 的实参个数与默认值展开；与 VerbRegistry 的 SVO 槽映射分开（评审 I-37）。
4. 类型/角色前缀 `类型:值` 的加载期拆分与校验（0.1.1 §4.1、§五）；角色不是必填：Shell profile 用 OS 用户，Agent profile 用角色表。
5. `[results]` 只允许 parallel 块级；`[ok]/[error]` 数量上限。
6. 未知介词、未知动词、未声明函数的报错阶段：解析期 vs 加载期（0.1.1 §五.8）。
7. HostProfile：capabilities 声明（Shell：manifest/CLI；Agent：角色/工具/limits）；脚本不可声明；profile 差异不得改变 AST。
8. `W-01`：`each` 的 `[in]` 位为裸词时输出警告，不报错；与 0.1.1 §4.20 的错误/提示表一致。

**退出判据**：

- 正例全部 `check` 通过（`--profile shell` 与 `--profile agent` 各跑一遍，共享 fixture 的 AST 相等）；
- 负例全部有稳定错误码，且行/列指向具体成分；
- `W-01` 在 `each $f [in] xs` 上触发且不阻断 `check`；`E-01` / `E-02` 有稳定错误码与行列号；
- map/fn 表可被 phase 9 以只读接口消费；
- 不执行任何工具。

**不做什么**：不做运行期 `{value, ok}`，不做段输出；**不把 RoleRegistry 写成 loader 的必选依赖**，否则 Shell 宿主无法通过校验。

**已知坑**：

- 评审 I-37/R-28：调用绑定不能塞进 parser；phase 4 只定义表与校验，绑定在 phase 9。
- 评审 R-23：`.env` 作宾语 vs `.host` 作 self 字段；phase 4 的 TypeRegistry 不把 dotfile 当字段。
- 0.1.1 §4.1/§五 的“角色 + 权限”是 Agent 形态；phase 4 必须抽象成 `principal`，Shell profile 映射为 OS 用户，不能把 role 设成必填（roadmap §3.3.3）。
- `//map` `<` 标记按 B1 行模式正常校验；phase 4 对 `<r>` 展开的 map 表项做通过声明。新增 `W-01`：`each [in]` 裸词提示，归 phase 4。

---

## phase 5：展示/压缩互转与回读（Parser 轨）

**目标**：实现 0.1.1 §4.16–§4.17 的双向转换；输入 AST，输出压缩态/展示态文本，并保证回读 AST 等价。

**依赖**：phase 3 的 AST、phase 2 的 token 规则；可与 phase 7/8/9 并行。

**产出物**：

- `src/formatter`；
- `rill fmt --compress` / `rill fmt --display`；
- property test：压缩→展示→压缩、展示→压缩→展示；
- 长词/转义/映射表的 golden。

**工作项**：

1. 压缩：去空白（引号内保留）、展开/收缩 map、值类映射归约为 `STRING` 节点（0.1.1 §4.17）。
2. 展示：加空格、按块缩进、尾随块同一行；值类长词按需加双引号并转义（`a"b` → `"a\"b"`，`my application` → `"my application"`；无特殊字符则原文）。
3. 可逆性：同一长词只对应一个短词；可见链最近绑定；反向映射从内到外取首个命中（评审 R-21/R-22）。
4. 引号/转义：单引号不转义；双引号仅 `\"` `\\`；裸词转义序列保留（评审 I-35）。
5. map/header 在展示态的位置；`//map {` 空格容忍（0.1.1 §3.1）。

**退出判据**：

- 压缩→展示→压缩的 AST 在忽略 span 后相等；
- 含空格长词、含 `"` 长词、含 `'` 长词、`'`/`` ` ``/`<` 三类标记各有 golden；
- 展示→压缩不改变语义，不产生 `LongWord` 节点（0.1.1 §4.17）。

**已知坑**：

- 评审 I-32/C-7：含空格长词与去空白的冲突；phase 5 必须用“按需加引号 + 先换短词再删空白/或反向匹配”的顺序实现，golden 直接覆盖 `my application`。
- 评审 R-20：反向映射前缀歧义（`alpha`/`alphabet`）；phase 4 建表时就要求长词唯一，phase 5 只消费。
- `<` 标记按 B1 行模式；相关 map golden 纳入正常用例，不再放 `pending/`。
- 双宿主：`Bytes/Opaque` 不做文本格式化；phase 5 只处理文本值，二进制值原样透传或报 `cannot_format`，不能有损转 STRING。

---

## phase 6：值模型与 `{value, ok}`（Runtime 轨）

**目标**：定义运行时值、成败通道、truthy/falsy、`$` 的基准模型；用 fake 工具，不接真实系统。

**依赖**：phase 3 AST；可与 phase 4/5 并行。

**产出物**：

- `src/runtime/value`、`src/runtime/result`；
- fake VerbRegistry；
- `Value` 的 `Bytes` / `Opaque` 变体（Shell 宿主的二进制/流口子；Agent 宿主可不用）；
- `ExecOutcome`：`{value, ok, error, host_meta?}` + `exit_code` 映射钩子；
- 单测：truthy/falsy、`{value, ok}` 构造、错误串、默认 break、host 值透传。

**工作项**：

1. 值类型：`STRING` / `NUMBER` / 数组 / 对象 / `null` / `bool`；来自工具的空对象/空数组；**预留 `Bytes` / `Opaque`**，不让 OS 类型进入 AST。
2. `ExecOutcome := {value, ok, error, host_meta?}`；`[ok]` 只在 `ok == true`，`$ = value`；`[error]` 只在 `ok == false`，`$ =` 错误串（0.1.1 §4.10）；`exit_code` 只留钩子，不写死数字。
3. truthy/falsy：`null`、`false`、`0`、`""`、`[]`、`{}` 为 false（0.1.1 §4.12）。
4. `$` 基准：无介宾语句的 `$` = 语句结果；`$name` 变量、`.`字段、`$` self 三者的区分（0.1.1 §4.8；评审 I-23/I-24）。
5. 默认错误：`break "RILL DSL ERROR"`；顶层/管道/块三种场域的初始定义（评审 I-12/I-15）。
6. `host_meta` 不进入 `$`，只供 Host 适配器/诊断使用；`$` 仍是规范定义的字符串/值。

**退出判据**：

- 单测覆盖 6 个 falsy 值 + 非空值；
- `ok == true` 但 `value == ""` 时 `[ok]` 仍触发；
- 默认错误串稳定；顶层失败不继续下一条语句；
- `$` 在无介宾语句中可观察；
- `Bytes/Opaque` 可构造、可透传，且不被 truthy/falsy 误判；
- `ExecOutcome.exit_code` 钩子存在，Agent profile 可为空、Shell profile 可映射。

**不做什么**：不实现尾随块顺序，不实现 `|>`，不实现 each/parallel；不把 OS 的 `ProcessResult` 直接塞进 `$`。

**已知坑**：评审 R-06/C-10（`[ok]` 按成功还是 truthy）；phase 6 必须把 `ok` 与 truthy 分开，`[ok]` 只看 `ok`，`if` 才看 truthy。双宿主：`Value` 必须从第一天就容纳 `Bytes/Opaque`，否则 Shell 接入时要改运行时核心。

---

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
