# 旧样例已迁移（v0.1 rev.1 → RILL 0.1.0）

> 状态：**已迁移**。本目录不再提供样例；可运行的样例在
> [examples/tour/](../../examples/tour/)，索引见 [examples/README.md](../../examples/README.md)。

## 1. 为什么迁移

这里原有 7 篇样例（`01-sequential` … `07-end-to-end`），写于实现之前，按
`v0.1 rev.1` 的 EBNF 手工推导，文件头自述 `unverified`、**没有运行过**。它们使用的
`# allow:` / `let` / `|>` / `.length` / 空格实参等写法，与现在的 RILL 0.1.0
（`<read> … [to] …`、`|>` 段间传值、`//map{}`、`//fn{}`）不是同一套语法。

保留两套语法并存只会让人抄错，因此旧文件已删除，改写后的真实样例统一放在
`examples/tour/`：每个 `.rill` 都配同名 `.md`，写明能力与语法要点，并贴实测输出。

## 2. 场景对照

| 旧样例 | 原来的场景 | 现在看哪里 |
| --- | --- | --- |
| `01-sequential` | 读取 → 搜索 → 合并写盘 | [02-pipe](../../examples/tour/02-pipe.md)、[03-into-order](../../examples/tour/03-into-order.md)、[15-profile](../../examples/tour/15-profile.md) |
| `02-conditional` | 条件分支 | [05-if](../../examples/tour/05-if.md) |
| `03-loop` | 循环与结果收集 | [06-each](../../examples/tour/06-each.md)、[07-break](../../examples/tour/07-break.md) |
| `04-error-handling` | 错误处理 | [12-error-run](../../examples/tour/12-error-run.md)、[13-error-handled](../../examples/tour/13-error-handled.md) |
| `05-batch-serial` | 批量串行 | [08-parallel](../../examples/tour/08-parallel.md) |
| `06-allowlist-boundary` | 白名单/能力边界 | [15-profile](../../examples/tour/15-profile.md) |
| `07-end-to-end` | 端到端编排 | [09-fn](../../examples/tour/09-fn.md)、[15-profile](../../examples/tour/15-profile.md) |

## 3. 想读规范

现行规范正文是 [docs/RILL-0.1.0.md](../RILL-0.1.0.md)（0.1.1，只读）。
旧的 `v0.1 rev.1` 材料留在 [docs/spec/](../spec/) 作历史档案，不作为当前语法依据。
