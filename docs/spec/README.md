# 规格层（Spec）

> 本目录放两部分：规范正文（`dsl/`）与带稳定 ID 的对外行为条目（`S-*.md`）。
> 状态词严格区分：
>
> - `accepted`：已拍板且已验收；当前 **0 条**。
> - `unverified`：已拍板、但尚无实现或无门禁证据；当前 S-001..S-024、T-001..T-006 与 `dsl/` 全部正文。
> - `pending`：未拍板，验收判据未定；见 [PENDING](PENDING.md)。不得当作已生效规则引用。

## 1. 规范正文

| 版本 | 状态 | 文件 |
| --- | --- | --- |
| `v0.1 rev.1`（2026-11-12） | unverified | [dsl/README.md](dsl/README.md) |

分卷：词法、文法、语义、管道与错误、数据与事件、安全、运行时、示例、里程碑、AST 与位置。每一处重要改动在正文内挂 `D-xxx`。

## 2. 条目索引

| ID | 行为 | 状态 | 决策 | 文件 |
| --- | --- | --- | --- | --- |
| S-001 | 调用统一空格；括号只作分组与 `fn` 参数表 | unverified | D-001 | [S-001](S-001-call-form.md) |
| S-002 | 实参文法与嵌套 | unverified | D-002 | [S-002](S-002-arguments.md) |
| S-003 | 数字与负号 | unverified | D-003 | [S-003](S-003-numbers.md) |
| S-004 | NEWLINE 终止与抑制 | unverified | D-004 | [S-004](S-004-newline.md) |
| S-005 | 括号与零参调用 | unverified | D-005 | [S-005](S-005-parens-zero-arg.md) |
| S-006 | emit payload | unverified | D-006 | [S-006](S-006-emit-payload.md) |
| S-007 | `\|?` 优先级与失败单元 | unverified | D-007 | [S-007](S-007-fallback-precedence.md) |
| S-008 | 可捕获错误集与 `degraded` | unverified | D-007 | [S-008](S-008-capturable-errors.md) |
| S-009 | 截断元数据 | unverified | D-008 | [S-009](S-009-truncation.md) |
| S-010 | 赋值与 `let mut` | unverified | D-009 | [S-010](S-010-assignment.md) |
| S-011 | `for`、`break`、`continue` | unverified | D-009 | [S-011](S-011-loops.md) |
| S-012 | R4 失败行为表 | unverified | D-010 | [S-012](S-012-r4-failure-table.md) |
| S-013 | 默认拒绝与 header 校验 | unverified | D-011 | [S-013](S-013-default-deny.md) |
| S-014 | `# allow: *` 与 deny 优先级 | unverified | D-011 | [S-014](S-014-allow-star-audit.md) |
| S-015 | 策略快照与强杀 | unverified | D-012 | [S-015](S-015-policy-snapshot.md) |
| S-016 | 审批绑定 | unverified | D-013 | [S-016](S-016-approval.md) |
| S-017 | 路径约束 | unverified | D-014 | [S-017](S-017-path-constraint.md) |
| S-018 | 命令与域名约束 | unverified | D-014 | [S-018](S-018-command-domain.md) |
| S-019 | emit 上限、双通道与重复键 | unverified | D-014 | [S-019](S-019-emit-limits.md) |
| S-020 | 错误格式与 `error_kind` | unverified | D-015 | [S-020](S-020-error-format.md) |
| S-021 | `# dsl-version:` 头 | unverified | D-018 | [S-021](S-021-dsl-version.md) |
| S-022 | `par` 保留字 | unverified | D-019 | [S-022](S-022-par-keyword.md) |
| S-023 | 嵌套 `into` | unverified | D-017 | [S-023](S-023-nested-into.md) |
| S-024 | 值层：拼接与 `length` | unverified | D-016 | [S-024](S-024-value-concat-length.md) |
| T-001 | 工具 `read` 契约 | unverified | 工具层 | [T-001](tools/T-001-tool-read.md) |
| T-002 | 工具 `grep` 契约 | unverified | 工具层 | [T-002](tools/T-002-tool-grep.md) |
| T-003 | 工具 `write` 契约 | unverified | 工具层 | [T-003](tools/T-003-tool-write.md) |
| T-004 | 工具 `json_parse` 契约 | unverified | 工具层 | [T-004](tools/T-004-tool-json-parse.md) |
| T-005 | 工具 `get` 契约 | unverified | 工具层 | [T-005](tools/T-005-tool-get.md) |
| T-006 | 工具 `json_build` 契约 | unverified | 工具层 | [T-006](tools/T-006-tool-json-build.md) |
| P-001..P-023 | 未决问题 | pending / partial / undecidable | 无 | [PENDING](PENDING.md) |

命名空间：`S-*` 是 DSL 对外行为条目，`T-*` 是工具契约条目，两者独立编号、互不复用（工具目录曾用 `S-021..S-026`，已改为 `T-001..T-006`）。`T-*` 的状态规则、条目格式与验收约定同本文 §3、§4。

## 3. 条目格式

每个 `S-*` 条目必须具备：

1. 状态与决策锚点；
2. 输入（可解析的源码形态或工具返回值）；
3. 输出（AST/运行结果的可观察约定）；
4. 失败语义（错误类别、位置、是否拒绝加载）；
5. 验收命令与阈值（没有就写 `尚未落盘`，不得写“通过”）；
6. 证据锚点（提交 sha、`file:line`）。

## 4. 验收命令约定

- 当前仓库没有构建、没有门禁、没有 `docs/acceptance.md`；所有验收命令均为 `尚未落盘`。
- M1 落地后补：`tools/check.sh g1`、`m1-tokens`、`m2-parse` 等子命令与 golden。
- 在命令存在之前，本目录任何条目都不得标 `accepted`。

## 5. 与主张层的关系

- 主张层：`docs/requirements/README.md`。
- 规格层只回答“做什么、怎么判对错”，不重复目标与理由。
- 未决项只在 `PENDING.md` 出现；`S-*` 与规范正文中不得把待定细节写成已生效规则。rev.1 正文不含 `provisional` 文本；原先三处已由 D-017/D-018/D-019 收口。
