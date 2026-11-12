# B1 反证席（challenger）：最小改动方案在真实 LLM 输出里的失效方式

> 席位：反对席（AGENTS §7.3）。只攻击 B1 五条争点下的「最小改动」方案。
> 证据纪律：按 AGENTS §7.7 E1–E5 出具；每条至少一条支持己方的 `file:line`，加一条**不利己方**的锚点（E2）。
> 本轮不改任何规范文件，不 `git add`，不跑全量门禁。

---

## 0. 结论先行

五条争点里，最小改动方案的共同特征是「保留 v0.1 原样，让实现去兜底」。这在**显式报错**类问题上勉强能用，但在下面三类问题上会坏：

| 危害级 | 定义 | 最小改动方案命中条数 |
| --- | --- | --- |
| S（静默错义） | 解析成功、schema 浅校验也过、结果错，LLM 与内核都不报错 | 4 / 5 |
| R（需重试才发现） | 报错文案与真实原因不匹配，LLM 重试 1–3 次才能撞对 | 3 / 5 |
| L（显式报错） | 直接 parse/load error，位置准确 | 1 / 5 稳定命中 |

判定「最小改动」为 **NO-GO** 的核心理由不是「不好看」，而是它把 B1 的失败模式从「加载期可判」推到了「运行期静默」——而 §1 原则 3 明写「隐式规则少且可预测」（[dsl-spec-v0.1.md:11](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L11)），原则 4 明写错误要能给 LLM 看（L12）。静默错义同时违反这两条。

---

## 1. B1.1 工具实参文法：`arg := primary` vs `arg := postfix_atom`

### 1.1 最小改动方案是什么

保持 v0.1 原样：`arg := primary`（[dsl-spec-v0.1.md:92](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L92)、[L346](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L346)），即实参位置允许**递归空格应用**。主张席的理由大概率是：`f a b c` 有确定实现策略（贪婪内吸或左结合二选一），且嵌套调用省一对括号。

### 1.2 反例（真实 LLM 会写的那种）

工具签名取规范自带例子：`grep` 声明 2 参 `(pattern, path)`，`read` 声明 1 参 `(path)`（[dsl-spec-v0.1.md:355-362](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L355-L362) 的示例风格）。LLM 写出：

```
grep "TODO" read path
```

在 `arg := primary` 下，这行至少有两条合法分析树：

- 树 A（贪婪内吸）：`grep("TODO", read(path))` —— 第二参是**文件内容**，不是路径。
- 树 B（左结合平铺）：`grep("TODO", read, path)` —— 3 参。

树 A 的参数个数 = grep 声明的 2，类型又都是 string，因此 **schema 浅校验全过**（规范自述只做「参数个数、字符串/数字区分」的浅校验，[L157-L158](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L157-L158)）。结果是：grep 拿到的是整篇文件内容当路径，返回空或报一个「path 不存在」，**整条脚本继续跑**。LLM 看到的是「没搜到」，不是「你写错了文法」。

更麻烦：树 A 与树 B 哪个成立，**规范没写**。`primary := IDENT (" " arg)*`（[L87](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L87)）对空格应用既没给结合性，也没给优先级。于是两个都「符合 v0.1」的实现可以给出不同 AST，同一份 LLM 输出在不同内核上语义不同——这已经不是「实现自由度」，是**规范未定义**。

第二个反例，来自规范自己的 §8 示例 3：`write "issues.txt" a + b`（[L393](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L393)）。讨论稿已认定它被解析成 `(write "issues.txt" a) + b`（[dsl-discussion.md:198-204](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L198-L204)）。这条恰好说明：**实参边界本身在 v0.1 里就没有定义**，`arg := primary` 只是把边界问题延后给解析器。

### 1.3 失败方式判定

- `grep "TODO" read path`：**静默错义（S）**。不报错、schema 过、结果错。
- `f a b c` 四棵树（[dsl-discussion.md:122](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L122)）：**规范级歧义**，实现自由选择，LLM 无法从 few-shot 预测。
- `read path.field`：`arg := primary` 下会解析成 `(read path).field`（P0-6，[dsl-discussion.md:168-176](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L168-L176)），访问的是「read 结果的字段」而不是「path.field」。若 read 返回 JSON 且有同名字段，**静默取错字段**。

### 1.4 我方方案

`arg := postfix_atom`：实参是**不递归**的 postfix 原子（`IDENT | STRING | NUMBER | BOOL | NULL | "$" | "(" expr ")"`，后接 `.field` / `[i]`），空格应用**左结合且不递归**：

- `f g "x"` = `f(g, "x")`，不是 `f(g("x"))`；
- 嵌套必须显式分组：`f (g "x")`；
- `read path.field` = `read(path.field)`。

代价是嵌套调用多一对括号，但把「静默错义」换成了「元数不符，加载期报错」：上面的 `grep "TODO" read path` 在 postfix_atom 下变成 `grep("TODO", read, path)`，3 ≠ 2，**当场报参数个数错**。这正是原则 4 要的「错误信息给 LLM 看」。

### 1.5 主张席大概会怎么反驳，以及回应

**反驳 A（最强）**：「LLM 写嵌套调用本来就少，为罕见路径牺牲 token 不划算；固定一种贪婪策略就确定了，不算歧义。」

回应（E5 steelman 引用其论点原文「固定一种贪婪策略就确定了」）：**确定 ≠ 可预测**。规范是给多个实现与多个模型看的，只要规范没写结合性，不同实现就能合法地不同；而本例里两种树**都过 schema 浅校验**，用户拿不到任何纠错信号。省下的一对括号只在「嵌套」这一条路径上出现，却要在所有「工具名后面跟了个变量名」的路径上承担静默错义风险。按 E4 的口径，这是用 S 级失败换一次性 token 节省，不成立。

**反驳 B**：「`arg := postfix_expr` 会让 `f (a + b)` 与 `f a` 的边界变复杂。」

回应：这正是要写死的部分——`arg` 的原子只有 `(` expr `)` 这一种复合形态，二元运算**不能**裸进实参。规范 §8 示例 3 因此要改成 `write "issues.txt" (a + b)`（讨论稿 P0-9 已给同向结论，[dsl-discussion.md:204](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L204)）。这不是新增复杂度，是把已有示例改成与文法一致。

**不利己方锚点（E2 强制）**：`arg := postfix_atom` 会让零参调用与变量引用撞车——`f` 单独出现时是工具调用还是变量？v0.1 靠 `primary := IDENT (" " arg)*` 的「有空格才是调用」回避了它，postfix_atom 必须补一条零参规则（见 §6 代价），否则会把问题从「歧义」挪成「未定义」。

---

## 2. B1.2 数字字面量：`-?[0-9]+(\.[0-9]+)?` vs 无符号数字 + 一元 `-`

### 2.1 最小改动方案是什么

保留词法 `NUMBER := -?[0-9]+(\.[0-9]+)?`（[dsl-spec-v0.1.md:22](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L22)）。主张席的理由大概率是：负数在工具参数里很常见，`read -1` 直接能写，省一对括号。

### 2.2 反例

**反例 1（决定性）：`subtract 10 -1`。**
在「实参用空格分隔 + NUMBER 吞负号」两条同时成立时，`-1` 是**一个** NUMBER token，`add_expr` 看不到那个 `-`（[L82](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L82) 的 `("+"|"-")` 分支不触发）。于是源码被唯一地读成 `subtract(10, -1)`。

但 LLM 完全可能想写「先调 `subtract 10`，再减 1」。规范没有任何机制区分这两种意图，而且**选择了调用读法、不报错**。这是 B1 里最干净的一枚「空格作实参分隔符 × 负号词法」冲突弹。

**反例 2：`let delta = total -1`。**
`total -1` 被读成 `total(-1)`（讨论稿 P0-1 已列出，[dsl-discussion.md:88-94](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L88-L94)）。若 `total` 是变量，报 unknown tool（R 级：文案误导，LLM 要重试才发现「少打了个空格」）；若 `total` 恰好是注册工具名，**静默发起一次工具调用**。

**反例 3：`1-2`。**
词法给出 `NUMBER(1) NUMBER(-2)` 两个相邻原子，既不是减法也不是合法调用。这条至少是 L 级，但报错会写成「unexpected number」，LLM 读不出「你的负号词法把减号吃了」。

### 2.3 失败方式判定

- `subtract 10 -1`：**静默错义（S）**。语义由词法决定，且词法选了 LLM 未必想要的那一支。
- `total -1`：S（total 是工具时）或 R（total 是变量时）。
- `1-2`：L，但文案不指向真因。

### 2.4 我方方案

`NUMBER := [0-9]+(\.[0-9]+)?`，`-` 只作一元/二元运算符（讨论稿 P0-1 同向，[dsl-discussion.md:94](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L94)）。代价：负数字面量实参要写 `f (-1)`。

关键论据（也是对本条最不利事实的处理）：**吞负号并没有真的买到「`read -1` 免括号」**。只要实参是空格分隔，`read -1` 在吞负号下是 `read(-1)`、在不吞负号下是 `read - 1`——两者都「能解析」，至少一方是错的。也就是说，吞负号不是「安全地支持负数」，而是「用词法偏袒负数、把二元减法的读法挤掉」。既然真正需要负数实参时仍要 `read (-1)` 才无歧义（讨论稿自己也这么写，[dsl-discussion.md:96](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L96)），那吞负号就只剩坏处：它让**不需要括号的减法**坏了。

### 2.5 主张席大概会怎么反驳，以及回应

**反驳 A**：「LLM 写数学表达式少，写负参数多；而且 `a - 1` 带空格仍然能算减法。」

回应：`a - 1` 能算，`a -1` / `a-1` 不能，而 LLM 的空白习惯**不稳定**——同一个模型在同一份脚本里两种写法都会出现。规范要按最坏写法设防。更关键的是，`subtract 10 -1` 这种形态里「有意为之的负参数」和「漏空格的减法」**在源码上完全相同**，任何实现都无法事后区分；这正是必须用文法禁止其中一支的理由。

**反驳 B（最强）**：「去掉吞负号后 `f -1` 变成 `f - 1`，会把最常见的负参数写法搞坏，错误率反而上升。」

回应（steelman 引用「会把最常见的负参数写法搞坏」）：这确实是代价，且不可否认。但它至少是**可纠正的 R/L 级**：`f - 1` 里 `f` 若是工具名、后面没有实参，加载期会报「tool 'f' needs an argument」；若 `f` 是变量则 `f - 1` 是合法减法、结果被下一句用掉，这时确有静默风险。两害相权：吞负号把**所有** `x-1` / `f a -1` 变成静默调用；不吞只把 `f -1` 这一种变成「要么报错、要么算成减法」。前者面更宽、更静默。选不吞。

**不利己方锚点（E2）**：不吞负号后，`read -1` 按 `primary := IDENT (" " arg)*` 会读成 `(read) - 1`——如果 `read` 是注册工具且允许零参，这就是一次**合法的零参调用减 1**，静默错义仍然存在。也就是说本条我给的不是「消灭静默」，只是「把静默面从所有减法缩到 `f -1` 一处」。主张席若抓住这点，我承认它是本条方案的真实残余风险，但残余面显著小于最小改动。

---

## 3. B1.3 语句终止：是否需要 NEWLINE

### 3.1 最小改动方案是什么

不加 NEWLINE，换行只当空白。理由大概率是：「`{}` 已经界定语句，`statement*` 靠关键字和括号就能切分；换行敏感会重蹈缩进语言的坑。」

### 3.2 反例

**反例 1（S 级）：两行字符串被合并成一次调用。**

```
read "src/a.c"
"src/b.c"
```

若换行只是空白、且 `read` 声明可变参数或 2 参 `(path, encoding)`，这会被读成 `read("src/a.c", "src/b.c")`：第二行本该是独立表达式（例如要 `emit` 或 `return` 的值），被静默吃成第一个调用的第二参。**解析成功、参数个数对得上、不报错。**

**反例 2（R 级）：`let` 被吃成实参。**

```
let a = b
let c = d
```

`b` 的实参循环读到 `let`。若 `let` 在词法上是普通 IDENT（v0.1 没有保留字表，[dsl-spec-v0.1.md:20](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L20) 也没有关键字声明；讨论稿 P0-7 已指出这点，[dsl-discussion.md:180](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L180)），就会读成 `b(let, c)` 然后撞上 `= d`，报一个与真因无关的错。

**反例 3（规范空洞）：`a |> f` 换行 `b`。**
`b` 是管道的续行（喂给 `f` 的下一段）还是新语句？v0.1 的 `pipe_expr`（[L78](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L78)）没有换行规则，两种都「说得通」。

**反例 4：`if x` 换行 `{`。**
`{` 必须紧跟 `if expr` 才成块（[L64](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L64) 的 `if_stmt` 里是字面量空格）；LLM 格式化时经常把 `{` 放到下一行（Allman 风格），v0.1 未定义这是否合法。

### 3.3 失败方式判定

- 反例 1：**S**，最危险。
- 反例 2：R（报错文案指向 `=`，不指向缺 NEWLINE）。
- 反例 3/4：规范未定义（实现自由），归 S/R 取决于实现。

### 3.4 我方方案

引入 NEWLINE 作为语句终止符，规则按讨论稿 P0-2 的 5 条（[dsl-discussion.md:110-117](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L110-L117)），但必须补两条最小改动版没有的：

1. **注释不得吞掉终止符。** `#` 注释吃到行尾（[dsl-spec-v0.1.md:33](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L33)），如果 lexer 把行尾 LF 一起吃进注释，`let x = 1 # c` 后面的换行就丢了，下一行会被合并。必须规定：注释只吃字符、不吃 LF；LF 一律产出 NEWLINE。
2. **`}` / EOF 也是终止符**，且空行折叠；管道续行把 NEWLINE 变透明。

对反例 4，明确 `if expr` 与 `{` 之间**允许且仅允许 NEWLINE**；`else` 前同理。这样 Allman 风格是合法的，不用靠实现兜底。

### 3.5 主张席大概会怎么反驳，以及回应

**反驳 A（最强）**：「`{}` 已经把块切开了，语句之内再引入换行敏感，就是把 Python 的缩进坑搬进来；LLM 在长行折行时会随机断句。」

回应（steelman 引用「就是把 Python 的缩进坑搬进来」）：这不是同一类问题。Python 的坑是**缩进深度**参与语义，深度靠空格数，肉眼与 tokenizer 都难对齐；NEWLINE 是**单一二值 token**，没有深度、没有列对齐，lexer 一行一个判断。而且反例 1 已经证明：不加 NEWLINE 时，`read "a"` 换行 `"b"` 的合并是**静默**的——`{}` 只能切块，切不开同一块内的两条相邻语句。这是本条方案与最小改动的分水岭。

**反驳 B**：「多行工具调用、多行 payload 会变难写。」

回应：规则 2/3 已覆盖——`(`/`[` 内换行忽略、`|>`/`|?` 后换行忽略；只有裸语句之间才终止。多行 payload 见 §4 的额外约束（对象字面量内部也忽略换行）。

**不利己方锚点（E2）**：NEWLINE 作终止符会与 v0.1「`;` 刻意不引入」（[dsl-spec-v0.1.md:37](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L37)）的省 token 目标产生张力：LLM 若写单行多语句 `let a = 1 let b = 2`，在 NEWLINE 终止符下**没有合法切分**，必须报错。这是 NEWLINE 方案引入的新硬约束，需要明说。

---

## 4. B1.4 postfix `()` 是否保留（§2 与 §3.3 冲突）

### 4.1 最小改动方案是什么

保留 §3.3 的 `postfix_expr := primary ("." IDENT | "[" expr "]" | "(" arg_list? ")")*`（[dsl-spec-v0.1.md:85](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L85)）与 `primary := ... | IDENT "(" arg_list? ")"`（[L88](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L88)），同时保留 §2「刻意不引入 ()」（[L37](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L37)）不改文档——即让矛盾留在文档里，实现选一边。

### 4.2 反例

**反例 1（S 级，但错在「该报错却不报」）：`find_issues("src/a.c")` 被静默接受。**

用户已拍板「工具与函数调用统一空格形态，`()` 只作分组」（[dsl-discussion.md:39-42](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L39-L42)）。但只要 postfix `()` 还在文法里，`find_issues("src/a.c")` 就会被当成合法调用**解析通过**，于是 LLM 永远不会被纠正到 `find_issues "src/a.c"`。规范 §3.3 自己还写着「这条规则写进 few-shot，LLM 需要区分工具（空格）和函数（括号）」（[L100](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L100)）——保留 postfix `()` 让这条 few-shot 的判别器失效：两种写法都合法，模型学不到区别。

**反例 2（L 级，但暴露链式）：`f()()`、`a.b()`。**
`("(" arg_list? ")")*` 带 `*` 且 `arg_list?` 可为空，直接允许 `f()()`；`a.b()` 也合法。这与 §2「不引入链式方法调用」（[L37](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L37)）和 §9「链式调用 / 尾随 lambda：管道是唯一数据流语法」（[L430](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L430)）直接冲突。运行时大概报「not callable」（L），但**加载期不拦**，等于把不该存在的语法放进 AST。

**反例 3（S 级，风格静默分叉）：`write "issues.txt" (a + b)` 与 `write("issues.txt", a + b)` 并存。**
两者都能解析、都能执行，但前者是被拍板的规范形态，后者是被禁的形态。LLM 在同一批输出里混用，统计「首次解析成功率」时两者都算成功，M1 验收的「`()` 误用次数」（[dsl-discussion.md:475](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L475)）就永远测不到真实误用——度量本身被污染。

### 4.3 失败方式判定

- 反例 1/3：**S**（该拒绝的输入被接受，纠错信号消失）。
- 反例 2：L（运行期），但加载期漏拦。

### 4.4 我方方案

**彻底删除 postfix `()`**：`(` `)` 只保留两个用途——表达式分组、`fn` 参数列表。与 §2、§9 和用户决定一致。

这会立刻暴露一个必须补的洞：**零参调用怎么写**。删除 `()` 后，`f` 单独出现无法区分「零参工具调用」与「变量引用」。我主张：零参工具调用也写成裸 `f`，消解规则按作用域——局部 `let` 绑定优先，其次工具注册表（这与 v0.1 R6 的「工具优先」[L182](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L182) 相反，必须显式改）。若不愿改 R6，则规定零参调用必须写 `f ()`——但这等于把 postfix `()` 留了一个后门，我不推荐。

### 4.5 主张席大概会怎么反驳，以及回应

**反驳 A（最强）**：「保留 `()` 能兼容 JS 习惯，LLM 更熟，首次成功率更高；用户只是说『工具用空格』，没说不能同时支持括号。」

回应（steelman 引用「LLM 更熟，首次成功率更高」）：用户决定原文是「**不再作为调用的标志**」（[dsl-discussion.md:41](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L41)），不是「可以并存」。并存意味着被禁形态静默通过，直接摧毁 M1 验收里「`()` 误用次数」这项度量（[dsl-discussion.md:475](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L475)）——你无法统计一个不报错的错误。若真担心首次成功率，正确做法是按讨论稿路径 B 做**一次性 A/B 实测后二选一**（[dsl-discussion.md:474-478](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L474-L478)），而不是两套文法长期并存。

**反驳 B**：「删了 `()` 就要处理零参调用与变量撞名，你等于把一个矛盾换成另一个。」

回应：承认。但零参歧义是**一处、可静态判定**的作用域规则（局部绑定 vs 注册表），写清即可；而保留 postfix `()` 是**每个调用点**都可能静默接受被禁形态，且与 §9 的链式禁令直接冲突。一处规则 vs 全局静默，选前者。

**不利己方锚点（E2）**：用户决定只覆盖「调用形态」，并未直接裁决删除 postfix `()`（讨论稿把它单列为「待定技术细节」，[dsl-discussion.md:166](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L166)）。所以「删除」不是用户已定结论，是本席主张；主张席有权要求走 Q2 的正式裁决（[dsl-discussion.md:487](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L487)）。

---

## 5. B1.5 emit 的 `{ "key": value }` 没有产生式

### 5.1 最小改动方案是什么

两条最小改法，都坏：
- M-a：不改文法，只改 §8 示例 4（[dsl-spec-v0.1.md:404](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L404)），把对象 payload 删掉；
- M-b：在 `emit` 位置临时允许 `{`，但不写产生式、不定义与块 `{` 的消歧。

### 5.2 反例

**反例 1（L 级，但让已发布示例不可解析）：规范自带示例 4 直接挂。**

`emit_stmt := "emit" STRING expr`（[L70](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L70)），而 `expr` 的原子集合里没有 `{`（[L87-L90](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L87-L90)）。§8 示例 4 写的是 `emit "analysis_done" { "file": "src/main.c", "count": 3 }`（[L404](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L404)），**必然 parse error**。M1 验收明确要求「若 §8 示例在新文法下解析失败，先改文档，不带着失败示例进入实现」（[dsl-discussion.md:478](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L478)），所以最小改动 M-a 过不了自家门禁。

**反例 2（S 级，错误恢复路径）：把 payload 的 `{` 当块 `{` 处理。**

如果实现「顺手」把 `emit STRING` 后面的 `{` 当块开头（因为 §3.2 的 `statement*` 里 `{` 太常见），那么：

```
emit "analysis_done" { "file": "src/main.c", "count": 3 }
```

会进入块解析，块内第一条是 `"file"` 表达式，接着撞 `:`。**带错误恢复的解析器**（规范的 M9 明确要做错误恢复与片段回填，[dsl-discussion.md:263-265](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L263-L265)）很可能跳过 `:` 后面的内容，产出一个**空 payload 的 emit**，然后继续执行。结果：事件按声明发出（`# emit:` 校验只看事件名，[dsl-spec-v0.1.md:227](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L227)），监听方拿到 null，**全程不报错**。这比直接报错更糟。

**反例 3（S 级，NEWLINE × 对象交叉）：多行 payload。**
若 §3 已采纳 NEWLINE 作终止符，而 `{` 同时是块界定（[L34](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L34)），那么：

```
emit "x" {
  "file": "a.c",
  "count": 3
}
```

的换行到底算不算语句终止？算，则 payload 内被切成多条「语句」直接坏；不算，则块内换行规则又要为 payload 开特例。**同一个 `{` token 承载两种语义，NEWLINE 规则无法在词法层一致**。

### 5.3 失败方式判定

- 反例 1：L（parse error），但违反自家 M1 门禁。
- 反例 2：**S**，错误恢复把 payload 丢成 null。
- 反例 3：规范未定义（S/R 取决于实现），且与 B1.3 规则互斥。

### 5.4 我方方案

补一条**限定在 emit 位置**的 payload 产生式（讨论稿 P0-4，[dsl-discussion.md:144-151](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L144-L151)）：

```
emit_stmt    := "emit" STRING emit_payload
emit_payload := json_value
json_value   := STRING | NUMBER | BOOL | NULL | postfix_expr
              | json_object | json_array
json_object  := "{" (STRING ":" json_value ("," json_value)*)? "}"
json_array   := "[" (json_value ("," json_value)*)? "]"
```

约束：
1. 键必须是 STRING 字面量；不允许尾随逗号；重复键 = 加载错误。
2. 只允许嵌套 json_value，不允许把任意 `expr` 塞进值位（值位允许 `postfix_expr` 是为了 `emit "x" { "k": $.v }` 这类）。
3. **`{` 的消歧靠位置，不靠看后面**：`if expr` / `into` / `fn` 后面的 `{` 是块，因为 `expr` 文法不接受裸 `{`（[L87-L90](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L87-L90)）；只有在 `emit STRING` 之后第一 token 的 `{` 是对象。
4. **对象内部 NEWLINE 忽略**，但为消除反例 3 的歧义，再收紧一条：**emit 的 payload 必须写在同一逻辑行**；跨行 payload 报加载错误并提示「put the emit payload on one line」。理由：payload 通常短，省 token；而 context-sensitive 的 NEWLINE 规则会污染整个 parser。

### 5.5 主张席大概会怎么反驳，以及回应

**反驳 A（最强）**：「对象字面量做成通用表达式更自然，LLM 想在哪构造 JSON 就在哪构造，还能省掉 json_build 工具调用。」

回应（steelman 引用「做成通用表达式更自然」）：§9 已把「通用对象字面量」列为明确不做（[dsl-spec-v0.1.md:431](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L431)），R7 也写「仅作为 emit 的 payload 语法糖，不作为通用表达式」（[L199](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L199)）。通用 `{}` 会与 `if x {`、`into {`、`fn f() {` 三处块首撞车，需要 LALR 之外的回溯或无限 lookahead，规范里根本写不清楚。emit-only 是能一句话说死的边界；其他地方用 `json_build` 工具（[L199](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-spec-v0.1.md#L199)）补足。

**反驳 B**：「emit payload 限一行太苛刻，真实事件有十几个字段。」

回应：十几个字段的事件应该用 `json_build` 工具构造成变量再 emit，而不是在语法糖里堆；或者在 json_object 内允许换行但**要求逗号位于行尾**（把续行判定交给 `,`，不交给 NEWLINE）。我给的方案优先选一行，是 MVP 成本最低、规则最短的版本；若证据席能给出真实 LLM 多行 payload 的频次数据，可以退到「逗号续行」版本——但那是第二选项，不是最小改动的现状。

**不利己方锚点（E2）**：`json_value` 允许 `postfix_expr`，意味着 `emit "x" { "k": a + b }` 里 `+` 不能进值位，LLM 会写错；这是为换取「值位与实参位规则一致」付出的代价，主张席可以拿它攻击我方方案不够省心。

---

## 6. 交叉耦合：五条不能分开裁

最小改动方案按条独立看，每条都「能跑」；合起来会互相拆台。至少有四处硬耦合：

| 耦合 | 冲突 | 后果 |
| --- | --- | --- |
| B1.3 × B1.5 | `{` 既是块又是 emit 对象，NEWLINE 规则必须随 `{` 的语义切换 | 词法无法一致；要么块内换行失效，要么 payload 内换行被切碎（§5 反例 3） |
| B1.1 × B1.2 | 实参分隔符是空格，负号词法又吃掉 `-`，两者抢同一个 `-` | `f a -1` 的语义由词法单方面决定（§2 反例 1） |
| B1.1 × B1.4 | 保留 postfix `()` 后，`f (g "x")` 到底是「分组实参」还是「对 f 结果的链式调用」 | 正是 B1.1 要消灭的歧义从后门回来 |
| B1.3 × B1.4 | 删 postfix `()` 后零参调用靠裸 `f`，与 NEWLINE 终止符一起要求「一行一个调用」 | 零参调用与变量引用的消解规则必须在同一处写死 |

结论：B1 应当作为**一组**整体裁定，而不是五条各自「最小改动」拼起来。拼起来的方案没有一条规则能同时满足上面四格。

---

## 7. 汇总表

| 争点 | 最小改动 | 最坏失败方式 | 级别 | 我方方案 | 主要代价 |
| --- | --- | --- | --- | --- | --- |
| B1.1 实参 | `arg := primary` 递归 | `grep "TODO" read path` → `grep("TODO", read(path))`，schema 过、结果错 | **S** | `arg := postfix_atom`，应用左结合不递归，嵌套加 `()` | 嵌套多一对括号；需补零参规则 |
| B1.2 数字 | `NUMBER` 吞负号 | `subtract 10 -1` 被唯一读成 `subtract(10,-1)` | **S** | 无符号数字，`-` 仅运算符，负数实参写 `(-1)` | `f -1` 不再是负参数；`f -1` 残余静默面 |
| B1.3 终止 | 无 NEWLINE | `read "a"` 换行 `"b"` 合并成 2 参调用 | **S** | NEWLINE 终止 + `{}`/EOF/折叠/续行/注释不吃 LF | 单行多语句不再合法 |
| B1.4 括号 | 保留 postfix `()` | `f(a,b)` 被静默接受，`()` 误用统计失真；`f()()` 合法 | **S**（该拒未拒） | 彻底删除，`()` 只分组与 `fn` 参数表 | 零参调用与变量撞名需写死 |
| B1.5 emit | 不改文法只改示例，或临时放行 `{` | 错误恢复把 payload 丢成 null，事件仍发出 | **S** | emit-only `json_value` 产生式 + 位置消歧 + 单行 payload | 多字段事件需 `json_build` 或退到逗号续行 |

---

## 8. 可证伪预测（E3）

对每条都给出「若我方成立，运行 X 应得到 Y」，供证据席一次性验证：

| # | 命令/构造 | 若最小改动成立应得 | 若我方成立应得 |
| --- | --- | --- | --- |
| P1 | 按 `arg := primary` 实现解析 `grep "TODO" read path`，对 grep 做参数个数校验 | 解析成功、2 参、无错 | 3 参、加载期报参数个数错 |
| P2 | 用吞负号词法解析 `subtract 10 -1` | AST 为 `subtract(10,-1)` | 无符号方案下同样输入应是 `subtract(10) - 1` |
| P3 | 无 NEWLINE 解析 `read "a"\n"b"`，read 声明 2 参 | 一次调用 2 参 | 两条语句，第二条是独立表达式 |
| P4 | 保留 postfix `()` 解析 `find_issues("src/a.c")` | 解析成功 | 解析失败，提示空格形态 |
| P5 | 把 `emit "x" { "k": 1 }` 交给「`{` 当块」的恢复式解析器 | 解析成功、payload 为 null | 加载期报「emit payload must be an object literal」 |

---

## 9. 代价量化（E4）

只算规范与最小实现，不算完整 M1：

| 争点 | 规范改动 | 实现影响 | 回退 |
| --- | --- | --- | --- |
| B1.1 | 改 1 条产生式（`arg`），加 1 条结合性说明，改 §8 示例 3 一行 | parser 实参循环从「递归 primary」改为「postfix 原子」；新增分组路径 | 还原 `arg := primary` 即可，无数据迁移 |
| B1.2 | 改词法 1 行，加 1 条负数实参写法说明 | lexer 数字分支去掉前导 `-`；unary 路径已有 | 还原词法 1 行 |
| B1.3 | 加 NEWLINE token + 5 条规则；改 §3.2/§7 骨架 | lexer 产 NEWLINE；parser 在 `(`/`[`/管道后过滤 | 删 token 与过滤，回到空白模式 |
| B1.4 | 删 §3.3 的 postfix `(` 分支与 `primary` 括号调用分支；改 §8 示例 1/3 的 `find_issues(...)` | 删两条产生式；补零参消解 | 加回两条产生式 |
| B1.5 | 加 4 条产生式；加 1 条单行约束 | parser 在 emit 位置分派对象/数组 | 删产生式，示例改回无 payload |

门禁影响：M1 的 golden 需要覆盖 P1–P5 五条；§8 五个示例要按新文法重写一遍。回退步骤均为「单条产生式还原」，无跨模块状态。

---

## 10. 我可能错在哪

1. **P1 的「LLM 真会写 `grep "TODO" read path`」是构造而非实测。** 我没有真实 LLM 样本。若证据席跑 20 条真实任务，这类串写出现 0 次，那 B1.1 只是「规范洁癖」，主张席的「罕见路径」论就成立。我的全部论证建立在「静默比报错更贵」这一价值判断上，而这条判断本身不在 AGENTS §7.1 的可判据清单里——它可能被裁判判为价值取舍、升级用户。
2. **B1.2 我承认残余风险。** 不吞负号后 `f -1` 在「`f` 是零参工具」时仍是静默减法/调用二义。我把它算成「面更小的残余」，但若真实分布里负参数远多于无空格减法，主张席的结论会反转。我给的分布判断（减法 ≫ 负参数）没有数据支撑。
3. **B1.3 的 NEWLINE 可能确实把简单问题复杂化。** 反例 1 依赖「read 是 2 参」，若所有 MVP 工具都是 1 参，合并会直接报参数个数错（L 级），NEWLINE 的必要性就下降。另外「注释不吃 LF」是我加的规则，规范未提，可能是我过度设计。
4. **B1.4 删除 postfix `()` 不是用户已定结论**，只是讨论稿的倾向（Q2，[dsl-discussion.md:487](file:///Users/samxx/trae-ws/rill-dsl/docs/design/dsl-discussion.md#L487)）。我把它写成「我方方案」有越权风险；若裁判认为应走用户拍板，本条只能算「提出待裁项」而非反证成功。
5. **B1.5 的「错误恢复丢 payload」是推测实现行为。** 规范只说要做错误恢复（M9），没说恢复策略；若实现选择「`:` 处硬失败」，反例 2 就退化成 L 级，我的 S 级主张不成立。单行 payload 约束也是我加码，讨论稿 P0-4 原案允许嵌套但没限定行数。
6. **我引的 CT 事实只用于「不要声称复用 CT」这一旁证**，B1 五条本身不依赖 CT；若裁判认为 CT 证据与 B1 判据无关，这部分应被剔出证据集（AGENTS §7.7 E2 要求锚点相关）。
7. **最强的反打可能是整体性的**：主张席可以说「你五条方案合起来是重写文法，不是最小改动；而规范尚未定稿，重写成本远大于收益」。我没有否定这个成本论点，只argue 收益（消灭静默）更大；这是可争议的权衡，不是可复现事实。

---

## 附：CT 只读事实（供「不要复用运行时」旁证，非 B1 主判据）

| 说法 | 事实 | 锚点 |
| --- | --- | --- |
| CT 无 `\|>` | 运算符表里没有 `\|>`；全仓 grep 仅命中 3 个 mermaid bundle，lexer/spec 无 | [language-spec.md:95-112](file:///Users/samxx/trae-ws/ct-lang/docs/language-spec.md#L95-L112)、`grep -r '\|>' /Users/samxx/trae-ws/ct-lang` |
| CT 词法 token 很少 | 只有 `T_EOF/T_ID/T_NUM/T_STR/T_PUNCT/T_PP` | [Lexer.h.ct:19-24](file:///Users/samxx/trae-ws/ct-lang/selfhost/ct-ast/frontend/lex/Lexer.h.ct#L19-L24) |
| `$` 不是通用当前对象 | 只在数组 range 初值里按元素展开；别处 `unexpected token` | [language-spec.md:1864-1867](file:///Users/samxx/trae-ws/ct-lang/docs/language-spec.md#L1864-L1867) |
| `into` 可借鉴但禁止嵌套 | `into` 是上下文关键字；嵌套报 `nested 'into' blocks are not supported` | [language-spec.md:2220-2247](file:///Users/samxx/trae-ws/ct-lang/docs/language-spec.md#L2220-L2247)、[Expr.h.ct:2892-2906](file:///Users/samxx/trae-ws/ct-lang/selfhost/ct-ast/frontend/parse/Expr.h.ct#L2892-L2906) |
| `foreach` 固定 `item` 且值拷贝 | 循环变量名固定、`i` 只读、`Map` 体内用 `i` 是硬错 | [language-spec.md:1985-2024](file:///Users/samxx/trae-ws/ct-lang/docs/language-spec.md#L1985-L2024)、[language-spec.md:2101-2109](file:///Users/samxx/trae-ws/ct-lang/docs/language-spec.md#L2101-L2109) |
| CT 诊断格式 | `path:line:col: error: msg` | [Diag.h.ct:75-89](file:///Users/samxx/trae-ws/ct-lang/selfhost/ct-ast/tool/diag/Diag.h.ct#L75-L89) |

用途仅限：若 B1 的消歧方案要声称「与 CT 对齐」，上面事实说明 CT 没有可对齐的运行时语义，只能对齐诊断格式与「上下文关键字 + 编译期脱糖」这一条形态。
