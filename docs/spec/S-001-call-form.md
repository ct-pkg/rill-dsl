# S-001 调用统一空格形态

- **状态**：`unverified`
- **决策**：[D-001](../decisions/D-001.md)（judge: 用户）、[D-002](../decisions/D-002.md)、[D-005](../decisions/D-005.md)
- **主张来源**：[dsl-discussion.md §2.1](../design/dsl-discussion.md#L35-L50)
- **规范**：[docs/spec/dsl/02-grammar.md](dsl/02-grammar.md)、[03-semantics.md](dsl/03-semantics.md)
- **基线对照**：[dsl-spec-v0.1.md §3.3](../design/dsl-spec-v0.1.md#L74-L91)（旧文法：工具空格、函数括号两套并列）

## 1. 输入

以下写法属于本条目：

```
read "src/main.c"
grep "malloc" "src/main.c"
analyze_file "src/a.c"
write "issues.txt" (a + b)
```

以下写法**不再是独立的调用形态**：

```
analyze_file("src/a.c")
```

括号只表示“把里面的表达式作为一个整体”，不是“这是函数调用”。上例与 `analyze_file "src/a.c"` 在语法上都是“一个调用 + 一个分组实参”；规范推荐并只展示空格写法。括号包裹单个原子合法（如 `f (g "x")`、`f (a + b)`），见 [02 §3](dsl/02-grammar.md)。

## 2. 输出

- 解析器输出统一的调用节点：`callee` + 按书写顺序的实参列表。
- 不产生“括号调用”节点；`f(a)` 不因括号而变成另一种调用。
- 工具与用户函数共用同一调用节点；解析后由加载期按注册表/`fn` 定义解析。工具名保留：局部绑定、参数、`fn` 名不得与已注册工具同名（`E_SHADOW_TOOL`），见 [D-005](../decisions/D-005.md)。
- `write "issues.txt" (a + b)` 的第二个实参是分组表达式 `a + b`。

## 3. 失败语义

**尚未实现。** 当前没有 lexer/parser，任何“解析成功/失败”的声明都不可执行。

M1 的目标失败语义（尚未落盘，不是现状）：

- 语法错误报 `path:line:col: error: ...`，格式见 [D-015](../decisions/D-015.md) 与 [07 §4](dsl/07-runtime.md)。
- 未定义名字/未知工具在加载期报错；相似名建议（Did-you-mean）待 P-013。
- `f(a, b)` 是语法错误（逗号不是分组的一部分），不得接受后静默改写；需要两个实参写 `f a b` 或 `f a (b)`。

## 4. 验收命令与阈值

- **命令**：`尚未落盘`。仓库当前没有构建、没有测试入口、没有 `tools/check.sh`。
- **计划中的命令**（M1 落地后）：
  - golden 解析用例覆盖 `docs/design/dsl-spec-v0.1.md` §8 的全部示例；
  - 真实 LLM 输出 ≥20 条，默认按路径 A（空格形态）解析。
- **阈值**（草案，未拍板）：
  - §8 示例全部可解析；
  - 同一模型、同一提示下调用形态写错 ≥3 次时，才切换路径 B（括号调用）作为退路，并附原始输出与统计；
  - 路径 B 不是并列默认方案。

## 5. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 用户决定记录 | `docs/design/dsl-discussion.md` L35-L50 | 讨论稿转述；用户原话未单独落盘 |
| v0.1 旧调用文法 | `docs/design/dsl-spec-v0.1.md` L74-L91 | 基线原文 |
| 四层要求 | `AGENTS.md` L50-L57 | 主规范生成块 |
| 决策记录 | `docs/decisions/D-001.md` | 本次落盘 |

## 6. 未决细节

以下**不是**本条目已生效的规则：

- 关键字与工具名/字段名冲突的完整规则（P-018 余项）；
- Did-you-mean、源码片段、插入符（P-013）；
- 错误格式的 Did-you-mean 扩展（格式主体已由 D-015 定）。
