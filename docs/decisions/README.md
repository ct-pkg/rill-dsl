# 决策记录索引

> 只登记已拍板的决定。未决问题不在这里造记录，统一见 [docs/spec/PENDING.md](../spec/PENDING.md)。

| id | date | status | judge | 一句话 | 文件 |
| --- | --- | --- | --- | --- | --- |
| D-001 | 2026-11-12 | accepted | USER | 调用统一空格形态；括号只作分组与 fn 参数表 | [D-001](D-001.md) |
| D-002 | 2026-11-12 | accepted | EDITOR | 实参文法 `arg := postfix_atom`，空格应用不递归 | [D-002](D-002.md) |
| D-003 | 2026-11-12 | accepted | EDITOR | 数字无符号，负号只作运算符 | [D-003](D-003.md) |
| D-004 | 2026-11-12 | accepted | EDITOR | NEWLINE 作语句终止符，N1–N7 抑制 | [D-004](D-004.md) |
| D-005 | 2026-11-12 | accepted | EDITOR | 删除 postfix `()`；零参写裸名；禁止遮蔽工具名 | [D-005](D-005.md) |
| D-006 | 2026-11-12 | accepted | EDITOR | emit payload 用受限 JSON 字面量，JSON 内换行忽略 | [D-006](D-006.md) |
| D-007 | 2026-11-12 | accepted | EDITOR | `\|?` 高于 `\|>`，左侧单 call，可捕获集显式 | [D-007](D-007.md) |
| D-008 | 2026-11-12 | accepted | EDITOR | 截断元数据用侧车伪字段（C 方案），粘性传播 | [D-008](D-008.md) |
| D-009 | 2026-11-12 | accepted | EDITOR | 赋值限 `let mut`；`for` + break/continue；无 `while` | [D-009](D-009.md) |
| D-010 | 2026-11-12 | accepted | EDITOR | R4 重述为“调用级降级、无块级恢复”；emit 子句由 D-014 取代 | [D-010](D-010.md)、[D-014](D-014.md) |
| D-011 | 2026-11-12 | accepted | EDITOR | `# allow:` 缺省默认拒绝，`*` 显式且审计 | [D-011](D-011.md) |
| D-012 | 2026-11-12 | accepted | EDITOR | 策略热更新用不可变快照 + 调用边界强杀 | [D-012](D-012.md) |
| D-013 | 2026-11-12 | accepted | EDITOR | 审批在内核，DSL 零审批语法；边界一节 | [D-013](D-013.md) |
| D-014 | 2026-11-12 | accepted | EDITOR | 参数约束按“必做/不做/deferred”分档硬化 | [D-014](D-014.md) |
| D-015 | 2026-11-12 | accepted | EDITOR | 错误格式统一为 `path:line:col: error:` + 详情 + Hint（技术裁定） | [D-015](D-015.md) |
| D-016 | 2026-11-12 | accepted | EDITOR | 值层：`string + 标量` 拼接、`json_array.length` | [D-016](D-016.md) |
| D-017 | 2026-11-12 | accepted | EDITOR | 嵌套 `into` 允许，内层 `$` 覆盖、退出恢复 | [D-017](D-017.md) |
| D-018 | 2026-11-12 | accepted | EDITOR | `# dsl-version:` 接受 `1`，其他值 `E_VERSION` | [D-018](D-018.md) |
| D-019 | 2026-11-12 | accepted | EDITOR | `par` 保留为关键字，出现即 `not_implemented` | [D-019](D-019.md) |
| D-020 | 2026-11-12 | accepted | EDITOR | AST 节点、稳定 `sexpr`、UTF-8 字节列与错误阶段；新增 10 卷 | [D-020](D-020.md) |
| D-021 | 2026-11-15 | accepted | USER | 演进目标为 rillShell（完整 CLI）；当前只做脚本执行器 + 最小 CLI，REPL 暂缓不砍 | [D-021](D-021.md) |
| D-022 | 2026-11-15 | accepted | USER | 函数定义去掉名字，按“动词+状语+介词”的形状识别；同形冲突加载期报错 | [D-022](D-022.md) |
| D-023 | 2026-11-16 | accepted | USER | 主语接受任意对象，解释权在动词的关系/约束层；语言层不做先验二选一 | [D-023](D-023.md) |
| D-024 | 2026-11-16 | accepted | USER | P-025 取 B：签名不识别类型前缀，常量位比字面原文；`shape_version=2` 仅定义侧并带消费者 | [D-024](D-024.md) |

## 状态说明

- `accepted`：用户或 battle 已裁定，文本已落盘；若涉及对外行为但尚未实现，规格条目仍标 `unverified`。
- `rejected`：明确否决，保留理由。
- `superseded`：被新决策取代，必须链接新旧记录。

## 未决项

D-002..D-014 覆盖 B1/B2/B3 的 13 条争点；D-015..D-020 是定稿所需的技术裁定（judge 为 EDITOR，不挂用户名义）；D-021..D-024 是用户直接指示的方向性记录。仍无决策的条目见 [PENDING](../spec/PENDING.md)（P-013/P-014、P-020/P-021 两个 undecidable 项，以及 P-024/P-026..P-029 待定）。
