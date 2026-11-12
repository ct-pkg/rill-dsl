# Issue 台账

> 状态：目录与索引已建立，当前 **0 条 issue**（阶段 0 未立案）。
> 状态词与分权见 `AGENTS.md` §5.4；台账闭合门禁 G6 在 Phase 1 后启用。

## 1. ID 前缀

**前缀：`RILL`。** 文件名 `issues/RILL-<n>.md`，`<n>` 三位补零，例如 `RILL-001`。

- 本仓库只有一个项目，不使用外部项目前缀。
- `D-*` 是决策、`S-*` 是 DSL 行为条目、`T-*` 是工具契约、`P-*` 是待定条目，均不是 issue，不与本台账混号。
- 安全类沿用 `SEC-<n>`（§3.8），文档腐化类沿用 `DOC-<n>`（§0.6），同样放在本目录。

## 2. 条目模板

新建条目时复制以下字段，不得留空：

    ---
    id: RILL-001
    status: open
    owner: REV
    opened: YYYY-MM-DD
    anchor: <HEAD sha>
    ---

    ## 现象
    <可观察事实>

    ## 复现
    <完整命令 / file:line>

    ## 影响
    <受影响的主张、规格、门禁或版本>

    ## 期望
    <修好后的可核对状态>

    ## 处置（DEV 追加，不改 status）
    提交 sha + 验证命令原始输出

    ## 复核（REV 写 verified / reopened）
    独立复现 + 逐条对照

## 3. 状态词

只允许 `AGENTS.md` §5.4 的 8 个：`open` / `fixed` / `verified` / `reopened` / `rejected` / `deferred` / `wontfix` / `superseded`。

- `fixed` 只写在正文处置段，**不得**写进 `status`；DEV 处置后 `status` 仍为 `open`，直到 REV 复核通过改为 `verified`。
- `open` 必须有复现命令或 `file:line`；`verified` 必须有独立复现证据。

当前目录无条目，因此本文件是唯一索引；首条 issue 立案时在此表登记：

| id | 标题 | status | owner | 文件 |
| --- | --- | --- | --- | --- |
