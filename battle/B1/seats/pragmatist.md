# B1 成本席（pragmatist）

## 0. 席位口径

- 我只算代价：实现量、改动面、LLM 写错率、可测试性、对「省 token」的净影响。不给方案投赞成票，只给每个方案标价。
- 标注规则：
  - `[引用]` = 本次读到的文件里有 `file:line` 锚点，可直接核对。
  - `[判断]` = 我按常见递归下降手写量估的，没有实现可对照，误差按 ±50% 处理。
  - `[未核实]` = 转述数字，我在三份文件里没找到锚点，不进合计。
- 计价三原则（这三条决定了后面的排序和只读行数排序不一样）：
  1. **返工按「触碰文件数」计价，不按行数计价。** 改 5 行但要求重写 40 个 golden，比改 60 行但只碰 1 个函数贵。
  2. **「0 行」通常是假的。** 一个产生式留在 BNF 里但没有消歧规则，成本会挪到散文规则、诊断代码和写不出来的测试用例上。我把这部分也计入。
  3. **增量成本，不是 patch 成本。** 仓库现在没有实现（见 §1），所有行数都是「M1 预算增量」；好处是现在裁定最便宜，坏处是我的估算没有任何既有代码可校准。

---

## 1. 事实基线

| 事实 | 证据 | 对成本的影响 |
| --- | --- | --- |
| 仓库无实现、无构建、无测试入口、无 `tools/check.sh` | [S-001-call-form.md](file:///Users/samxx/trae-ws/rill-dsl/docs/spec/S-001-call-form.md#L36)、[同文件 L46](file:///Users/samxx/trae-ws/rill-dsl/docs/spec/S-001-call-form.md#L46) | 今天「让已写好的 parser 返工」成本 = 0。这个 0 只在这一刻成立，M1 一落地就消失 |
| M1 = 1500 行，M6 = 700 行，M7 = 400 行 | [引用] [dsl-spec-v0.1.md §12](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L491-L497) | 我用它当分母：本文推荐方案合计约 145 行 ≈ M1 的 7%~10% |
| 「while 约 300 行」 | [未核实] 三份文件里没有锚点 | 不计入合计，也不用来类比 |
| 词法表没列 `,` `:` `(` `)`，但文法在用 | [引用] 表在 [v0.1 L19-L35](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L19-L35)；`param_list` 用 `,` 在 [L68](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L68)，`arg_list` 用 `,` 在 [L86](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L86)，分组 `(` 在 [L91](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L91)，postfix `()` 在 [L85](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L85) | 任何「lexer 改 0 行」的说法都不成立。四项标点最少 +5~10 行，已摊到下面各项 |
| B1 五条全部 pending | [PENDING.md L27 P-001](file:///Users/samxx/trae-ws/rill-dsl/docs/spec/PENDING.md#L27)、[L28 P-002](file:///Users/samxx/trae-ws/rill-dsl/docs/spec/PENDING.md#L28)、[L44 P-018](file:///Users/samxx/trae-ws/rill-dsl/docs/spec/PENDING.md#L44) | 现在改一行 BNF 只写一次；M1 之后同样一行要连带全部 golden |

**成本最高的场景不是选错，是带着未决项开工。** M1 的交付物按 [讨论稿 §7](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L460-L478) 是「parser + golden」。B1 五条里有三条直接改变 token 流或 AST 形状，golden 一旦按旧形状落盘，就是按文件数计价的返工。

---

## 2. 逐项

### 2.1 实参文法：`arg := primary` vs `arg := postfix_expr`

| 方案 | lexer | parser | 诊断/文档 | golden | 返工触发器 | token |
| --- | --- | --- | --- | --- | --- | --- |
| A：`arg := primary`（v0.1 原样，[L92](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L92)） | 0 | 0 照抄，但要补消歧 | +15~25 行散文 + 20~30 行特判 | 4~6 条只能测「能解析」，测不到「解析成什么」 | 高：AST 形状会变 | 0 |
| A'：A + 散文消歧（同级不递归） | 0 | +20~30 | +15~25 行规范文本 | 8~10 | 中：文档与实现两处可能漂移 | 0 |
| B：`arg := postfix_expr`（[讨论稿 P0-3 L128](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L128)） | 0 | +10~20 | +10 | 6~10 | 无（终局形态） | 常见 0；嵌套 +3 字符 / 0 lexeme |

排序（便宜→贵）：**B < A' < A**。

依据：

1. A 的「0 行」是账面数字。`f a b c` 在 A 下有四种分析树，这是 [引用] [P0-3 L122](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L122) 已经写死的。要落地必须先选一棵树：
   - 选「贪婪递归」= `f(a(b(c)))`，0 行消歧代码，但语义反直觉，golden 没法按直觉写；
   - 选「同级不递归」= 在行为上已经等于 B，只是把规则写在散文里（A'），代码没省，反而多了一份可能和实现漂移的规范文本。
2. A' 比 B 贵在**同一规则存在两处**（BNF 一处散文、parser 一处特判），任何一次改动要同步两处。这是长期成本，不是一次性成本。
3. 单独看，A 的「+0 行」比 B 的「+10~20 行」便宜。但 A 让 4~6 条测试用例写不出确定期望——在这个仓库里，「测不了」比「多 20 行」贵，因为 M1 的验收门就是 golden。

回退步骤（三条方案通用）：只动一个 `parse_arg`/`parse_postfix` 入口，回退 = 还原该产生式 + 删对应 golden，无跨模块状态。

### 2.2 数字字面量是否带负号

| 方案 | lexer | parser | golden | 返工触发器 | token |
| --- | --- | --- | --- | --- | --- |
| A：`-?[0-9]+...`（[L22](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L22)） | 0 | 0（但必然 bug） | 5~8 条回归 | 高：NUMBER 词法变了，所有含数字的用例重看 | 0 |
| A-补：保持词法，parser 里看前一个 token 判断 | 0 | +25~40 | 5~8 | 高：`(`/`[`/`,`/`|>` 后各要一份判断 | 0 |
| B：非负数字 + 一元 `-`（[P0-1 L94](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L94)） | −1~3（删 `-?`；`-` 已在 [L29](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L29) 算术表内） | 0（unary 已在 [L84](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L84)） | 4~6 | 无 | `read (-1)` +2 字符 / 0 lexeme，极低频 |

排序：**B << A-补 < A**。

依据：

1. B 是 B1 里唯一「净删代码」的方案（lexer 少一条规则），而且一元 `-` 的产生式在 v0.1 里已经存在，parser 一行不用加。这是全组性价比最高的一项。
2. A 的代价不在 lexer 行数，在**失败模式**：`a -1`→`a(-1)`、`x-1`→`x(-1)`、`1-2`→两个相邻 primary（[P0-1 L88-L94](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L88-L94)）。后者**不报错**，会变成一次带奇怪参数的调用。对 LLM 来说这是最坏的错法：没有语法错误可自纠，只有工具侧报参数类型错，甚至产生副作用（`write` 多一个参数）后才暴露。
3. A-补（看前一个 token）在 `read -1` 这类实参位置会和 2.1 的 arg 解析纠缠：前一个 token 是 IDENT 时，`-1` 到底是实参还是减法，取决于 2.1 选了 A 还是 B。**所以 2.2 的方法选择部分被 2.1 锁定**，两项应同批裁定。
4. 跨项接口先记一笔：如果选 B，`emit "x" { "k": -1 }` 里的负数要靠 `json_value` 接受一元 `-` 或接受分组，否则 2.5 的对象字面量会静默禁掉负数。

回退：单条 lexer 正则 + 4~6 条 golden，回退成本可忽略。

### 2.3 NEWLINE 语句终止符

| 方案 | lexer | parser | golden | 返工触发器 | token |
| --- | --- | --- | --- | --- | --- |
| A：不加（换行只是空白） | 0 | 「stop-set 补丁」不成立，见下 | 多语句程序写不出确定性用例 | **最高**：token 流契约变更 | 0 |
| B：加 NEWLINE + 5 条细则（[P0-2 L112-L117](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L112-L117)） | +15~25 | +25~40 | +8~12 | 无（M1 开工前定） | 0 |

排序：**B（一次性 +40~65 行）< A（要么无解，要么引入更贵的分隔符）**。

依据：

1. A 的补丁路径只有一半可行。关键字打头的语句可以用 stop-set 切（`let/if/for/fn/return/emit` 都是保留字），但表达式语句切不开：`read "a"` 换行 `"b"` 会变成两个实参，`f x` 换行 `g y` 无任何 token 能区分（[P0-2 L104-L105](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L104-L105)）。结论不是「A 需要更多代码」，是**A 没有完整解**：要补只能退回 `;` 或缩进，而这两者都被 [L37](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L37) 明确否掉。
2. A 的失败模式同样是静默的：两条语句被合并成一次带多余实参的调用。解析期不报错。
3. B 的 token 成本是 **0**，这是本席最想强调的一点：LLM 输出本来就是一行一句，把换行升格为 token 不要求它多写一个字符。所以「省 token」不构成反对 NEWLINE 的理由。
4. B 的返工乘数最大：NEWLINE 改变了 token 流契约，M1 的每个多语句 golden 都要重写。若 M1 交付 30~60 个 golden [判断]，推迟的代价是 30~60 个文件，而不是 40 行代码。**这是「只修三条」里必须排第一的唯一理由。**

回退：NEWLINE 是词法层新增 token，回退 = 删 token + 恢复 `statement*` 的空白跳过，但 golden 会再次全部受影响。属「一次定死」项。

### 2.4 postfix `()` 去留

| 方案 | lexer | parser | 诊断/loader | golden | 返工触发器 | token |
| --- | --- | --- | --- | --- | --- | --- |
| A：保留（[L85](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L85)） | 0 | 0 | +10~20（识别后拒绝）或推翻 D-001 | 3~5 | 中 | 字符 −2/次；lexeme 口径反而 +1 |
| B：删除（[P0-5 L164](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L164)） | 0 | −3~5 | +10~15 | 3~5 | 无 | 同上，两口径相反 |

排序：**B < A**。

依据：

1. A 的三个成本都不在 parser 行数上：
   - **治理**：D-001 已是 `accepted`（[D-001 L6](file:///Users/samxx/trae-ws/rill-dsl/docs/decisions/D-001.md#L6)），保留 postfix `()` 等于要么接受两种调用形态（推翻 D-001 + 改 S-001 + 改 few-shot + 改示例），要么 parse 通过后拒绝（+10~20 行诊断）。两条都比 B 贵。
   - **能力幻觉**：`a.b()` 暗示方法调用，但 §10 映射只有字段读走 `json_get`（[L446](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L446)），运行时没有方法派发。保留产生式 = 要么实现一个没人要的特性，要么让 parser 接受运行时接不住的东西。
   - **吃掉 2.1 的成果**：保留 postfix `()` 后，`f (g "x")` 里的 `(` 既可以是分组也可以是 postfix 调用的开头，2.1 辛苦定下的「实参边界唯一」当场失效。**这是 2.1 与 2.4 必须打包裁定的硬理由，不是我的偏好。**
2. B 是净删产生式（−3~5 行），唯一新增是 3~5 条「这里不许写括号调用」的诊断用例，而这批用例在 A 下同样要写（因为 D-001 禁止接受括号调用）。
3. token 我不给这条定价：按空格切分的 lexeme 口径，`f("a")` 是 1 个 lexeme、`f "a"` 是 2 个，括号形态反而「更省」；按真实 BPE 分词多半相反。两个口径结论相反，且我没有跑分词器，所以这条只按歧义与治理成本排序。

### 2.5 emit 对象字面量产生式

| 方案 | lexer | parser | golden | 返工触发器 | token |
| --- | --- | --- | --- | --- | --- |
| A：无产生式（v0.1 原样） | 0 | 0 | 2~4（错误路径） | 低 | 每次结构化 emit +5~10 lexeme [判断] |
| B：仅 emit 位置允许对象/数组（[P0-4 L144-L149](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L144-L149)） | +2~4（补 `:`、`,`） | +40~60 | 6~10 | 无（M7 内部） | 0（`{...}` 已是最紧凑写法） |
| C：通用对象字面量 | +2~4 | +80~120 + 所有块构造要前瞻 | 10~15 | 高：`{` 歧义扩散到 if/for/while/into | 0 |

排序：**B < A < C**。

依据：

1. A 不是零成本：§8 示例 4 的 `emit "analysis_done" { ... }`（[L396-L406](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L396-L406)）在 A 下不可解析，必须改文档 + 改 few-shot；结构化 payload 只能走 `json_build`，每次 emit 多 5~10 lexeme，并把成本推给每一次调用。
2. B 把成本一次性付清，且**爆炸半径最小**：只碰 `emit` 一个语句的 payload 位置，不动表达式文法，`if expr {` 的 `{` 不受影响（[P0-4 L149](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L149)）。M7 本来就 400 行 [引用 L497]，+40~60 行 ≈ +10~15%。
3. C 是唯一的「会毁掉块消歧」的选项：`{` 进入通用表达式后，`if`/`for`/`while`/`into` 每个块构造都要前瞻判断「这是块还是对象」，错误信息也会退化。多花 40~60 行买一个没有需求支撑的特性，最贵。
4. 时序成本：B 可以等到 M7 再定，不影响 M1。所以它排最后不是因为它贵，是因为它**不阻塞**。

---

## 3. 汇总（推荐组合：全选 B）

| 项 | lexer | parser | 诊断/loader | golden 用例 | 返工触发器 | token 净变化 |
| --- | --- | --- | --- | --- | --- | --- |
| 2.1 实参文法 | 0 | +10~20 | +10 | 6~10 | 高（AST 形状） | 0；嵌套 +3 字符 |
| 2.2 负数词法 | −1~3 | 0 | 0 | 4~6 | 高（NUMBER 词法） | 罕用 +2 字符 |
| 2.3 NEWLINE | +15~25 | +25~40 | 0 | 8~12 | 最高（token 流） | 0 |
| 2.4 postfix `()` | 0 | −3~5 | +10~15 | 3~5 | 中 | 见 §2.4，不给数 |
| 2.5 emit 对象 | +2~4 | +40~60 | +5 | 6~10 | 低（M7 内部） | 0；替代写法省 5~10/次 |
| **合计** | **+16~26** | **+72~115** | **+25~30** | **27~43** | — | **全部为 0 或负** |

合计约 115~170 行，对 M1 的 1500 行 [引用] 是 8%~11%。**五条里没有一条在 token 上是净增的**——「省 token」这个原始目标与这五个修复都不冲突，唯一有争议的 2.4 我给不出可信数字，因此不拿 token 当它的理由。

回退（E4 第三项）：五项都落在单点产生式上，无跨模块状态。回退 = 还原产生式 + 删除对应 golden；唯一例外是 2.3，回退会再次冲击全部多语句 golden。

---

## 4. 总排序与「只修三条」

按「返工乘数 × 触碰面」排序（不是按行数）：

| 序 | 项 | 一句话理由 |
| --- | --- | --- |
| 1 | 2.3 NEWLINE | 唯一改 token 流契约的项；推迟代价按 golden 文件数计，token 成本为 0 |
| 2 | 2.1 实参文法（**打包** 2.4 postfix `()`） | 同一个 parse 函数、同一条产生式；不删 postfix `()` 会吃掉 2.1 的消歧成果 |
| 3 | 2.2 负数词法 | 全组最便宜（净删 1~3 行），却影响每个数字字面量；与 2.1 共用 `read -1` 这批用例 |
| 4 | 2.4 postfix `()` | 已折进第 2 条；单独看比 2.2 更便宜 |
| 5 | 2.5 emit 对象 | 爆炸半径最小但不阻塞 M1，M7 前定都来得及 |

**只修三条：2.3 NEWLINE →（2.1 + 2.4 打包）→ 2.2 负数词法。**

理由：这三条是唯一同时满足「现在改便宜、以后改要连坐 golden」的项。2.5 虽然也便宜，但它只影响 `emit` 一个语句、且排在 M7，晚定不会让任何已有产物作废；把它塞进前三只会让本次裁定多一条未验证的接口。

若裁判不接受「2.1 + 2.4 打包」算一条，则第三条换成 **2.4 postfix `()`**（它更便宜且是 2.1 的前置），2.2 顺延为第四——行数排序不变，只是「三条」的切法变了。

---

## 5. 两个没人报价的成本

1. **双形态回退路径是常驻成本。** [讨论稿 §7 L475-L477](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L475-L477) 把「路径 B（括号调用）」写成 M1 验收失败时的退路。如果实现层面的做法是「parser 同时接受两种形态」，成本是 +60~100 行 parser + 双份 golden + few-shot 双写，且 2.1/2.4 全部作废。要留退路就做成**构建开关或版本分支**，不要做成运行时双接受。
2. **反悔 D-001 有治理成本。** D-001 已 `accepted`。任何「保留/恢复括号调用」的结论都要 `supersede` 它、改 S-001、改 few-shot、改 1~3 个示例（如 [L22](file:///Users/samxx/trae-ws/rill-dsl/docs/spec/S-001-call-form.md#L22) 的 `analyze_file("src/a.c")`）。这部分不进代码行数，但进工期。

---

## 6. 我的核算在什么条件下失效

1. **M1 不产 golden。** 若 M1 只做手工冒烟、没有 golden 套件，「返工按文件数计价」这条前提消失，排序退化为纯行数：2.2 < 2.4 < 2.1 < 2.5 < 2.3。
2. **评测给出相反数据。** 若真实 LLM 在空格调用上写错 ≥3 次并按 [L476](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L476) 切到路径 B，2.1/2.4 的成本结论重算。
3. **emit 频次高。** 若真实脚本里结构化 emit 占比高（我没有频次数据），2.5 从最后提到前二。
4. **行数基准问我。** 所有 `[判断]` 项若被实现方实测推翻，我按实测改写，不改排序理由本身（排序靠的是「触碰面 × 返工乘数」，与具体行数弱相关）。

---

## 7. 我可能错在哪

1. 行数全是我按常见手写递归下降估的，没有实现可对照，误差可能 ±50%；`+40~60`（emit）和 `+25~40`（NEWLINE parser）这两处最不可靠。
2. token 我给了 lexeme 与字符两个口径，但**没有跑任何 BPE 分词器**。「空格形态更省 token」在真实分词器上可能不成立，我不替它背书；2.4 我因此拒绝用 token 定价。
3. 「M1 会交付 30~60 个 golden」是判断，不是实测——仓库没有测试目录（[S-001 L46](file:///Users/samxx/trae-ws/rill-dsl/docs/spec/S-001-call-form.md#L46)）。这个数字直接决定 2.3 排第一的力度，若实际只有 10 个 golden，2.3 与 2.1 的排序可以互换。
4. 「2.1 与 2.4 必须打包」我按成本论证（同函数、同产生式、有交互），但裁判完全可能认为这是两条独立判据；我在 §4 已给出不接受打包时的替代切法。
5. 「while ≈300 行」我没找到锚点，按未核实处理；如果我漏读了包含它的文档，我的分母类比可能偏保守。
6. 我只读了 v0.1、讨论稿、AGENTS §7、PENDING、S-001、D-001，没有读 `docs/requirements/` 全文。若有既定判据与我的失效条件冲突，以判据为准，我的成本排序需要重跑。
