# S-007 `|?` 优先级与失败单元

- **状态**：`unverified`
- **决策**：[D-007](../decisions/D-007.md)
- **规范**：[04 §2](dsl/04-pipeline-errors.md)、[02 §3](dsl/02-grammar.md)
- **里程碑**：M4

## 1. 输入

```
read "primary" |? read "fallback" |> json_parse
a |> f b |? g c
a |? b |? c
(f a |> g) |? h
read "a" |? read "b" |> f |> g
```

## 2. 输出

- `|?` 高于 `|>`：第 1 行 = `(read "primary" |? read "fallback") |> json_parse`；primary 成功时 `json_parse` 仍然执行。
- 第 2 行 = `a |> (f b |? g c)`；左侧成功时 `g` 不执行。
- 第 3 行左结合：`(a |? b) |? c`。
- 第 4 行 → 加载期 `fallback_lhs`（左侧是分组管道，不是单个 call）。
- 第 5 行 = `((read "a" |? read "b") |> f) |> g`；`|?` 不捕获 `f` 或 `g` 的失败。

## 3. 失败语义

| 输入 | `error_kind` |
| --- | --- |
| `(f a |> g) \|? h` | `fallback_lhs` |
| `a + b \|? c` | `fallback_lhs` |
| `a \|? b`（b 为字面量） | 合法，b 是右侧值 |
| `\|?` 左侧是不可捕获错误 | 按 R4 中止，`error_kind` 原样上抛 |

- `fallback_lhs` 的 Hint：`wrap the left side in a fn, e.g. 'fn step() { ... }'`。

## 4. 验收命令与阈值

- **命令**：`尚未落盘`（M4 后 `tools/check.sh m4-pipeline`）。
- **阈值**：5 条输入逐条 AST/求值轨迹一致；成功路径不得跳过后续管道阶段；不可捕获错误 0 次被吞。

## 5. 证据锚点

| 证据 | 锚点 | 性质 |
| --- | --- | --- |
| 优先级 | [04 §2](dsl/04-pipeline-errors.md) | 规范正文 |
| 求值轨迹推导 | [D-007 §理由](../decisions/D-007.md) | 决策记录 |
| 旧提案（已改判） | `docs/design/dsl-discussion.md` L222-L230 | 历史输入 |
