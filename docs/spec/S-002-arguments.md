# S-002 实参文法与嵌套

- **状态**：`unverified`
- **决策**：[D-002](../decisions/D-002.md)
- **规范**：[02 §3](dsl/02-grammar.md)、[02 §6](dsl/02-grammar.md)
- **里程碑**：M2

## 1. 输入

```
copy src dst
f g "x"
f (g "x")
read path.field
f (a + b)
f(a)(b)
```

## 2. 输出

- `arg := postfix_atom`，空格应用不递归：`f g "x"` 的 AST 是 `f(g, "x")`，不是 `f(g("x"))`。
- `f (g "x")` 的 AST 是 `f(g("x"))`；括号是进入嵌套的唯一方式。
- `read path.field` 的实参是 `path.field`；`f (a + b)` 的实参是分组表达式。
- `f(a)(b)` 是两个分组实参 `f(a, b)`。
- 表达式实参必须分组：`f a + b` 是 `(f a) + b`。

## 3. 失败语义

- `f g x` 不得被解析成 `f(g(x))`；若实现给出该 AST，判失败。
- 实参未加括号的复杂表达式不得“猜测”为实参；按运算符优先级解析，不报错。
- 语法错误统一 `syntax`，位置指向第一个多余 token。

## 4. 验收命令与阈值

- **命令**：`尚未落盘`（M2 后 `tools/check.sh m2-parse`；golden 在 `examples/m2-parse/`）。
- **阈值**：上述 6 条输入逐条 AST 相等；另加 `grep "TODO" read path` 用例证明不产生嵌套调用；0 个 golden 失败。

## 5. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 文法规则 | [02 §3](dsl/02-grammar.md) | 规范正文 |
| 歧义推导 | [D-002 §理由](../decisions/D-002.md) | 决策记录 |
| 旧文反例 | `docs/design/dsl-discussion.md` L120-L136 | 基线输入 |
