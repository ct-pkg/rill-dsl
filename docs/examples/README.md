# Rill DSL 样例集

> 状态：`unverified`。本目录是**非规范性**样例，不是规范正文；规范以 [docs/spec/dsl/](../spec/dsl/README.md) 的 `v0.1 rev.1` 为准。
> 仓库当前没有 lexer/parser/解释器，下面的脚本**没有运行过**；它们只按 `v0.1 rev.1` 的 EBNF、[D-001..D-020](../decisions/README.md) 与 [工具契约](../spec/tools/README.md) 手工推导。凡涉及尚未定稿的语法，正文会标明依据；没有定稿的写法不写进样例。

## 1. 这组样例解决什么

面向两类读者：

- **评审**：直接看「自然语言指令 → DSL 脚本 → 逐步语义」，判断语法是否够用、错误传播是否符合预期。
- **后续实现**：把每个样例当作候选 golden 的输入；实现落地后再补真实的 lexer/parser/运行期证据，而不是现在就把手工推导当成验收结果。

每个样例都包含：场景一句话、带注释的 DSL 源码、逐步语义、LLM 指令大意、暴露出的空白。本目录共 **7 个场景样例**；结尾的 [§5 问题清单](#5-样例暴露的问题清单) 汇总 **15 条问题**，按严重程度排序。

## 2. 阅读顺序

| # | 文件 | 场景 | 主要覆盖 |
| --- | --- | --- | --- |
| 01 | [顺序编排](01-sequential.md) | 读两个文件 → 搜索 → 合并写盘 | header、`let`、空格调用、`\|>`、数组拼接、`write` |
| 02 | [条件分支](02-conditional.md) | 有命中写数组，无命中写 `none` | `if`/`else`、`.length`、`[]` 与 `null` 的区别 |
| 03 | [循环与遍历](03-loop.md) | 逐个文件统计，空项跳过，`STOP` 提前退出 | `for`、`break`/`continue`、`let mut`、`json_parse` |
| 04 | [错误处理](04-error-handling.md) | 配置读取失败回退默认配置 | `fn`、`\|?`、`into`/`$` 注入、可捕获/不可捕获 |
| 05 | [批量与并行](05-batch-serial.md) | 串行批量处理；说明 `par` 为何不能写 | 串行等价写法、逐项降级、`not_implemented` |
| 06 | [白名单与权限边界](06-allowlist-boundary.md) | 只授权 `read`，越界 `write` 被拒绝 | `# allow:`、三层白名单、`tool_not_allowed`、路径 `constraint` |
| 07 | [综合例子](07-end-to-end.md) | 批量读取 → 逐项摘要 → 汇总报告 + 事件 | 顺序、条件、循环、错误处理、批量、`emit` |

## 3. 通用约定

- **工具只用六个契约内工具**：`read`、`grep`、`write`、`json_parse`、`get`、`json_build`（可选）。样例不发明工具；没有出现的工具名不要当成已注册。
- **header 不是注释**：`# allow:`、`# deny:`、`# emit:`、`# dsl-version:` 是 header 行；`# allow:` 缺失时默认拒绝（`no_allow_header`）。
- **调用是「名字 + 空格实参」**：`read "a.txt"`、`grep "TODO" text`；括号只用于分组和 `fn` 形参表。`f()`、`f(a, b)` 不是本 DSL 的调用形态。
- **实参不递归**：`f g "x"` = `f(g, "x")`；要传嵌套调用写 `f (g "x")`，要传表达式写 `f (a + b)`。
- **`|>` 追加实参**：`a |> f b` = `f(b, a)`；管道不改变 arity，所以 `x |> read "p"` 会得到 2 个实参并在加载期报 `arity`。
- **`|?` 高于 `|>`**：`a |> f b |? g c` = `a |> (f b |? g c)`；`|?` 左侧必须是单个 call，链式时只检查最左操作数。
- **空集合不是 `null`**：`grep` 无匹配返回 `[]`，判空写 `matches.length > 0`，不要写 `matches != null`。
- **`write` 的两种落盘形态**：`content` 是 `string` 时写原始 UTF-8 字节；是其他五类值时写 JSON 文本。
- **没有 `while`、递归、`try/catch`、通用对象/数组字面量、并行**：`par` 是保留字，脚本出现即加载期 `not_implemented`；轮询交给工具的 `timeout`/`interval` 或内核重试。
- **路径相对 workspace root**：`read`/`write` 的路径约束由内核执行；`..` 在打开前消解，越界报 `constraint`，不可捕获。
- **样例中的代码块是推导文本，不是 golden**：没有 parser，不能据此声称「能跑通」。

## 4. 样例与规范条目的对应

| 样例 | 主要规范 | 决策锚点 |
| --- | --- | --- |
| 01 | [02 §3](../spec/dsl/02-grammar.md)、[04 §1](../spec/dsl/04-pipeline-errors.md)、[03 §1](../spec/dsl/03-semantics.md) | D-001、D-002、D-016 |
| 02 | [03 §4](../spec/dsl/03-semantics.md)、[03 §8](../spec/dsl/03-semantics.md)、[04 §3](../spec/dsl/04-pipeline-errors.md) | D-016 |
| 03 | [02 §2](../spec/dsl/02-grammar.md)、[03 §4](../spec/dsl/03-semantics.md)、[03 §5](../spec/dsl/03-semantics.md) | D-009 |
| 04 | [04 §2](../spec/dsl/04-pipeline-errors.md)、[03 §6](../spec/dsl/03-semantics.md)、[03 §7](../spec/dsl/03-semantics.md) | D-007、D-010、D-017 |
| 05 | [03 §4](../spec/dsl/03-semantics.md)、[04 §1](../spec/dsl/04-pipeline-errors.md)、[06 §6](../spec/dsl/06-security.md) | D-019 |
| 06 | [06 §1](../spec/dsl/06-security.md)、[06 §2](../spec/dsl/06-security.md)、[06 §5.1](../spec/dsl/06-security.md) | D-011、D-014 |
| 07 | [03 §4](../spec/dsl/03-semantics.md)、[03 §6](../spec/dsl/03-semantics.md)、[05 §2](../spec/dsl/05-data-metadata.md) | D-007、D-016、D-019 |

## 5. 样例暴露的问题清单

> 共 15 条：高 6 条、中 8 条、低 1 条。每条标注类型，并指向已有结论或明确写「无结论」。
> 类型列先给三类主标签：**语法歧义 / 语义未定义 / 表达能力缺口**；「语法限制」「语义已定但易误用」「安全模型缺口」是补充标签，分别表示文法已定但表达不便、语义已定但有陷阱、安全边界不完整，均**不是**「语法歧义」。
> 「已定」表示规范/决策已有结论，问题在于表达能力或使用成本；「无结论」表示仓库里没有拍板，不应在实现时自行发明规则。

| ID | 严重度 | 类型 | 一句话 | 结论状态 |
| --- | --- | --- | --- | --- |
| [EX-01](#ex-01) | 高 | 表达能力缺口 | 没有目录枚举/`glob`，批量输入必须外部提供清单 | 无结论 |
| [EX-02](#ex-02) | 高 | 语义未定义 + 表达缺口 | 没有类型判定，批量元素类型不可校验 | 无结论 |
| [EX-03](#ex-03) | 高 | 表达能力缺口 | `\|?` 只能包单个 call，不能包整条管道；无错误值 | D-007/D-010 已定 |
| [EX-04](#ex-04) | 高 | 语义未定义 | `null` 不是失败，没有 null 合并语法 | 部分有结论，无合并语法 |
| [EX-05](#ex-05) | 高 | 安全模型缺口 | `# allow:` 自声明、不校验未注册名、无外部主体 | P-023 已定；P-020 undecidable |
| [EX-06](#ex-06) | 高 | 表达能力缺口 | 没有并行/汇合原语，`par` 只报 `not_implemented` | D-019 已定 |
| [EX-07](#ex-07) | 中 | 表达能力缺口 | 没有 `string.length`、`join`、`split`、`format` | D-016 部分已定；其余无结论 |
| [EX-08](#ex-08) | 中 | 语义未定义 | `grep` 的正则方言、锚点、Unicode 行为未定义 | 无结论 |
| [EX-09](#ex-09) | 中 | 语法限制 | 没有 `else if`；`if` 不是表达式 | 文法已定；无结论 |
| [EX-10](#ex-10) | 中 | 语义已定但表达受限 | `into` 是语句，块值被丢弃，不能作表达式 | D-017/03 §7 已定 |
| [EX-11](#ex-11) | 中 | 表达能力缺口 | 无通用对象/数组构造；`json_build` 是可选工具 | 02 §4、T-006 已定 |
| [EX-12](#ex-12) | 中 | 语义已定但表达受限 | `write` 覆盖写、不原子、不能追加/流式写 | T-003 已定；追加无结论 |
| [EX-13](#ex-13) | 中 | 语义已定但易误用 | 截断输入进 `json_parse` 报不可捕获的 `limit` | T-004/07 §3.2 已定 |
| [EX-14](#ex-14) | 低 | 安全风险 | `grep` 的 ReDoS 没有长度/复杂度上限 | T-002 已声明本期不主张 |
| [EX-15](#ex-15) | 中 | 语义已定但可移植性缺口 | workspace root 由内核配置提供，脚本不可见 | 06 §5.1 已定 |

<a id="ex-01"></a>
### EX-01 没有目录枚举/`glob`（高，表达能力缺口）

- 现象：[样例 05](05-batch-serial.md)、[样例 07](07-end-to-end.md) 的「一批文件」只能来自外部 `files.json`；脚本不能自己列目录。
- 依据：[工具目录 §1](../spec/tools/README.md) 只收录 `read`/`grep`/`write`/`json_parse`/`get`/`json_build`；[dsl/README §4](../spec/dsl/README.md) 的非目标表也没有「目录枚举」的替代工具。
- 结论：**无结论**。若后续增加 `list`/`glob`，需要同时定义路径约束、排序、截断与错误类别，不能只加一个名字。

<a id="ex-02"></a>
### EX-02 没有类型判定，批量元素类型不可校验（高，语义未定义 + 表达缺口）

- 现象：`for` 只保证集合是 `json_array`（[03 §4](../spec/dsl/03-semantics.md)），不保证元素是 `string`；`read path` 对非字符串报 `constraint`，不可捕获（[04 §2.1](../spec/dsl/04-pipeline-errors.md)），整批中止。
- 依据：值模型只有六类（[03 §1](../spec/dsl/03-semantics.md)），没有 `typeof`、类型谓词或模式匹配。
- 结论：**无结论**。当前只能信任清单输入，或在 DSL 外预处理。

<a id="ex-03"></a>
### EX-03 `|?` 只能包单个 call，无错误值（高，表达能力缺口）

- 现象：`read "a" |> json_parse |? fallback` 的 `|?` 绑定到右侧 `json_parse`，`read` 的失败不会被捕获；要覆盖整条链路必须用 `fn` 包装（[样例 04](04-error-handling.md)）。
- 依据：[D-007](../decisions/D-007.md)、[04 §2](../spec/dsl/04-pipeline-errors.md) 已定「左侧单 call」；[04 §2.7](../spec/dsl/04-pipeline-errors.md) 明确 `|?` 只产生值、不产生错误对象。
- 结论：**已定，非未决**。这是刻意的调用级降级设计；代价是「整段回退」写法不直观，且无法按 `error_kind` 分支。

<a id="ex-04"></a>
### EX-04 `null` 不是失败，没有 null 合并（高，语义未定义）

- 现象：`get "port" cfg` 缺键返回 `null`，`|?` 不触发；必须显式写 `if port == null`（[样例 04](04-error-handling.md)）。
- 依据：[04 §2.1](../spec/dsl/04-pipeline-errors.md) 已定「`null` 是值，不是失败」；规范没有 `??`/`default`/可选链语法。
- 结论：**「null 不是失败」已定；是否新增 null 合并语法无结论**。不要在实现里偷偷把缺键改成 `not_found`，那会改变 `|?` 的可捕获集。

<a id="ex-05"></a>
### EX-05 白名单自声明、不校验未注册名、无外部主体（高，安全模型缺口）

- 现象：`# allow:` 由脚本作者自书；默认拒绝只防「无意识授权」，不阻止显式申请危险工具；`# allow: raed` 不会加载失败，调用 `raed` 才 `unknown_tool`；没有 `principal_id`/`grant_set` 约束自授权（[样例 06](06-allowlist-boundary.md)）。
- 依据：[D-011](../decisions/D-011.md) 定默认拒绝与 `*` 审计；[P-023](../spec/PENDING.md) 定「未注册名不报错」；[P-020](../spec/PENDING.md) 为 `undecidable`。
- 结论：**P-023 已定；P-020 无结论**。多租户/外部授权场景的安全边界仍不完整。

<a id="ex-06"></a>
### EX-06 没有并行/汇合原语（高，表达能力缺口）

- 现象：多个独立调用只能按源码顺序串行，或写成串行 `for`；`par` 是保留字，脚本出现即 `not_implemented`，不解析块（[样例 05](05-batch-serial.md)）。
- 依据：[D-019](../decisions/D-019.md)、[06 §6](../spec/dsl/06-security.md)、[dsl/README §4](../spec/dsl/README.md)。
- 结论：**已定**。并行由内核调度；脚本内部没有 join/依赖图/并发语义。

<a id="ex-07"></a>
### EX-07 字符串处理不足（中，表达能力缺口）

- 现象：没有 `string.length`，没有 `join`/`split`/`format`；`grep` 返回数组后，`write` 写的是 JSON 文本，想「一行一条」只能手工 `+ "\n"`（[样例 01](01-sequential.md)、[样例 07](07-end-to-end.md)）。
- 依据：[D-016](../decisions/D-016.md) 只给 `string + 标量` 拼接与 `json_array.length`，并明确不给 `string.length`；[T-003 §1](../spec/tools/T-003-tool-write.md) 定 `write` 的非字符串内容按 JSON 序列化。
- 结论：**`string.length` 不定义已定；`join`/`split`/格式化无结论**。需要报告拼装、行切分、长度校验时只能绕。

<a id="ex-08"></a>
### EX-08 `grep` 正则方言未定义（中，语义未定义）

- 现象：`grep` 的 `pattern` 是「正则表达式文本」（[T-002 §1](../spec/tools/T-002-tool-grep.md)），但没有指定 ERE/POSIX/RE2、锚点、大小写、Unicode、`.` 是否匹配空行等；用 `grep "."` 切行是常见 workaround，但结果不可移植。
- 依据：工具条目只写了「正则作为字符串」，没有方言；规范也没有正则字面量。
- 结论：**无结论**。样例只使用 `"TODO"`/`"ERROR"` 这种字面模式，避免依赖未定语义。

<a id="ex-09"></a>
### EX-09 没有 `else if`，`if` 不是表达式（中，语法限制）

- 现象：`if_stmt := "if" expr block ("else" block)?`（[02 §2](../spec/dsl/02-grammar.md)）；多分支只能 `else { if ... }`。`if` 是语句，不能 `let x = if cond { a } else { b }`；要选值必须 `let mut` + 分支赋值。
- 依据：文法已定；没有 `else if` 产生式，也没有对应决策记录。
- 结论：**文法已定；是否增加 `else if`/if 表达式无结论**。不要在样例里自行发明。

<a id="ex-10"></a>
### EX-10 `into` 块值被丢弃（中，语义已定但表达受限）

- 现象：`expr into { ... }` 是语句，块的值被丢弃，不能 `let x = e into { ... }`（[03 §7](../spec/dsl/03-semantics.md)）；`into` 只能注入 `$`，不能作为数据转换表达式返回值。
- 依据：[D-017](../decisions/D-017.md) 定嵌套与 `$` 覆盖/恢复；03 §7 定「块值被丢弃」。
- 结论：**已定**。「into 作为表达式」没有结论，且当前明确不是表达式。

<a id="ex-11"></a>
### EX-11 无通用对象/数组构造（中，表达能力缺口）

- 现象：`{`/`[` 只在 emit payload 位置作字面量；表达式里没有数组/对象字面量。`json_build` 是可选工具，未注册时调用 `unknown_tool`；它也不构造数组（[T-006 §1](../spec/tools/T-006-tool-json-build.md)）。
- 依据：[02 §4](../spec/dsl/02-grammar.md)、[dsl/README §4](../spec/dsl/README.md)、[工具目录 §1](../spec/tools/README.md)。
- 结论：**已定**。需要结构化结果时只能用工具返回、emit 字面量或可选的 `json_build`。

<a id="ex-12"></a>
### EX-12 `write` 不原子、不能追加（中，语义已定但表达受限）

- 现象：`write` 覆盖写，不承诺原子（[T-003 §3](../spec/tools/T-003-tool-write.md)）；没有 append/stream。大批量报告只能内存拼好后一次写，失败可能留下半截文件（[样例 07](07-end-to-end.md)）。
- 依据：T-003 §1/§3 定覆盖语义与「不承诺原子写」。
- 结论：**覆盖/非原子已定；追加/流式无结论**。断点续写与事务性写盘不在 MVP。

<a id="ex-13"></a>
### EX-13 截断输入进 `json_parse` 报不可捕获的 `limit`（中，语义已定但易误用）

- 现象：`read` 大文件被截断后，`json_parse` 因 `requires_complete_input` 在 handler 之前报 `limit`，不可捕获；`|?` 不能兜底（[样例 04](04-error-handling.md)、[样例 07](07-end-to-end.md)）。
- 依据：[T-004 §3](../spec/tools/T-004-tool-json-parse.md)、[07 §1](../spec/dsl/07-runtime.md)、[07 §3.2](../spec/dsl/07-runtime.md)、[04 §2.1](../spec/dsl/04-pipeline-errors.md)。
- 结论：**已定**。需要先判断 `(read p).truncated` 或调大 `max_output_bytes`；不能把半截 JSON 当正常输入。

<a id="ex-14"></a>
### EX-14 `grep` 的 ReDoS 没有上限（低，安全风险）

- 现象：`pattern` 的长度/复杂度上限「本期不主张」（[T-002 §4](../spec/tools/T-002-tool-grep.md)）；恶意正则可能占满 `timeout_ms`，最终 `limit`，但会消耗 CPU。
- 依据：T-002 §4 明确记录为「本期不主张」。
- 结论：**已声明不主张**；不是遗漏，但评审应知道风险仍在。

<a id="ex-15"></a>
### EX-15 workspace root 不可见（中，语义已定但可移植性缺口）

- 现象：路径约束以 workspace root 为基准解析（[06 §5.1](../spec/dsl/06-security.md)），root 由内核配置提供，脚本里看不到；同一个脚本换一个 root 可能从允许变成 `constraint`（[样例 06](06-allowlist-boundary.md)）。
- 依据：06 §5.1、[T-001 §1](../spec/tools/T-001-tool-read.md) 定「相对路径以 workspace root 为基准」。
- 结论：**已定；是否在脚本里暴露 root 无结论**。当前写法利于安全，但不利于脚本跨环境复用。

## 6. 如何继续使用

- **评审**：先读 [01](01-sequential.md) 建立「空格调用 + 管道」的直觉，再读 [04](04-error-handling.md) 与 [06](06-allowlist-boundary.md) 检查错误与安全边界，最后读 [07](07-end-to-end.md) 看整体是否够用。
- **实现**：不要直接把本目录当 golden；实现落地后，应按 [09 里程碑](../spec/dsl/09-milestones.md) 把每个样例转成可解析/可运行的夹具，并补真实退出码与输出。样例中的「期望错误」只是按 [07 §4](../spec/dsl/07-runtime.md) 手工推导的形状。
- **修订**：如果某条样例与规范正文冲突，以规范为准；发现规范没有结论的地方，登记到 [PENDING](../spec/PENDING.md) 或新决策，不要在本目录里发明规则。
