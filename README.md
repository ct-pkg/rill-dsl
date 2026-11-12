# rill-dsl

Agent 工具编排 DSL 的规范讨论仓库。当前处于**讨论阶段，未定稿，无实现代码**。

## 状态

- 唯一已拍板项：调用统一空格形态，括号只作分组（[D-001](docs/decisions/D-001.md)，judge: 用户）。
- 其余 Q1–Q10 与文法/语义/安全问题全部未决：[docs/spec/PENDING.md](docs/spec/PENDING.md)。
- 没有 lexer、parser、测试、门禁或版本号；不要把任何 pending 条目当成已生效规则。

## 文档地图

| 层 | 位置 | 内容 |
| --- | --- | --- |
| 主张层 | [docs/requirements/](docs/requirements/README.md) | 目标、非目标、约束、术语、决策索引、候选偏离 |
| 规格层 | [docs/spec/](docs/spec/README.md) | S-001（unverified）、P-001..P-019（pending） |
| 实现记录层 | [docs/design/](docs/design/README.md) | v0.1 原文基线、讨论稿（均为非规范） |
| 决策层 | [docs/decisions/](docs/decisions/README.md) | D-001 |
| 治理 | [AGENTS.md](AGENTS.md) | 跨项目主规范 v1.7.0 生成块（原样入库） |

## 当前可执行的验证

无构建、无门禁。文档层只做人工/链接核对；验收命令统一写 `尚未落盘`，见 [规格层](docs/spec/README.md)。

## 候选偏离（未签字）

DOC-S2（单份 ≤300 行）、G0（session-map / tools/check.sh / snippets）、G4（snippet 渲染）、T-7（先红后绿）当前不适用或有冲突。理由与收敛方式见 [主张层 §6](docs/requirements/README.md)，未写入 `AGENTS.md` 的 `deviation:` 段。

## 不做什么

agent 主循环、上下文压缩、记忆/跨脚本状态、审批、调度、MVP 并行，均按讨论稿暂归内核或列为非目标；均未最终拍板。
