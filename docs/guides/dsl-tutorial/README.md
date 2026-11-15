# 旧教程已迁移（v0.1 rev.1 → RILL 0.1.0）

> 状态：**已迁移**。本教程的 12 卷基于 `v0.1 rev.1` 文法手工推导，自述 `unverified`、
> **没有运行过**，与现在能跑的 RILL 0.1.0 不是同一套语法。旧卷已删除，按下面的对照
> 表改读 [examples/tour/](../../../examples/tour/) 与 [语言规范](../../RILL-0.1.0.md)。

## 1. 为什么整体下线

旧教程里的 `let text = read "notes.txt"`、`# allow: read, write`、`if hits.length > 0`、
`|>` 追加实参等写法，在当前实现里分别对应完全不同的形态（句子式动词、`[to]` 介宾、
`//map{}`/`//fn{}`、`|>` 只传段值）。教程还按“仓库没有 parser”的前提写成推导稿，
继续留着会让人把不存在的语法当契约。

## 2. 卷目对照

| 旧卷 | 原主题 | 现在看哪里 |
| --- | --- | --- |
| 01 | 定位与边界 | [README](../../../README.md) §8、[规范](../../RILL-0.1.0.md) 第 1–2 节 |
| 02 | 最小可运行脚本 | [01-send](../../../examples/tour/01-send.md)、[02-pipe](../../../examples/tour/02-pipe.md) |
| 03 | 词法 | [01-send](../../../examples/tour/01-send.md)、[04-map](../../../examples/tour/04-map.md)、[规范](../../RILL-0.1.0.md) §4.16 |
| 04 | 管道 | [02-pipe](../../../examples/tour/02-pipe.md)、[12-error-run](../../../examples/tour/12-error-run.md) |
| 05 | 作用域 | [03-into-order](../../../examples/tour/03-into-order.md) |
| 06 | 变量与循环 | [05-if](../../../examples/tour/05-if.md)、[06-each](../../../examples/tour/06-each.md)、[07-break](../../../examples/tour/07-break.md) |
| 07 | 函数 | [09-fn](../../../examples/tour/09-fn.md) |
| 08 | 事件 | **当前实现没有事件机制**，无对应样例；不要把旧卷的写法当可用语法 |
| 09 | 安全与能力边界 | [15-profile](../../../examples/tour/15-profile.md) |
| 10 | 错误与限制 | [10-error-lex](../../../examples/tour/10-error-lex.md)、[11-error-parse](../../../examples/tour/11-error-parse.md)、[12-error-run](../../../examples/tour/12-error-run.md) |
| 11 | 常见错误 | [10-error-lex](../../../examples/tour/10-error-lex.md)、[11-error-parse](../../../examples/tour/11-error-parse.md) |
| 12 | few-shot | [样例索引](../../../examples/README.md)（17 个实测样例，按能力分组） |

## 3. 读法建议

第一次接触：`01-send` → `02-pipe` → `03-into-order` → `05-if` → `06-each` → `08-parallel`
→ `09-fn`，然后按 [索引](../../examples/README.md) 补错误路径与宿主部分。每个样例的
`.md` 都写了“演示什么 + 需要哪条语法”，命令可直接复制运行。

## 4. 历史材料

旧的 `v0.1 rev.1` 规范与工具契约留在 [docs/spec/](../../spec/) 作历史档案，按 DOC-S2
冻结，不作为当前语法依据。
