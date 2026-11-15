# B2 主张书（advocate）

- 席位：主张席，只争 B2 四个语义原语争点。
- 环境：`Darwin 27.2.0 arm64`；rill-dsl HEAD `033e5860406b91bbf226a5aa42a1818d520d28c0`；ct-lang HEAD `da83aded69c78fdc377e4d3f2e31595709f1c8d2`；2026-11-12 Asia/Shanghai。
- 隔离：未读 `battle/B2/seats/` 下其他席位文件（AGENTS §7.6 L805：庭内三席各自独立上下文）。
- 写入范围：只写本文件；未 `git add` / `git commit`；未跑全量门禁。
- 基线口径：`docs/design/dsl-spec-v0.1.md` 是**原文基线**，不直接改；本文说的“改哪一行”指下一版规范中的对应条款（[讨论稿 L9-L14](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L9-L14)）。

## 0. 结论先行

| 争点 | 主张 | 一句话判据 |
| --- | --- | --- |
| 1 降级 `\|\?` | `\|\?` 是**调用级**二元恢复，**优先级高于 `\|>`**（夹在 `\|>` 与 `or` 之间）；左操作数必须是**单个 call 节点**；失败单元 = 该 call（含其参数求值）；右侧独立求值，不接收管道值；`$` 每次调用独立注入，顺序为显式参数 → 管道值 → `$`；`retry n { ... }` 与 try/catch 都不进 MVP | 管道连续性：`a \|? b \|> c` 在 `a` 成功时 `c` 仍必须执行；P0-11 的低优先级方案在成功路径上把 `c` 整段吞掉（见 §3.3 S2/S3） |
| 2 截断元数据 | 采用**选项 C**：绑定的是值，元数据是值侧车（sidecar）；`x.truncated` / `x.original_size` 是保留伪字段，先于 JSON 字段解析；工具永远只看到 payload；读 JSON 自带同名字段用 `get "truncated" x`；截断标记**粘性**传递；不加 `limit N lines` | 零改动 v0.1 §8 的 5 个示例；`write "f" r` 不需要 `.value`；`grep` 不会把上游截断洗白 |
| 3 循环与赋值 | 引入 `x = expr`，但只能写 `let mut` 声明的**同一函数帧局部变量**；普通 `let` 不可变，`let` 仍是唯一**绑定**点；`for` 变量是每轮不可变的值拷贝；`break`/`continue` 进 M4；**`while` 不进 MVP** | `let` 的唯一定义点不被破坏：赋值只存不建名；`while` 的收益（重试已被用户裁给工具参数、轮询应在工具里带 timeout）低于其终止性与预算成本 |
| 4 R4 | R4 不推翻，改成“失败是 call 级控制信号；默认中止块；唯一消费者是它左侧那个 call 的 `\|\?`”，并补 fn 边界规则 | 同一份脚本在新 R4 下每条失败路径都有唯一归属；不存在“整块中止”与“`\|\?` 捕获”并存的两套说法 |

## 1. 不可谈判的前提（不是我立场的来源，是约束）

1. 用户已裁：`|?` 是唯一降级形态；不采用 `retry n { fallback: ... }`；重试次数走工具参数（[讨论稿 §2.3 L70-L78](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L70-L78)）。
2. 用户已裁：截断不进 DSL 语法，不加 `limit N lines` / `head N chars`；DSL 只规定 `{ value, truncated, original_size }`；字段访问必须能读到 `truncated`（[讨论稿 §2.2 L52-L68](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L52-L68)）。
3. D-001：工具调用与用户函数调用统一为一个 call 节点；括号只分组（[D-001 L29-L33](file:///Users/samxx/trae-ws/rill-dsl/docs/decisions/D-001.md#L29-L33)、[S-001 L29-L32](file:///Users/samxx/trae-ws/rill-dsl/docs/spec/S-001-call-form.md#L29-L32)）。这决定了 `|?` 的“一次调用”天然包含 `fn` 调用。
4. v0.1 的三条隐式规则不可再加第四条：隐式 await、隐式管道传参、`$`（[v0.1 §1 L11](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L11)）。任何方案若需要“记录自动拆包”“按工具类型切换返回形状”这类新隐式，直接扣分。
5. CT 只当实现语言，不当运行时语义宿主。CT 的 `into` 是**编译期脱糖**、要求静态类型、禁止嵌套（[language-spec §4.52 L2243-L2247](file:///Users/samxx/trae-ws/ct-lang/docs/language-spec.md#L2243-L2247)、[Expr.h.ct L2903-L2906](file:///Users/samxx/trae-ws/ct-lang/selfhost/ct-ast/frontend/parse/Expr.h.ct#L2903-L2906)、[Expr.h.ct L2929-L2933](file:///Users/samxx/trae-ws/ct-lang/selfhost/ct-ast/frontend/parse/Expr.h.ct#L2929-L2933)）；CT 没有运行时错误类型，诊断是编译期的 `path:line:col: error:`（[Diag.h.ct L74-L89](file:///Users/samxx/trae-ws/ct-lang/selfhost/ct-ast/tool/diag/Diag.h.ct#L74-L89)）；CT 词法只有 `T_EOF/T_ID/T_NUM/T_STR/T_PUNCT/T_PP`（[Lexer.h.ct L18-L24](file:///Users/samxx/trae-ws/ct-lang/selfhost/ct-ast/frontend/lex/Lexer.h.ct#L18-L24)）。所以 v0.1 §R3 的“复用 CT into scope 语义、parser 和 scope resolution 共享同一套逻辑”（[v0.1 L150](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L150)）必须撤回，见 §5.4。

## 2. 判据（逐条，可判定）

| ID | 判据 | 判定方式 |
| --- | --- | --- |
| C1 | 解析确定性：fallback 的保护范围在**加载期**静态确定，不随运行数据变化 | 给定脚本，能写出被保护的 call 的 `file:line:col` |
| C2 | 管道连续性：恢复后，后续 `\|>` 步骤仍对恢复值执行 | 对每个候选文法，写出 `a \|? b \|> c` 的求值轨迹 |
| C3 | 失败归属可读：最终诊断同时给出被保护调用与最终失败调用的位置 | 诊断文本含两个 `file:line:col` |
| C4 | 单次消费：一个失败最多被一个构造消费，没有嵌套 handler 二义 | 失败信号模型只有“调用点消费 / 中止块”两条出口 |
| C5 | LLM 首次写对率：形态增量 ≤2 token；自然语言描述与解析一致；写错能被加载错误精确纠正 | token 计数 + 反例脚本的预期错误文案 |
| C6 | token 成本：`\|?` 相对基线 ≤2 token/次；可变绑定 ≤1 token | 逐 token 计数 |
| C7 | 元数据不污染工具边界：handler 永远只看到值 | 管道/实参的封送规则只有一条“取 payload” |
| C8 | 元数据可静态定位：`x.truncated` 的合法性加载期可判 | 不需要运行时类型探测 |
| C9 | JSON 冲突可逃逸：值本身含 `truncated` 字段时有确定读法 | `get "truncated" x` 的语义唯一 |
| C10 | R4 自洽：新规则下 R4 仍能一句话表述，且无未定义分支 | 对四个脚本走完所有失败路径 |
| C11 | CT 不冲突：不声称复用 CT 编译期能力；不要求 CT 提供动态值/运行时错误 | CT 侧只读锚点可核对 |
| C12 | 可回退：每项 ≤1 个可单独 revert 的切片；不改变 D-001 | 改动清单逐项列文件/行数 |
| C13 | 截断可传递：下游调用不能把上游截断洗白 | `read 截断 -> grep` 的结果仍 `truncated=true` |
| C14 | 终止性：任何循环在 `ExecLimits` 下有界 | 空体 `while true` 的预期结果 |

## 3. 争点一：降级 `|?`

### 3.1 三个候选与两个备选

| 方案 | 形态 | 失败单元 | 与 `\|>` 的关系 |
| --- | --- | --- | --- |
| **T（我的主张）** | `fallback_expr := or_expr ("\|?" rhs)*`，FB-L1 把左侧限制为单个 call；`rhs := call \| atom \| "(" expr ")"` | 左侧**单个 call 节点**（含其参数求值失败） | `\|?` 高于 `\|>`，是管道操作数内部的事 |
| L（P0-11 现提案） | `fallback := pipe ("\|?" pipe)*` | 左管道**最后执行的那次工具调用** | `\|?` 低于 `\|>` |
| W（备选，题面“整个左表达式”） | 同 L，但失败单元 = 整个左管道 | 左管道任意一步失败 | `\|?` 低于 `\|>` |
| R | `retry n { fallback: ... }` | 整块？最后一次？未定义 | 语句形态 |
| E | try/catch | 整个 try 块 | 语句形态 |

P0-11 的原文是 L 方案：`expr := fallback_expr`；`fallback_expr := pipe_expr ("|?" pipe_expr)*`；失败单元是“左侧管道最后执行的那次工具调用”（[讨论稿 L224-L230](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L224-L230)）。它自己的消歧示例把 `x |> f b |? g c` 解析成 `(x |> f b) |? (g c)`（[讨论稿 §6.3 L452](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L452)）。

### 3.2 我的文法（T）

```
expr          := pipe_expr
pipe_expr     := fallback_expr ("|>" fallback_expr)*
fallback_expr := or_expr ("|?" fallback_rhs)*          # 左结合
fallback_rhs  := or_expr
```

加载期约束（不是文法约束，便于给出可读错误）：

- **FB-L1**：每个 `|?` 的左操作数必须是**单个 call 节点**（工具调用或 `fn` 调用，按 D-001 同一节点）。左侧是变量、字面量、算术表达式、分组管道 → 加载错误：`left of '|?' must be a single call; wrap the earlier chain in 'fn' or move '|?' next to the call`。
- **FB-L2**：右侧可以是 call、原子或分组表达式；**不能是裸管道**。文法上 `|>` 在 `fallback_expr` 之外，所以 `a |? b |> c` 只能是 `(a |? b) |> c`，不是 `a |? (b |> c)`。
- **FB-L2b**：在管道 stage 里，管道值只追加到 `|?` **左侧**那个 call；右侧 rhs 不接收管道值。这是 S3 求值轨迹的前提。
- **FB-L3**：`|?` 不出现在 emit payload 与 header。
- **FB-L4**：失败单元包含“该 call 的实参求值失败”。理由：`f (g "x") |? h` 若只捕获 handler 失败，失败归属会取决于 `g` 在实参里还是别处，LLM 无法预测；把整次 call 求值当一个单元更可教。

### 3.3 同一脚本在 T / L / W 下怎么解析、怎么求值

**S1：`read "a" |> parse |? read "b"`**

| 方案 | 解析 | 求值 |
| --- | --- | --- |
| T | `read "a" \|> (parse \|? read "b")` | `read a` 失败 → 中止，无 fallback；`read a` 成功 → `parse(v)`；`parse` 失败 → `read "b"`（不接收 v） |
| L | `(read "a" \|> parse) \|? (read "b")` | 同上。S1 不区分 T/L |
| W | 同 L，失败单元改为整个左管道 | `read a` 失败也会触发 `read "b"` |

**S2：`read "primary" |? read "fallback" |> parse`**（决定性反例）

| 方案 | 解析 | 求值 |
| --- | --- | --- |
| T | `(read "primary" \|? read "fallback") \|> parse` | `parse` **总是**执行，输入是 primary 或 fallback 的值 |
| L | `read "primary" \|? (read "fallback" \|> parse)` | primary 成功时 **`parse` 根本不执行**，`let cfg = ...` 里静默拿到原始字符串 |
| W | 同 L | 同 L：成功路径仍跳过 `parse` |

这是 L/W 的硬缺陷：一个“读配置再解析”的脚本，在配置文件存在时反而没有解析，错误延迟到下游才炸。C2 直接判 L/W 不成立。

**S3：`read "a" |> f |? g |> h`**

| 方案 | 解析 | 求值 |
| --- | --- | --- |
| T | `read "a" \|> (f \|? g) \|> h` | `h` 总是执行，输入是 `f` 或 `g` 的结果 |
| L | `(read "a" \|> f) \|? (g \|> h)` | `f` 成功时 `g` 与 `h` 都不执行——**成功路径反而少跑一步** |
| W | 同 L | 同 L |

S3 比 S2 更露骨：成功的分支被跳过后继管道。任何“`|?` 低于 `|>`”的方案都必然如此。

**S4：`$` 与 `|?` 同时出现**

```
read "cfg.json" into {
    get "server.port" |? get "server.port" $.fallback
}
```

设 `get(key, obj)` 声明 `accepts_context`。

| 方案 | 解析 | 求值（按 §3.5 的注入规则） |
| --- | --- | --- |
| T | `get "server.port" \|? get "server.port" $.fallback`，两个 call 同级 | 左：显式 1 个参数 < 形参 2 个 → 注入 `$`，`get("server.port", $)`；失败 → 右：显式 2 个 = 形参 2 个 → 不注入，`get("server.port", $.fallback)` |
| L | 左 pipe 与右 pipe 各一个 call | 同上；`$` 注入是**每次 call 独立**的，与 `\|?` 的优先级无关 |
| W | 同 L | 同 L |

结论：`$` 的先后不是 `|?` 优先级问题，是**每次调用独立注入**问题；T/L/W 在 S4 上没有差别。P0-11 把两者混在一条待定里（[讨论稿 L230](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L230)），应当拆开。

### 3.4 逐条判据

| 判据 | T | L | W | R | E |
| --- | --- | --- | --- | --- | --- |
| C1 解析确定性 | 通过（FB-L1 静态） | 勉强（“最后执行”是静态的，但“更早失败不触发”反直觉） | 通过 | 不通过（n 次重试的失败单元未定义） | 通过 |
| C2 管道连续性 | 通过 | **不通过**（S2/S3） | **不通过**（S2/S3） | 不通过（块内后续语句是否重跑未定义） | 通过（catch 后续继续） |
| C3 失败归属 | 通过（两个 call 位置） | 通过 | 通过 | 不通过（重试 n 次后报哪次？） | 通过 |
| C4 单次消费 | 通过 | 通过 | 通过 | 不通过（retry 内部再失败算谁的） | 不通过（嵌套 try 二义） |
| C5 LLM 首写 | 通过（“只保护紧挨着的那次调用”） | 不通过（自然语言读成“整条链”） | 不通过（同 L） | 不通过（多 4-6 token + 块） | 不通过（多 8+ token + 两块） |
| C6 token | 通过（1 个运算符） | 通过 | 通过 | 不通过 | 不通过 |
| C10 R4 自洽 | 通过 | 通过 | 通过 | 不通过 | **不通过**（与 v0.1 §9 “MVP 不做 try/catch” L428 直接冲突） |
| C14 终止性 | 与循环无关 | 同 | 同 | 重试次数有界 | 无界（catch 可重入） |

`retry n { fallback: ... }` 额外的问题是：`retry 3 { read "a" |> parse }` 里“重试”到底重跑整块还是最后一次调用，和 `|?` 的失败单元问题一模一样，只是乘以 n；用户已经裁掉这个形态（[讨论稿 L74](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L74)），不再展开。try/catch 与 v0.1 §9 的“MVP 不做 try/catch，错误直接冒泡”（[v0.1 L428](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L428)）正面冲突，且 CT 没有异常运行时可以借（[Diag.h.ct L74-L89](file:///Users/samxx/trae-ws/ct-lang/selfhost/ct-ast/tool/diag/Diag.h.ct#L74-L89)）。

### 3.5 `$` 隐式上下文参数的追加顺序

主张三条规则：

1. **每次调用独立注入**：`|?` 的左右两侧各自算自己的参数表，左分支的 `$` 不传给右分支。
2. **顺序**：显式参数（书写序）→ 管道值 → 隐式 `$`。`$` 在注入时恒为最后一个位置参数。
3. **按形参位决定是否注入**：设该 call 的显式+管道参数个数为 `n`，工具 schema 的固定位置形参个数为 `m`；仅在 `n < m` 时注入 `$`。`n == m` 不注入（否则多一个参数）；schema 是变长/无法确定 `m` 时不注入，要求脚本显式写 `$`。

规则 3 是为了消掉 v0.1 的自相矛盾：R2 说管道值“追加到末尾”（[v0.1 L112](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L112)），R3 说 `$` “追加到参数列表末尾”（[v0.1 L137](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L137)），两句话同时成立就没有“末尾”。按形参位决定注入后，`read "cfg" |> get "server.port"`（schema 2 个形参）得到 `get("server.port", cfg)`，不会再多塞一个 `$`；如果 schema 是 3 个形参并声明 `accepts_context`，才得到 `get("server.port", cfg, $)`。错误信息可以直接说：`schema takes 2 arguments; '$' was not injected; write '$' explicitly if this tool needs context`。

不采用“两个都无条件追加、谁先谁后”的方案：那会制造一个用户在写 `grep` 时才发现的参数错位，且 R2/R3 的“末尾”二义永远无法靠文档消除。

### 3.6 LLM 更容易写对哪一种

| 证据 | T | L / W |
| --- | --- | --- |
| 自然语言规则 | “`\\|?` 只保护紧挨着它的那一次调用”一句话 | “它保护整条左边管道，但只对最后执行的那次调用生效”——两句话且互相打架 |
| 常见意图 `read a \|? read b \|> parse` | 解析与意图一致（两个分支都 parse） | 解析与意图相反（成功时不 parse） |
| 写错时的反馈 | FB-L1 加载错误，直接给 fn 包一层的修法 | 没有语法错误，只有一个晚到的类型/形状错误 |
| token | 1 个运算符 | 1 个运算符（但不省心） |
| 与训练先验 | 类似 `a ?? b`、`a || b` 的二元运算符 | 类似 try/catch 的“块”直觉，但语法不是块，先验反而误导 |

`retry n { ... }` 与 try/catch 在 token 上就输了：多一对花括号、关键字、缩进或分号；v0.1 明确说过花括号是为了可定位（[v0.1 L39](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L39)），不是鼓励多写块。

### 3.7 失败时脚本看到什么

- **左失败、右成功**：表达式/变量的值是右分支的值与元数据；左调用的失败**不产生任何值**，脚本不能把它存起来、比较或当参数传。失败记录进内核的执行轨迹（`trace_id`，[讨论稿 P1-6 L285-L298](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L285-L298)），但 MVP 不向脚本暴露 `fallback_used` 或错误对象。
- **两边都失败**：中止当前块（R4），诊断同时列出两个调用点：

```
script.ri:3:12: error: call failed and its fallback also failed
  left : read('primary') -> not found
  right: read('fallback') -> permission denied
  Hint: check both paths, or make the fallback a tool that cannot fail.
```

- **不引入错误值**：R5 的值域是 `null/bool/number/string/json_object/json_array`（[v0.1 L158](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L158)），没有 error。把失败做成值会多出一套类型与比较语义，与“不做类型系统”（[v0.1 L426](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L426)）冲突。若庭上要求可观测，最小增量是在调用结果侧车加 `x.fallback_used`（与 §4 的元数据同一条通道），而不是错误值；这是可单独裁决的附加项，不作为 MVP 前提。

### 3.8 与 CT 的冲突

- CT **没有** `|>` / `|?`：全仓 `selfhost/ lib/ docs/language-spec.md` 检索这两个 token 零命中（命令与输出见 §7 E1-B）。词法只有六种 token（[Lexer.h.ct L18-L24](file:///Users/samxx/trae-ws/ct-lang/selfhost/ct-ast/frontend/lex/Lexer.h.ct#L18-L24)）。
- CT **没有**运行时错误：诊断是编译期 `path:line:col: error:` 并累加 `nsem`（[Diag.h.ct L74-L89](file:///Users/samxx/trae-ws/ct-lang/selfhost/ct-ast/tool/diag/Diag.h.ct#L74-L89)）。`|?` 无法脱糖成 CT 的 `?:` 或错误 flag：CT 生成的 C 里没有“每次调用一个失败位”的表示，硬塞就要改 handler 签名，等于自建运行时。
- 因此 `|?` 必须在 DSL 解释器里实现（v0.1 §10 的“解释器维护 error 标志”一行本来就是运行时机制，[v0.1 L448](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L448)），但要把它从“失败跳到 block 末尾”改为“call 级信号，`|?` 在调用点消费”，见 §6。
- 这与 CT 的 `into` 编译期脱糖不冲突，因为二者根本不是同一层：CT 的 `into` 只在编译期展开为普通 C（[language-spec L2246-L2247](file:///Users/samxx/trae-ws/ct-lang/docs/language-spec.md#L2246-L2247)），DSL 的 `into` 是解释器里的动态作用域。冲突在**文档措辞**（v0.1 L150），不在语义设计。

### 3.9 代价量化（C12）

| 项 | 文件 | 行数 | 门禁 | 回退 |
| --- | --- | --- | --- | --- |
| T 文法 + 加载检查 FB-L1/L2 | 1 个 parser 文件 + 下一版规范 1 节 | 60-100 | 无（当前仓库无构建/门禁） | 单 commit revert |
| 运行时失败信号 + `\|?` 消费 | 1 个 interp 文件 | 40-60 | 同上 | 同上 |
| 双侧失败合并诊断 | 诊断模块 | 20-30 | 同上 | 同上 |
| `$` 注入按形参位 | 调用封送 | 30-50 | 同上 | 同上 |
| 不改 | ExecLimits、ToolDef、§8 示例 | 0 | — | — |

## 4. 争点二：截断与结果元数据

### 4.1 已被用户裁掉的部分

- `limit N lines` / `head N chars` 这类 DSL 后缀：不做。理由是语法关键字会逼每个工具实现后缀式参数并与工具自己的参数名冲突（[讨论稿 L56-L61](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L56-L61)）。
- 截断控制走工具参数；DSL 只规定 `{ value, truncated, original_size }`，且字段访问必须能读到 `truncated`（[讨论稿 L58-L59](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L58-L59)）。
- 仍待定的是暴露方式 A/B/C/D（[讨论稿 P1-2 L254-L259](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L254-L259)）。我只争这一层。

### 4.2 A/B/C/D 与同一段脚本

脚本 Tr：

```
let r = read "big.log"
if r.truncated {
    write "note.txt" "partial"
}
write "copy.txt" r
```

| 方案 | `r` 是什么 | `r.truncated` | `write "copy.txt" r` | 现有 §8 示例 |
| --- | --- | --- | --- | --- |
| A 始终记录 | `{value, truncated, original_size}` | 记录字段 | 工具收到**记录对象**；必须写 `r.value`，或解释器自动拆包（第四条隐式规则） | 5 个示例都要改；每个管道左值都要定“记录还是 `.value`” |
| B 只有声明元数据的工具返回记录 | 取决于 callee | 有时是字段，有时非法 | 同上；且管道左值形状随 callee 变 | 示例部分要改；仍需“记录怎么进管道”的规则 |
| **C 绑定值 + 侧车（我的主张）** | 字符串 | 侧车伪字段 | 工具收到字符串 | **0 改动** |
| D 只在截断时返回记录 | 随数据变 | 可能是字段，可能不存在 | 随数据变 | 不可静态判断，直接否 |

A 的问题不是“多写 `.value`”这点 token，而是它把“工具边界”变成了记录边界：`read "a" |> grep "x"` 里 `grep` 要么收到记录（JSON schema 不认识），要么解释器自动拆包（新增隐式规则），二者都违反 §1 的原则 3（[v0.1 L11](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L11)）。B 把形状变成“callee 的函数”，LLM 必须记住哪些工具带元数据；它没有消除 JSON 同名冲突，只是把冲突缩小到部分工具。D 让返回形状依赖运行数据，无法写 golden，直接出局（讨论稿自己也写“不推荐”，[L258](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L258)）。

### 4.3 主张 C 的精确规则

- **R-M1（值表示）**：运行时值是 `(payload, meta)`；`payload` ∈ `null/bool/number/string/json_object/json_array`，`meta = { truncated: bool, original_size: int }`。字面量与算术结果也有 `meta`，默认 `truncated=false`、`original_size` 为序列化字节长度。
- **R-M2（工具边界）**：工具 handler 与工具参数永远只拿 `payload`。管道传值、实参封送、emit payload 都取 `payload`；`meta` 只活在解释器里。
- **R-M3（伪字段优先）**：`x.truncated` / `x.original_size` 先解析 `meta`，再解析 `payload` 的 JSON 字段。也就是说，同名 JSON 字段被遮蔽。
- **R-M4（逃逸）**：要读 JSON 自带的 `truncated` 字段，用 `get "truncated" x`。`get` 接收的是 `payload`，所以拿到的就是原字段。这是唯一的逃逸路径，写进文档与示例。
- **R-M5（传播）**：`let` 复制 `(payload, meta)`；管道把上一段的 `(payload, meta)` 传给下一段；`into` 绑定 `(payload, meta)`，`$.truncated` 可读；`fn` 返回被 `return` 表达式的 `(payload, meta)`；`|?` 返回实际胜出分支的 `(payload, meta)`。`value` **不是**字段——表达式本身就是值，这一点写死，避免出现 `.value`。
- **R-M6（粘性截断）**：`result.truncated = this_call_cut || any(input.truncated)`；`result.original_size` 若本调用切了，取本调用切前字节数；否则若任一输入 `truncated=true`，取这些输入 `original_size` 的最大值；否则取本值序列化字节数。这样 `read "huge.log"（截断） |> grep "ERROR"` 的结果仍是 `truncated=true`，不会让 agent 误判“没有错误”。
- **R-M7（单位）**：`original_size` 用 UTF-8 字节，与 `ExecLimits.max_output_bytes` 同口径（[v0.1 L292](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L292)）。行数/字符数是工具自己的参数或返回字段，不进通用元数据。
- **R-M8（静态合法性）**：因为所有值都有 `meta`，`x.truncated` 在任何值上都合法；`x.trunc` 这种拼错走普通字段查找，由 Did-you-mean 提示 `truncated`（P1-3，[讨论稿 L261-L268](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L261-L268)）。这条让 C8 成立：不需要运行时类型探测。
- **R-M9（内联读元数据要分组）**：`read "big" .truncated` 在“实参是 postfix 原子”的规则下会解析成 `read("big".truncated)`，不是“对调用结果取字段”（[讨论稿 P0-3 L120-L136](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L120-L136)）。要内联读就写 `(read "big").truncated`；更推荐先 `let`。这条必须写进错误提示，否则 LLM 必踩。

### 4.4 为什么是侧车而不是内置 `meta x`

- 用户要求“字段访问必须能读到 `truncated`”（[讨论稿 L59](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L59)），`x.truncated` 是最短路径；`meta x` 多一个内置名、多 2 token，而且仍然要求元数据挂在值上，等于同一套机制的另一种写法，MVP 不该有两种写法。
- “只记日志”不满足用户要求：脚本无法据此决定是否继续（agent 的核心用途就是看截断后改策略），否。
- “工具参数”只能控制截断，不能报告截断，继续保留为控制手段，不是暴露手段。

### 4.5 与 CT 的冲突

- CT 没有动态值：`null/bool/number/string/json_object/json_array` 不在 CT 的类型系统里；`lib/std` 只有 `Vec.h.ct` 与 README，没有 `Map`、没有 `json_get`（[讨论稿 §5 L359-L360](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L359-L360)；目录实测见 §7 E1-B）。所以侧车元数据只能是 DSL 解释器的值表示，不能“复用 CT 的 trait/struct 语义”。
- v0.1 §10 的“字段访问 `x.a.b` 调 ct-json 的 `json_get`，返回 borrow 或 null”（[v0.1 L447](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L447)）是**事实错误**：仓库没有 `ct-json`，也没有 `json_get`。这条与 B2-2 直接相关：伪字段必须在任何 JSON 访问之前解析，否则 C9 的逃逸路径不成立。下一版规范应把它改成“DSL 运行时自有的 JSON 访问 + 侧车伪字段优先”。
- 与“into 是编译期脱糖”不冲突：侧车是解释器值表示，`into` 在 DSL 里也是解释器作用域；冲突仍在措辞（v0.1 L150），见 §5.4。

### 4.6 代价量化

| 项 | 文件 | 行数 | 说明 |
| --- | --- | --- | --- |
| 值表示加 `meta` | 1 个运行时头/源 | 40-60 | 每个值 8-16 字节，或按需分配 |
| 字段解析先查 `meta` | 字段访问 | 20-30 | 一行优先级 |
| 封送取 `payload` | 调用/管道 | 10-20 | 规则唯一 |
| 粘性截断 | 调用结果合并 | 20-30 | OR + max |
| `get` 逃逸 | 文档 + 1 个内置工具 | 0 代码（已有 get） | — |
| §8 示例改动 | 0 | 0 | C 的核心卖点 |
| ToolResult 增加三字段 | `v0.1 §6.1` 接口 | 3 字段 | `value/truncated/original_size` 由 handler 填 |

## 5. 争点三：while / break / continue 与 `x = expr`

### 5.1 主张

1. 引入赋值语句 `IDENT "=" expr`，但**只能写 `let mut` 声明的同一函数帧局部变量**。
2. 普通 `let` 不可变。`let` / `let mut` / fn 参数 / `for` 变量是**唯一**的绑定引入点；赋值只存不建名。
3. `for` 循环变量是每轮一个**不可变的值拷贝**；要改就 `let mut v = item`。
4. `break` / `continue` 进 M4，只能出现在循环体内，不能跨 `fn` 边界。
5. **`while` 不进 MVP**；用 `for` + 工具级 wait/paginate + `|?` 覆盖。

### 5.2 “let 是唯一定义点”会不会被破坏

不会，前提是把“定义”与“存储”分开：

- `let x = 1` / `let mut x = 1` 是**绑定引入**，一个作用域内同名二次 `let` 报错（`'x' is already declared in this scope`）。嵌套块可以遮蔽，这是词法作用域的常规行为。
- `x = 2` 是**对既有绑定的存储**，不是新定义。加载期三条检查：
  - **AS-L1** 目标必须能解析到当前函数帧的局部绑定；解析不到 → `assignment to undefined name 'x'; add 'let x = ...'`。
  - **AS-L2** 目标必须是 `let mut`；否则 → `assignment to immutable 'x'; declare it with 'let mut x = ...'`（行/列指向赋值号）。
  - **AS-L3** 赋值是语句，不是表达式；`if x = 1 {` 在 `=` 处报语法错误，提示 `use '==' to compare`。这直接消灭 C 语言最经典的 `if (x = 1)` 事故。
- 闭包只读：R6 已规定函数内读外层变量是只读（[v0.1 L179](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L179)），所以 **AS-L4** 目标不能是捕获变量；否则 → `cannot assign to captured variable 'x'; pass it as a parameter or return the new value`。
- `$` 不可赋值：R3 规定 `$` 在 into 块内只读（[v0.1 L136](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L136)），**AS-L5** `$ = ...` 报错。注意 CT 的 `into` 允许 `$ = expr` 重新绑定（[language-spec L2231](file:///Users/samxx/trae-ws/ct-lang/docs/language-spec.md#L2231)），这正是不能声称复用 CT 语义的又一证据。

### 5.3 同一段脚本在两种方案下

**方案 M1（可变 `let`，无 `mut`）**

```
let total = 0
for n in nums {
    total = total + n
}
```

解析：`let` 绑定可变；`assign_stmt` 直接写。求值：正常累加。代价：`total` 在任何后续行都可能被改，静态阅读失去“这个名字从此不变”的保证；拼错 `totl = ...` 仍会被 AS-L1 抓住，但误写不会。

**方案 M2（我的主张：`let` 不可变，`let mut` 可变）**

```
let mut total = 0
for n in nums {
    total = total + n
}
```

若 LLM 漏写 `mut`：

```
script.ri:3:5: error: assignment to immutable 'total'
  Hint: declare it with 'let mut total = 0'.
```

解析/求值同 M1，只多一个关键字。判据：C5 —— M2 的失败是加载期、可精确纠正；M1 的失败是运行期或根本不被发现。C6 —— 只有被赋值的绑定多 1 token，v0.1 §8 的 5 个示例没有一个需要 `mut`，token 成本为 0。C12 —— 词法多一个上下文关键字、parser 多一条 `assign_stmt`、loader 多三条检查，可单切片回退。

### 5.4 `while` 为什么不做

| 论据 | 证据 |
| --- | --- |
| 重试已被用户裁给工具参数，脚本内最常见的 `while` 用途消失 | [讨论稿 L76](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L76) |
| 轮询/等待应由工具承担并带自己的 `timeout_ms`；DSL 阻塞在脚本里会拖垮单次执行 | `ExecLimits.timeout_ms`（[v0.1 L293](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L293)）、P1-11 的超限语义（[讨论稿 L343](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L343)） |
| `while true {}` 的终止性只能靠 `max_steps` 粗粒度兜底；空体循环的步数口径、`continue` 是否计步都要额外定义 | C14 |
| v0.1 的能力边界是“工具 + 数据流 + 条件 + 上下文 + 函数 + 事件”六件事，越界语法要有明确收益 | [v0.1 L516](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L516) |
| LLM 的经典 bug 是忘记更新条件导致死循环；没有 `while` 就写不出这个 bug | C5 |
| 评审建议进 M4（[讨论稿 L240](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L240)）是“能力主张”，不是“必须有消费者”的证据；当前没有任何任务样例要求脚本内循环 | 仓库无实现、无任务集（S-001 L36） |

**重开条件（可证伪）**：出现一个具名真实任务，满足以下全部条件，则我把 `while` 放回 M4：

1. 该任务不能用 `for` + 工具级 wait/paginate + `|?` 表达；
2. 该任务必须在单次 `dsl_exec` 内完成，不能交给内核主循环；
3. 能写出循环预算规则（每次迭代计一步，`continue` 也计步，超限返回 `ok=0 + error_kind=limit`）。

届时 `while` 不带任何额外关键字；`break`/`continue` 规则同 §5.5。若庭上现在就坚持要 `while`，我接受的最小形态是：`while expr block`，每次迭代至少计 1 步，`ExecLimits` 不新增字段，空体循环也必然终止于 `max_steps`。

### 5.5 `break` / `continue`

- **BC-L1**：只能在 `for`（以及未来若放行的 `while`）体内；否则加载错误 `'break' outside a loop` / `'continue' outside a loop`。
- **BC-L2**：不能跨 `fn` 边界。`for ... { fn f() { break } }` 报 `'break' cannot cross a function boundary`；`fn` 是独立的失败/返回边界，和 R4 的 fn 规则一致。
- **BC-L3**：`into` / `if` 不是 handler 边界，循环体里的 `into { break }` 作用于最近的外层循环。这条要写死，否则 `into` 会被误当成 try 块。
- **BC-L4**：`break` / `continue` 是语句，不能出现在表达式位置；`let x = break` 报语法错误。

### 5.6 ExecLimits

不新增字段。`max_steps` 的计数口径补两句：每个循环迭代至少 +1（空体也不例外），`continue` 不重置计数；`timeout_ms` 是墙钟兜底。这样 `while true {}`（若未来放行）与 `for x in huge {}` 都在 `max_steps` 处终止，返回 `ok=0 + error_kind=limit`，与 P1-11 的超限语义一致（[讨论稿 L343](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L343)）。

### 5.7 与 CT 的冲突

- CT 的 `foreach` 把循环变量按**值拷贝**绑定，写 `item` 不回写容器（[language-spec L1987](file:///Users/samxx/trae-ws/ct-lang/docs/language-spec.md#L1987)、[L2005-L2006](file:///Users/samxx/trae-ws/ct-lang/docs/language-spec.md#L2005-L2006)）。DSL 的 `for` 采用同一心智模型：每轮不可变的值拷贝，要改就 `let mut v = item`。这与项目已裁的“item 值拷贝”硬约束一致。
- CT 的 `break`/`continue` 是普通 C 跳转，并负责释放 autodrop 变量（[language-spec L2011-L2012](file:///Users/samxx/trae-ws/ct-lang/docs/language-spec.md#L2011-L2012)）。DSL 没有 `own`/Drop，所以只借“普通跳转”的形态，不借释放语义。
- CT 有 C 风格 `while`，但 DSL 不是 CT 的子集；不能因为 CT 有就默认 DSL 要有。反过来，CT 没有 `let mut`（C 风格声明），所以 M2 是 DSL 独有规则，不需要 CT 支撑。

### 5.8 代价量化

| 项 | 文件 | 行数 | 说明 |
| --- | --- | --- | --- |
| `let mut` 词法/文法 | lexer + parser | 20-30 | 一个上下文关键字 |
| AS-L1..L5 加载检查 | loader | 40-60 | 每条一个可读错误 |
| BC-L1..L4 加载检查 | loader | 30-40 | 静态可判 |
| 赋值求值 | interp | 15-25 | 只写已有槽位 |
| 不做 `while` 省下 | interp + 规范 + golden | 150-250 | 含空体、嵌套、continue 计步 |
| 示例改动 | 0 | 0 | §8 没有循环 |

## 6. 争点四：引入 `|?` 之后的 R4

### 6.1 新表述（替换 v0.1 §4 R4，L152-L154）

- **R4.0** 运行时失败是**控制信号**，附着在产生它的那次 call 上；它不是值，不能存变量、比较或当参数。
- **R4.1** 信号沿求值向外传播到最近的块边界（`if`/`for`/`into`/`fn` 体）；该块中止，信号继续向外。
- **R4.2** 唯一的消费者是 `|?`，且只消费**它左侧那个 call** 产生的信号。左调用成功时右操作数不执行（串行模型，R1）。
- **R4.3** 右操作数也失败时，信号继续向外，诊断同时给出两侧调用的位置（§3.7 的合并诊断）。
- **R4.4** `|?` 不是 handler 作用域：它不捕获更早管道阶段的失败，不捕获外层块的失败，也不给右操作数“兜底其内部嵌套调用”的额外能力。只有左 call 的信号归它。
- **R4.5** `fn` 边界：fn 体内失败中止 fn 体，该 **fn 调用**失败；调用方的 `|?` 可以消费它。于是“整条链兜底”可以用 `fn load() { ... }` + `load() |? fallback` 表达，粒度由用户选择，不需要 W 方案。
- **R4.6** 没有 try/catch、没有错误值、没有恢复执行。一个失败要么中止块，要么被恰好一个 `|?` 变成值。

这样 R4 仍是“默认中止整块”，只是补了“唯一例外及其边界”；不再出现“默认中止”与“`|?` 能捕获”两套互相否定的句子。`|?` 是**调用级恢复**，不是异常处理。

### 6.2 同一脚本在旧/新 R4 下

```
fn load(p) {
    let c = read p
    c |> json_parse
}
let cfg = load "cfg.json" |? load "default.json"
if cfg != null { write "ok.txt" cfg }
```

| 情形 | 旧 R4（无 `\|?`） | 新 R4 |
| --- | --- | --- |
| `cfg.json` 不存在 | `read` 失败 → `load` 体中止 → 顶层块中止，脚本看到 `DslResult.ok=0` | `load "cfg.json"` 这个 call 失败 → `\|?` 消费 → 调 `load "default.json"`；成功则继续 `if` |
| 两个都不存在 | 同上，只报第一个 | 顶层中止，诊断同时列 `load` 的左/右两次调用的内部失败位置 |
| `cfg.json` 存在但 JSON 坏 | 旧 R4 一样中止 | `json_parse` 在 `load` 体内失败 → fn 调用失败 → `\|?` 消费 → 尝试 default。**这是 fn 粒度的收益**，不是 W 的收益 |
| `cfg.json` 与 default 都好 | 正常 | 左成功，右不执行 |

旧 R4 的唯一矛盾句是“工具调用失败时默认中止当前 block”与“`|?` 捕获”并列；新 R4 用 R4.2/R4.4 把“捕获”限定为“左侧 call 的信号”，矛盾消失。W 方案看似更宽容，但它让“哪里失败”决定“整条链是否重来”，与 R4.5 的 fn 粒度重复，且违反用户“一次调用”的裁定（[讨论稿 L75](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L75)）。

### 6.3 下一版规范要改的行（v0.1 原文保留）

| 位置 | 现文 | 改法 |
| --- | --- | --- |
| v0.1 §4 R4 L152-L154 | “工具调用失败时，默认中止当前 block……MVP 不做 try/catch” | 换成 §6.1 的 R4.0-R4.6；保留“默认中止”，把 `\|?` 写成唯一调用级恢复 |
| v0.1 §9 L428 | “异常处理：MVP 不做 try/catch，错误直接冒泡” | 改成“除 `\|?` 的调用级恢复外，错误直接冒泡” |
| v0.1 §10 L448 | “错误传播：解释器维护 error 标志，失败跳到 block 末尾” | 改成“call 级失败信号；`\|?` 在调用点消费；其余跳到 block 末尾” |
| v0.1 §10 L150 | “直接复用 CT 的 into scope 语义……共享同一套逻辑” | 撤回；改为“只借表面形态，DSL 自建动态作用域” |
| v0.1 §10 L447 | “字段访问调 ct-json 的 json_get” | 改为“DSL 运行时自有 JSON 访问；侧车伪字段优先”；仓库无 `ct-json` |
| v0.1 §2 L25 | 词法只有 `\|>` | 增加 `\|?` |
| v0.1 §4 R2 L112 / R3 L137 | 两处都称“追加到末尾” | 改为“显式 → 管道 → `$`；按形参位决定是否注入 `$`” |
| v0.1 §11 L453-L484 | 只有单点错误示例 | 增加 §3.7 的双侧失败诊断 |

## 7. 举证（E1-E5，AGENTS §7.7 L807-L817）

### 7.1 E1 可复制命令与原始输出

环境：`Darwin 27.2.0 arm64`；rill-dsl `033e5860406b91bbf226a5aa42a1818d520d28c0`；ct-lang `da83aded69c78fdc377e4d3f2e31595709f1c8d2`；只读工作树（rill-dsl 仅有未跟踪的 `battle/`）。

**E1-A：本仓关键行原文**

```sh
cd /Users/samxx/trae-ws/rill-dsl && echo '--- discussion 222,224-230' && sed -n '222p;224,230p' docs/design/dsl-discussion.md && echo '--- spec 150,152-154,428,447-448' && sed -n '150p;152,154p;428p;447,448p' docs/design/dsl-spec-v0.1.md && echo '--- discussion 76-78' && sed -n '76,78p' docs/design/dsl-discussion.md
```

原始输出（逐字）：

```
--- discussion 222,224-230
评审意见：`|?` 优先级低于 `|>`；失败单元是一次工具调用，不是整个左表达式。
我方倾向（提案）：

- `expr := fallback_expr`；`fallback_expr := pipe_expr ("|?" pipe_expr)*`，左结合；
- `pipe_expr` 内部才是 `|>`；
- 失败单元 = 左侧管道**最后执行的那次工具调用**；左侧更早的调用失败不触发右侧；
- 右侧独立求值，不接收左侧的管道值；
- 与 `$` 同时出现时的追加顺序仍待定（见 P1-2）。
--- spec 150,152-154,428,447-448
into 与 CT 的映射：DSL 的 into 直接复用 CT 的 into scope 语义和 $ 绑定，parser 和 scope resolution 共享同一套逻辑。
R4：错误传播

工具调用失败时，默认中止当前 block 并向上传播（类似 Rust ?）。if/for/into/fn 块内失败，整个块中止。MVP 不做 try/catch。
· 异常处理：MVP 不做 try/catch，错误直接冒泡。
字段访问 x.a.b 调 ct-json 的 json_get，返回 borrow 或 null
错误传播 解释器维护 error 标志，失败跳到 block 末尾
--- discussion 76-78
- 需要重试次数时，用工具参数表达，不新增语句形态。

仍待定：`|?` 的优先级、失败单元、右侧是否允许整条管道、与 `$` 隐式参数的先后顺序（见 §3 P0-11、§4 P1-2）。
```

```sh
cd /Users/samxx/trae-ws/rill-dsl && echo '--- discussion 74-75' && sed -n '74,75p' docs/design/dsl-discussion.md
```

```
--- discussion 74-75
- 不采用 `retry n { fallback: ... }` 这种花括号形态。
- 降级统一走 `|?`（左侧的一次工具调用失败则尝试右侧）。
```

**E1-B：CT 侧事实**

```sh
cd /Users/samxx/trae-ws/ct-lang && grep -rn --include='*.ct' --include='*.md' -e '|>' -e '|?' selfhost lib docs/language-spec.md; echo "grep_rc=$?"
```

```
grep_rc=1
```

```sh
cd /Users/samxx/trae-ws/ct-lang && echo '--- Expr 2903-2906' && sed -n '2903,2906p' selfhost/ct-ast/frontend/parse/Expr.h.ct && echo '--- Expr 2929-2933' && sed -n '2929,2933p' selfhost/ct-ast/frontend/parse/Expr.h.ct && echo '--- Expr 4715-4730' && sed -n '4715,4730p' selfhost/ct-ast/frontend/parse/Expr.h.ct && echo '--- spec 2243-2247' && sed -n '2243,2247p' docs/language-spec.md && echo '--- Diag 78-88' && sed -n '78,88p' selfhost/ct-ast/tool/diag/Diag.h.ct && echo '--- Lexer 18-24' && sed -n '18,24p' selfhost/ct-ast/frontend/lex/Lexer.h.ct && echo '--- lib/std' && ls lib/std
```

原始输出（逐字）：

```
--- Expr 2903-2906
            if (self->into_node >= 0) {
                tool::diag::ct_sem_error(line, col,
                    "nested 'into' blocks are not supported", self->sup->mem->path);
                return -1;
--- Expr 2929-2933
            if (type[0] == 0) {
                tool::diag::ct_sem_error(line, col,
                    "cannot determine the receiver type of this 'into' block",
                    self->sup->mem->path);
                return -1;
--- Expr 4715-4730
        /* Phase 24: the range index. `$` has no C spelling of its own -- the
           emitter renders it as `((int)<k>)` -- so it never reaches the symbol
           table; outside the element expression of a range initialiser it is a
           syntax error, never an undeclared name. */
        if (self->lex->tok == T_PUNCT && strcmp(self->lex->toktext, "$") == 0) {
            /* Phase 30: inside an `into` block `$` is the receiver itself. */
            if (self->into_node >= 0) {
                n = self->sup->new_node(N_INTO_SELF);
                if (n < 0) return -1;
                self->arena->nodes[n].num = self->into_node;
                snprintf(self->arena->nodes[n].text, MAX_TEXT, "%s",
                         self->arena->nodes[self->into_node].text);
                self->sup->lex_next();
                return n;
            }
            if (!self->dollar_ok) return self->sup->fail("unexpected token");
--- spec 2243-2247
- **诊断**：L30-1 位置不允许、L30-2 接收者形态不对、L30-3 静态类型未知、L30-4 接口值或
  `own` 接收者、L30-5 已知成员表里没有该字段、L30-6 语句形态用了右值接收者、
  L30-7 嵌套 `into` 块。
- **不引入运行时**：块、`.name` 与 `$` 在编译期完全脱糖为普通 C 语句与普通调用；
  生成物里不出现 `into {`、`$`，接收者表达式只出现一次。
--- Diag 78-88
    int sem_error(int line, int col, const char *msg, const char *path)
    {
        (void)self;
        fprintf(stderr, "%s:%d:%d: error: %s\n", path, line, col, msg);
        self->nsem++;
        /* past the cap the reports are cascades of the first few, not news */
        if (self->nsem > MAX_ERRORS) {
            fprintf(stderr, "ctc: too many errors, stopping\n");
            exit(1);
        }
        return -1;
--- Lexer 18-24
#define MAX_TEXT   160
#define T_EOF    0
#define T_ID     1
#define T_NUM    2
#define T_STR    3
#define T_PUNCT  4
#define T_PP     5
--- lib/std
README.md
Vec.h.ct
```

**E1-C：仓库状态**

```sh
uname -srm && cd /Users/samxx/trae-ws/rill-dsl && git status --porcelain | head -5 && git rev-parse HEAD && cd /Users/samxx/trae-ws/ct-lang && git rev-parse HEAD
```

```
Darwin 27.2.0 arm64
?? battle/
033e5860406b91bbf226a5aa42a1818d520d28c0
da83aded69c78fdc377e4d3f2e31595709f1c8d2
```

### 7.2 E2 锚点（支持与不利各列）

**支持我的锚点**

| 锚点 | 内容 | 支撑点 |
| --- | --- | --- |
| [讨论稿 L75](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L75) | “降级统一走 `\|?`（左侧的一次工具调用失败则尝试右侧）” | 失败单元是“一次调用”，不是整条左管道 |
| [D-001 L29-L33](file:///Users/samxx/trae-ws/rill-dsl/docs/decisions/D-001.md#L29-L33) | 工具与用户函数统一为一个 call 节点 | call 级单元自然包含 `fn` 调用，R4.5 成立 |
| [v0.1 L11](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L11) | 只保留三条隐式规则 | 拒绝 A/B 的记录自动拆包与“按工具切换形状” |
| [language-spec L2246-L2247](file:///Users/samxx/trae-ws/ct-lang/docs/language-spec.md#L2246-L2247) | CT 的 `into` 编译期完全脱糖 | 撤回 v0.1 L150 的“共享 parser/scope” |
| [language-spec L1987](file:///Users/samxx/trae-ws/ct-lang/docs/language-spec.md#L1987)、[L2005-L2006](file:///Users/samxx/trae-ws/ct-lang/docs/language-spec.md#L2005-L2006) | `foreach` 的 `item` 是值拷贝、不回写 | `for` 变量不可变的心智模型 |

**不利于我的锚点**

| 锚点 | 内容 | 我如何回应 |
| --- | --- | --- |
| [讨论稿 L222](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L222) | 评审意见：“`\|?` 优先级低于 `\|>`；失败单元是一次工具调用” | “一次工具调用”与“低于 `\|>`”组合起来就是我说的 L 方案，S2/S3 会破坏管道连续性；优先级必须反过来，失败单元保留 |
| [讨论稿 L224-L230](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L224-L230) | P0-11 的 `pipe_expr ("\|?" pipe_expr)*` 提案 | 这是 L 方案；它的 §6.3 示例（[L452](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L452)）已经显示右侧是整条 pipe，正好触发 S2/S3 |
| [v0.1 L112](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L112)、[L137](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L137) | 管道值与 `$` 都“追加到末尾” | 两句同时成立没有“末尾”；我的“按形参位决定是否注入 `$`”是消除二义，不是新增偏好 |
| [讨论稿 L259](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L259) | 截断暴露倾向 B 或 C | 我只赢一半：B 是 C 的竞争者，见 §4.2 的管道形状反驳 |
| [讨论稿 L240](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L240) | 评审建议 `while` 进 M4 | 我用“重试已裁给工具、轮询应在工具里”对抗；这是我的主张里最可能被判不成立的一条，见 §8 |
| [讨论稿 L244](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L244) | 倾向允许对已声明局部变量赋值 | 支持赋值，但不支持我加的 `let mut`；`let mut` 是本文的额外限制，没有既有文本背书 |

### 7.3 E3 可证伪预测（M1/M3 落地后一次验证）

| # | 输入 | 预期（T + C + M2） | 若不符，说明 |
| --- | --- | --- | --- |
| P1 | `read "missing" \|> parse \|? read "b"` | `read` 失败，`\|?` 不触发，块中止；错误在 `read` 的行列 | 若触发了 fallback，说明实现把失败单元做成了整个左管道（W） |
| P2 | `read "primary" \|? read "fallback" \|> parse` | `parse` 总执行；primary 是坏 JSON 时在 `parse` 处失败 | 若 primary 成功时 `parse` 不执行，说明用了 L |
| P3 | `(read "a" \|> parse) \|? read "b"` | 加载错误 FB-L1，提示用 `fn` 包住链 | 若被接受，说明允许了管道级左操作数 |
| P4 | `read "big.log"` 被截断后 `grep "ERROR"` | 结果的 `truncated=true`；`original_size` 是源文件切前字节数 | 若为 false，说明截断没做粘性（C13 失败） |
| P5 | `let r = read "big"; write "copy" r` | `write` 收到字符串；`r.truncated` 可读 | 若收到 `{value,...}`，说明走了 A/B |
| P6 | `let x = 0` 后 `x = 1` | 加载错误 AS-L2，提示 `let mut x = 0` | 若通过，说明 `let` 默认可变（M1） |
| P7 | `for n in nums { n = 1 }` | 加载错误 AS-L2（循环变量不可变） | 若通过，说明 `for` 变量可变 |
| P8 | `while true {}` | 加载错误“while 不在本版本”，提示 `for`/工具级 wait | 若被接受且无预算，C14 失败 |
| P9 | `into { get "k" \|? get "k" $.d }`，`get(key,obj)` 声明 `accepts_context` | 左 `get("k", $)`；右 `get("k", $.d)`；右侧不额外注入 `$` | 若右侧变成 3 个参数，说明注入未按形参位 |

### 7.4 E4 代价量化

| 项 | 文件数 | 行数 | 影响门禁 | 回退步骤 |
| --- | --- | --- | --- | --- |
| T 文法 + FB-L1..L4 | 2（parser + 下一版规范） | 80-130 | 无（仓库无构建/门禁） | revert 该切片 commit |
| `\|?` 运行时 + 合并诊断 | 2（interp + diag） | 60-90 | 无 | 同上 |
| `$` 按形参位注入 | 1（调用封送） | 30-50 | 无 | 同上 |
| C 侧车元数据 | 2-3（值表示 + 字段 + 封送） | 90-140 | 无 | 同上；可先只做 `truncated`，`original_size` 后补 |
| `let mut` + AS-L1..L5 | 3（lexer/parser/loader） | 60-90 | 无 | 同上 |
| BC-L1..L4 | 1（loader） | 30-40 | 无 | 同上 |
| 不做 `while` | 0（省） | 省 150-250 | 无 | 不需回退 |
| R4 重述 | 1（下一版规范）+ 1（诊断文案） | 30 | 无 | 纯文档 |

总计：净增约 380-540 行实现 + 约 120 行规范/示例；不改 `ExecLimits`、不改 `ToolDef`、不改 D-001、不改 §8 的 5 个示例。所有切片可独立 revert，仓库始终保持可构建（当前无构建，因此以“文档自洽 + golden 未定”为可构建口径）。

### 7.5 E5 对最强反方论点的 steelman 回应

1. **“`|?` 低于 `|>` 更符合 try/else 直觉”**（原文：[讨论稿 L222](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L222)）。
   Steelman：`read "primary" |? read "fallback" |> parse` 读起来就是“先试主路径，不行再走备路径，然后解析”，把 `|?` 放低、右侧吃整条 pipe，正好表达“整条备路径”。
   回应：这个读法在**成功路径**上会跳过 `parse`（S2），在 `read a |> f |? g |> h` 上会跳过 `h`（S3）。“备路径”不等于“成功路径少跑一步”。如果确实要整条链兜底，用 `fn load() { ... }` + `load() |? fallback`（R4.5），语义显式、粒度更粗但不破坏管道。优先级反过来不牺牲表达力，只牺牲一个会静默出错的写法。
2. **“B 更局部、可静态校验”**（原文：[讨论稿 L259](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L259)）。
   Steelman：只有声明元数据的工具返回记录，其他工具不受影响；registry 在加载期已知，所以 `r.truncated` 的合法性可以静态判定。
   回应：B 的静态校验只解决“字段是否存在”，没解决“记录怎么进管道”：`read`（记录）`|> grep` 要么把记录塞给 schema，要么解释器自动拆包（第四条隐式规则）。C 的侧车对工具边界零影响，`x.truncated` 对所有值都合法（R-M8），静态性更强。
3. **“`while` 是 agent 的刚需”**（原文：[讨论稿 L240](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L240)）。
   Steelman：轮询任务状态、分页拉取、重试都要循环；没有 `while` 的 DSL 表达力不足。
   回应：重试已被用户裁给工具参数（L76），轮询应由工具带 `timeout_ms` 完成，分页应由工具返回 `next_cursor` 而不是脚本里 `while`。这三类都不需要在单次 `dsl_exec` 里写循环。我的重开条件是具名任务 + 无法用 `for`/工具表达 + 可写预算规则（§5.4），不是永久拒绝。
4. **“`let mut` 多一个关键字，LLM 会忘”**（原文没有直接文本，这是对 M1 的自然辩护；[讨论稿 L244](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L244) 只倾向“允许赋值”）。
   Steelman：少一个关键字就少一个错误源；Rust 的 `mut` 对不熟 Rust 的模型反而是负担。
   回应：忘写 `mut` 得到的是**加载期**、带修法的错误（AS-L2），一次就能改对；默认可变得到的是**无提示**的状态变化，`let` 的唯一定义点消失，后续阅读与静态检查都变弱。C5 的判据是“首次写对率”，不是“首次通过率”；M2 把一个隐性约定变成显式检查。
5. **“A 更显式，`.value` 一眼看出这是结果记录”**（原文：[讨论稿 L254](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L254)）。
   Steelman：显式信封让“值”和“元数据”永远不混，脚本作者不会误以为 `r` 是裸值。
   回应：显式的代价是每个工具边界都要拆包，而工具 schema 不认识信封；这不是“更显式”，是把解释器内部表示泄漏给用户与工具两侧。C 的 `x.truncated` 已经足够显式地表达“我在读元数据”，且不改变任何既有脚本。

## 8. 我可能错在哪

1. **T 的 FB-L1 可能过严**。如果 M1 的真实 LLM 语料里 `(a |> b) |? c` 出现频率很高，说明“整条链兜底”是主流意图；那时应重新评估 W，或在加载期把分组管道自动改写成 `fn` 调用（隐式改写是我现在明确反对的，但数据可能逼我让步）。
2. **粘性截断（R-M6）可能超出用户原意**。用户只说“DSL 只规定 `{value, truncated, original_size}`”，可能期望 `truncated` 描述**本次调用**，而不是血缘。若庭上裁定为 per-call，`grep` 洗白上游截断的风险需要另一个机制（例如解释器在消费 `truncated=true` 的值时向内核发告警），否则 C13 落空。
3. **`let mut` 可能是不必要的摩擦**。如果真实脚本里“声明后赋值”的比例很低、而漏写 `mut` 的比例很高，M1 的 token/错误率数据会支持“默认可变 + 仅禁止隐式创建”。我把 C5 押在“精确错误优于隐性状态”上，这个偏好可被数据推翻。
4. **不做 `while` 可能过头**。我的重开条件依赖“具名真实任务”，这在没有任务集的当前仓库里不可证伪；如果庭上认为“可等待的工具”本身还没落地，`while` 就是唯一可用的轮询手段，那我应该让步到“带步数预算的 `while`”，而不是坚持不做。
5. **`$` 按形参位注入依赖 schema 质量**。如果工具 schema 普遍是变长或描述不全，`n < m` 判不出来，规则退化成“永远要求显式 `$`”，用户会觉得隐式上下文没用；那时应回到“无条件注入 `$` 且禁止 pipe+accepts_context 同调用”（一个静态禁令），而不是猜 arity。
6. **FB-L4（实参求值失败算该 call 失败）可能过度捕获**。如果 `f (g "x") |? h` 里 `g` 的失败被 `f` 的 `|?` 吃掉，诊断会指向 `f` 而不是 `g`，LLM 可能改错地方。若证据显示归属混乱，应收窄为“只捕获 handler 失败”，让嵌套调用失败直接冒泡。
7. **CT 可能最终还是运行时宿主**。我按“CT 只当实现语言”推进（与讨论稿 §5 结论一致，[L364](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L364)）；如果项目后续决定把 DSL 编译成 CT 而不是解释执行，`|?`、动态值、侧车元数据都要重新设计成 CT 可表达的形态，本文的运行时假设会整体失效。
8. **所有运行期判据目前都不可执行**。仓库没有 lexer/parser/解释器/门禁（[S-001 L36](file:///Users/samxx/trae-ws/rill-dsl/docs/spec/S-001-call-form.md#L36)），所以 C1-C14 里只有文档层与 CT 事实层现在可判；P1-P9 是设计期预测，不是已复现证据。若裁判按 AGENTS H-3（命令+输出+环境三样齐全）严格执行，本主张在运行期判据上只能记 `undecidable`，不能记 `upheld`。
