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
2. 重写样例，不复用旧 `v0.1 rev.1` 语法（`let` / `fn` / `|?` / `# allow:`，不是 0.1.1）；
   旧样例目录已下线，现行样例在 `examples/tour/`。
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


> phase 7–12 的详细计划见 [rill-0.1.0-phase-plan-7-12.md](rill-0.1.0-phase-plan-7-12.md)。
