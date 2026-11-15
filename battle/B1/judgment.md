# B1 语法消歧 — 裁判判决

- battle：B1
- judge：EDITOR（裁判席）
- 立案依据：AGENTS.md §7.2 B-5（用户指定 `battle: B1/B2/B3`）
- 审理对象：`battle/B1/seats/advocate.md`、`battle/B1/seats/challenger.md`、`battle/B1/seats/pragmatist.md`
- 基线：`rill-dsl` HEAD `033e5860406b91bbf226a5aa42a1818d520d28c0`（工作树仅 `?? battle/`）；`ct-lang` 当前 HEAD `6c21f26d505fff782d4f51e4d20a95f6710794f8`
- 已拍板前置：D-001（调用统一空格、括号只分组），不复审

---

## 1. 争点

| ID | 争点 | 席位分歧 |
| --- | --- | --- |
| B1-1 | 实参文法：`arg := primary`（递归空格应用）还是 `arg := postfix_atom`（不递归） | 主张席与反证席均选 postfix_atom；成本席选同一实质（称 `postfix_expr`），排序 B < A' < A |
| B1-2 | 数字字面量是否带负号 | 三席一致：无符号 + 一元 `-` |
| B1-3 | 是否引入 NEWLINE 作语句终止符 | 三席一致：引入；细则数量不同（5 条 / 7 条） |
| B1-4 | postfix `()` 去留 | 三席一致：删除；零参调用写法有分歧（主张席裸名 + 载入期判定，反证席要求写死作用域顺序） |
| B1-5 | emit 对象字面量产生式 | 主张席与反证席均选 emit-only JSON；冲突点：payload 是否必须单行、值位是否允许任意 `expr` |

---

## 2. 判据（逐条）

| 争点 | # | 判据 | 判定方式 |
| --- | --- | --- | --- |
| B1-1 | J1 | 给定 token 流只有一棵 AST，且不依赖运行期工具 arity | 形式推导 |
| B1-1 | J2 | `read "path"`、`grep "a" "b"` 的 token 数不增 | 计数 |
| B1-1 | J3 | `read path.field` 绑为 `read(path.field)` | 文法推导 |
| B1-1 | J4 | 嵌套调用与表达式实参各只有一种写法 | 文法推导 |
| B1-2 | J5 | `a-1`、`x-1`、`1-2`、`f 1-2` 一律按减法解析 | 词法最大吞噬推导 |
| B1-2 | J6 | 负数实参有确定写法且错误可纠正 | 文法 + 错误文案 |
| B1-3 | J7 | `read "a"` 换行 `"b"` 可表达为两条语句 | 推导 |
| B1-3 | J8 | `{}` 内语句可切分；`()`/`[]` 内与管道续行不误报 | 规则覆盖 |
| B1-3 | J9 | `}`/`else`、`if x` 换行 `{` 有定义；源码 token 不增 | 规则 + 计数 |
| B1-4 | J10 | 不产生 `f()()`、`a.b()` 这类不可求值链 | 文法推导 |
| B1-4 | J11 | `f(a)` 与 D-001 的“调用 + 分组实参”一致 | 与 S-001 §2 对齐 |
| B1-4 | J12 | 零参调用有确定且不依赖空的写法 | 名字解析规则 |
| B1-5 | J13 | §8 示例 4 与 R7 例子可解析 | 产生式推导 |
| B1-5 | J14 | `{` 与块界定消歧不靠回溯、不靠“看里面像不像语句” | 上下文判定 |
| B1-5 | J15 | 不引入通用对象表达式；payload 可多行 | 文法边界 |

---

## 3. 主张书（claim.md 索引）

未落盘 `claim.md`；主张以上述 `battle/B1/seats/advocate.md` 为准（§0 结论速览、§2–§6 逐条主张、§7 合并文法）。

## 4. 反证清单（counter.md 索引）

未落盘 `counter.md`；反证以 `battle/B1/seats/challenger.md` 为准（§1–§5 的 S/R/L 分级反例、§6 交叉耦合、§8 可证伪预测）。

## 5. 出证（核实命令 / 输出 / 环境）

环境：Darwin 27.2.0 arm64，2026-11-12，只读核对。

我重跑并对齐的关键命令与原始输出：

```
$ cd /Users/samxx/trae-ws/rill-dsl && git rev-parse HEAD && git status --short
033e5860406b91bbf226a5aa42a1818d520d28c0
?? battle/

$ find . -type f \( -name '*.ri' -o -name '*.dsl' \) -not -path './.git/*' | wc -l
0

$ sed -n '22p;37p;70p;85p;87p;92p;150p;152,154p;199p;428p;430p' docs/design/dsl-spec-v0.1.md
数字      -?[0-9]+(\.[0-9]+)?            整数、浮点
刻意不引入：;、()（函数调用参数用空格分隔）、=>、链式方法调用、尾随 lambda。这些是 JS 里最占 token 的样板。
emit_stmt   := "emit" STRING expr
postfix_expr:= primary ("." IDENT | "[" expr "]" | "(" arg_list? ")")*
primary     := IDENT (" " arg)*             # 工具调用：name arg1 arg2
arg         := primary
into 与 CT 的映射：DSL 的 into 直接复用 CT 的 into scope 语义和 $ 绑定，parser 和 scope resolution 共享同一套逻辑。
R4：错误传播

工具调用失败时，默认中止当前 block 并向上传播（类似 Rust ?）。if/for/into/fn 块内失败，整个块中止。MVP 不做 try/catch。
对象字面量：{ "key": value } 仅作为 emit 的 payload 语法糖，不作为通用表达式。其他场景需要构造 JSON 时，用 json_build 工具。
· 异常处理：MVP 不做 try/catch，错误直接冒泡。
· 链式调用 / 尾随 lambda：管道是唯一数据流语法。

$ sed -n '122p;164p;446p;452p' docs/design/dsl-discussion.md
现象：v0.1 的 `arg := primary`，而 `primary := IDENT (" " arg)*`，`f a b c` 至少有四种分析树：`f(a,b,c)`、`f(a(b),c)`、`f(a,b(c))`、`f(a(b(c)))`。
仍待定：是否彻底删除 postfix `()`（我方倾向：删除；MVP 没有一等函数/方法调用，保留它只会制造 `f()()` 这类歧义）。
| `read -1` | 非法实参；写 `read (-1)` | 实参是 postfix 原子 |
| `x |> f b |? g c` | `(x |> f b) |? (g c)`，`|?` 更低` | 失败单元是 `f b` |

$ cd /Users/samxx/trae-ws/ct-lang && git rev-parse HEAD && sed -n '19,24p;70p' selfhost/ct-ast/frontend/lex/Lexer.h.ct
6c21f26d505fff782d4f51e4d20a95f6710794f8
#define T_EOF    0
#define T_ID     1
#define T_NUM    2
#define T_STR    3
#define T_PUNCT  4
#define T_PP     5
            if (c == '\n') { self->bol = 1; self->line++; self->pos++; self->lstart = self->pos; continue; }

$ grep -n '^# allow:' docs/design/dsl-spec-v0.1.md; grep -n '^示例 ' docs/design/dsl-spec-v0.1.md
219:# allow: read, grep, write
356:# allow: read, grep, write
368:# allow: read, json_parse, get, write
380:# allow: read, grep, write
399:# allow: read, grep
411:# allow: read, json_parse, get, write
353:示例 1：读→搜→条件写
365:示例 2：into + $
377:示例 3：fn 复用
396:示例 4：emit 事件
408:示例 5：嵌套 into
```

核实结论：

| 席位声称 | 核实结果 |
| --- | --- |
| 主张席 §1.1 的 v0.1 行号（L22/L37/L70/L85/L87/L92/L199/L391-L393/L404/L417） | 逐行一致，**成立** |
| 主张席、成本席的仓库无实现、无 `.ri`/`.dsl` 脚本 | `find` 计数 0，**成立** |
| CT 词法只有 6 类 token、`\n` 直接 `continue` | 原文一致，**成立** |
| 三席均以 `ct-lang` HEAD `da83ade…` 为锚 | **已漂移**：当前 `6c21f26…`；上表锚点内容在当前 HEAD 仍一致，但 sha 声明失效 |
| 反证席 §1.2 “工具签名取规范自带例子：`grep` 声明 2 参 `(pattern, path)`（L355-362）” | **核实失败**：规范全文无任何工具形参声明；L356 只是 `# allow: read, grep, write`，L358 起是示例 1 代码；L97 仅出现用法 `grep "foo" "file"` |
| 反证席 §4.2 “§3.3 自己还写着『LLM 需要区分工具（空格）和函数（括号）』（L100）” | **成立**（L95-L100 原文） |

E1 继承（不替席位美化）：

| 席位 | E1 状态 |
| --- | --- |
| 主张席 | 有命令与逐字输出（§1.1/§1.4），但全部是静态文档与源码事实，无运行输出；自认“解析结果”是文法论证与 E3 预测 |
| 反证席 | **无 E1**；§1–§5 全部为构造反例，§8 自认 P1–P5 是“构造而非实测” |
| 成本席 | **无 E1、无 E3**，只有 E2/E4；行数自标 `[判断]`（±50%）、`[未核实]` |

因此本判决只对“文法层面的唯一性/可表达性”作 upheld；任何“运行后必然如何”的断言一律记为 unverified。

---

## 6. 判决（逐条）

| 争点 | verdict | 采纳方案 | 决策记录 |
| --- | --- | --- | --- |
| B1-1 | **upheld** | `arg := postfix_atom`；空格应用不递归；嵌套加括号；`into` 在实参位按上下文关键字终止调用 | D-002 |
| B1-2 | **upheld** | `NUMBER := [0-9]+("."[0-9]+)?`，`-` 只作一元/二元运算符 | D-003 |
| B1-3 | **upheld** | NEWLINE 作语句终止符，N1–N7 抑制规则，另加“注释不得吞 LF” | D-004 |
| B1-4 | **upheld** | 删除 postfix `()`；`(` 只保留分组与 `fn` 参数表；零参用裸名，工具名禁止被局部绑定遮蔽 | D-005 |
| B1-5 | **upheld** | 仅 emit payload 位置允许受限 JSON 字面量；JSON 内 NEWLINE 忽略；拒绝“payload 必须单行” | D-006 |

---

## 7. 生效范围

- 约束下一版规范 §2 词法、§3.2 语句、§3.3 表达式与 §7 骨架；不修改 `docs/design/dsl-spec-v0.1.md` 正文本身。
- 与 D-001 同向：所有调用统一空格，“调用 + 分组实参”是唯一括号含义。
- 不包括：保留字全集（P0-7）、`# dsl-version:`（P0-8）、错误格式（P0-10）、postfix 之外的“零参调用与变量同名”的完整名字解析（仅裁决“禁止遮蔽工具名”这一条）。
- 范围外不得引用本判决宣称“文法已定稿”。

## 8. 理由（逐条对应判据）

**B1-1**：J1 由构造满足——`arg` 只吃一个 `postfix_atom`，遇到下一个 `arg_start` 即开始新实参，1 token 前瞻，不需要注册表 arity。J2 主流形态零变化。J3 由 `suffix` 收进实参原子后唯一。J4 嵌套与表达式实参各只有括号一种写法。反方最强论点是“罕见嵌套不值得多一对括号”；该论点不成立的关键不在 token，而在 `grep "TODO" read path` 这类**两个 IDENT 起头**的实参在递归文法下有两棵都过 schema 浅校验的树，属规范未定义而非实现自由度（讨论稿 L122 已记录四种树）。成本席的“A 的 0 行是账面数字”与此同向。

**B1-2**：J5 由词法最大吞噬直接推出；带符号字面量把 `f 1-2` 静默读成两个实参，属静默语义漂移，违反 §1 原则 4。J6 的代价是 `read (-1)`，可由错误文案纠正。反方最强论点是“负参数更常见、去负号会抬高错误率”；该论点不成立：两种词法下 `read -1` 都“能解析”，带符号只是把二元减法的读法挤掉，把高频的 `x-1`/`f a -1` 变成静默调用，面更宽且更静默。三席无分歧。

**B1-3**：J7 是 D-001 的直接后果——空格调用下换行是区分“第二实参/下一语句”的唯一手段。J8/J9 由 N1–N7 覆盖；成本席指出的“换行升格为 token 但 LLM 不多写字符”成立。反方最强论点是“这是把 Python 缩进坑搬进来”；不成立，缩进靠空格数参与语义，NEWLINE 是单值 token，无深度与列对齐。采纳反证席补充的“注释只吃字符不吃 LF”，因为该缺陷会把 `let x = 1 # c` 的终止符吞掉，属真实边界。

**B1-4**：J10 由删除 postfix 分支直接满足；J11 与 S-001 §2 一致（`f(a)` = 调用 + 一个分组实参）；J12 需要一条硬规则。主张席的“本地变量优先、其次工具”与反证席同向，但两者都承认这**反转**了 v0.1 R6「冲突时工具优先」。我改判为更强且不反转 R6 的规则：局部绑定、参数、`fn` 名**不得**与已注册工具同名（加载错误），裸名 `f` 仅在“已注册工具/零参 fn”时作零参调用，否则是变量引用。这样零参有唯一写法，工具名保留不被脚本遮蔽，且不需要空的 `()`。反方最强论点是“删了 `()` 会把一个矛盾换成另一个”；承认，但换成的是**一处、加载期可判**的规则，而保留 postfix 是每个调用点都可能静默接受被禁形态并污染 M1 的 `()` 误用度量（讨论稿 L475）。

**B1-5**：J13 由新增产生式满足；J14 靠位置判定——`expr` 的任何分支都不以 `{` 起始，`emit STRING` 后没有块选项，判定退化为一个上下文标志。J15 由“`{` 只在 payload 位置合法”保证。两处冲裁判定：其一，payload 值位采纳主张席的 `json_value := json_object | json_array | expr`，因为 `,` `}` `]` 都不是 `expr` 的延续 token，终止性有保证，而反证席的“只许 postfix_expr”会迫使 `"count": n + 1` 先 `let`；其二，payload 多行采纳主张席的“JSON 内 NEWLINE 忽略”，**拒绝**反证席的“必须单行”——该限制不带来消歧收益（`emit` 后的 `{` 只有对象一种解释），只增加无谓报错。反方最强论点是“错误恢复可能把 payload 丢成 null”；这是对特定恢复策略的推测，规范用“productions 级限制 + 位置判定”即可堵住，不需要牺牲多行可写性。

## 9. 失效条件（含重开条件）

| 争点 | 触发条件 | 处置 |
| --- | --- | --- |
| B1-1 | M1 用真实 LLM ≥20 条脚本统计，`f (g x)` 形态占比高，且强制括号导致首次解析失败率显著高于基线 | 重开 B1-1，评估“嵌套免括号”的替代；不得直接改判据宽度 |
| B1-2 | 实测负数实参占全部数字实参 >5% 且 `(-1)` 引发可归因错误 ≥3 次/同提示 | 重开 B1-2 |
| B1-3 | 实测跨行写法集中在行尾 `and`/`or`/`+` 续行，N1–N7 误报率高 | 追加 N8 等增量抑制，不推翻终止符 |
| B1-4 | 实测零参工具调用频繁且“禁止遮蔽工具名”造成可归因失败 ≥3 次 | 重开零参规则（P-018），D-005 主结论不变 |
| B1-5 | 实测事件 payload 出现管道/嵌套过深导致可读性差 | 收窄 `json_value` 到 `unary_expr`，属实现级回退 |

以上触发条件均需真实语料与命令输出；未取得前不得以“印象”重开。

## 10. 影响面

| 对象 | 影响 |
| --- | --- |
| 决策记录 | 新增 D-002..D-006 |
| PENDING | P-001 部分定稿（P0-1/P0-2/P0-3/P0-4/P0-5/P0-6/P0-9）；P-002 定稿；P-018 部分定稿；P0-7/P0-8/P0-10 仍 pending |
| S-001 | 零参调用与同名冲突补一条边界；不改 D-001 口径；implementation 状态仍 unverified |
| M1 | 需覆盖 golden：多 IDENT 实参、嵌套、后缀实参、表达式实参、负数报错、NEWLINE 边界、`f()()` 报错、emit payload |
| 门禁 | 当前无门禁可跑；本判决只给文法判据，不给“已通过” |
| 版本号 | 无产品版本号，不 bump |
| ct-lang | 仅作实现语言；锚点 sha 需重钉到 `6c21f26…`，不复用其 lexer 的换行处理 |
