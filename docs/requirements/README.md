# 主张层：Rill DSL（讨论阶段）

> 状态：**规范正文已有 `v0.1 rev.1` 草案（unverified，无实现）**。本文件只做主张层索引，不替代规范正文。
> 已拍板项为 [D-001](../decisions/D-001.md) 与 [D-002..D-020](../decisions/README.md)；其中 D-015..D-020 多为裁判席技术裁定，不挂用户名义。
> 仍未决的问题登记在 [docs/spec/PENDING.md](../spec/PENDING.md)；规范正文已无 `provisional` 文本。

## 1. 目标（一句话）

用最少的 token 让 LLM 表达「单次执行」的工具调用与数据流，并用可机械校验的语法边界把歧义挡在加载期。

来源：`docs/design/dsl-spec-v0.1.md` 开篇（基线原文，尚未重新拍板）。

## 2. 主张条目

| ID | 类型 | 内容 | 状态 | 依据 |
| --- | --- | --- | --- | --- |
| R-001 | 目标 | 以最少 token 表达工具调用与流程编排，语法边界由内核严格控制，安全由三层白名单兜底 | baseline | v0.1 开篇、§1 |
| R-002 | 非目标 | agent 主循环、上下文压缩、记忆/跨脚本状态、审批、调度归内核，不进单次执行语法 | decided | [06 §6](../spec/dsl/06-security.md)、[D-013](../decisions/D-013.md)、[P1-4](../design/dsl-discussion.md#L269-L276)、[P1-9](../design/dsl-discussion.md#L317-L324) |
| R-003 | 非目标 | MVP 不做并行；`par` 只讨论预留，不产生可执行能力 | pending | [讨论稿 P1-5](../design/dsl-discussion.md#L277-L284)、[P1-10](../design/dsl-discussion.md#L325-L332) |
| R-004 | 非目标 | 不做类型系统、模块/import、try/catch、递归、通用对象字面量、正则字面量 | baseline | v0.1 §9（尚未重新拍板） |
| R-005 | 约束 | 实现语言为 CT；但 CT 只作实现语言，运行期语义（动态值、管道、工具注册、事件）需自建 | pending | [讨论稿 §5](../design/dsl-discussion.md#L349-L366) |
| R-006 | 约束 | 单文件脚本；值是动态的（null/bool/number/string/json_object/json_array） | baseline | v0.1 §4 R5、§9 |
| R-007 | 约束 | 三条隐式规则：隐式 await、隐式管道传参、`$` 指代 into 当前对象 | baseline | v0.1 §1 原则 3 |
| R-008 | 约束 | 文档四层与单份 ≤300 行（DOC-S2）；本仓库当前存在候选偏离，见 §6 | active | `AGENTS.md` 50-57、980 |
| R-009 | 约束 | 未拍板项不得写成 accepted 决策；只能登记为 pending | active | 用户 2026-11-12 指示 |

状态词按对象分维度，不跨类混用：

- **R-\* 需求条目**用 `baseline` / `pending` / `decided` / `active`：
  - `baseline`：v0.1 原文里的主张，当前只作讨论基线，**不等于用户已重新拍板**。
  - `pending`：结论未定，登记在 PENDING。
  - `decided`：已由决策记录或规范正文定死，但尚未实现。
  - `active`：当前仓库治理规则，已生效。
- **S-\* / T-\* 规格条目**只用 `unverified` / `verified`（`accepted` 是决策记录的状态词，不用于规格条目）：见 §3 术语表。

## 3. 术语

| 术语 | 含义 |
| --- | --- |
| 单次执行 | 一次加载（parse + 静态检查）与 `dsl_exec` 的生命周期；本规范的范围上限 |
| 工具调用 | 内核注册表里的工具被脚本调用；参数空格分隔，见 S-001 |
| 管道 | `a \|> f b`，把左侧值追加到右侧调用参数末尾；见 D-007 | 已定稿（unverified） |
| 降级 | `left \|? right`，左侧单 call 失败则尝试右侧；高于 `\|>`，见 D-007 | 已定稿（unverified） |
| 结果元数据 | `{ value_json, truncated, original_size }`，侧车伪字段，见 D-008 | 已定稿（unverified） |
| into / `$` | 词法作用域绑定；`$` 指代当前绑定值；嵌套允许、内层覆盖退出恢复（D-017）；块外使用报 `dollar_outside` |
| 策略快照 | 加载时绑定的 allow/deny/registry/constraint 版本，执行期不随热更新改变；见 D-012 |
| trace_id | 一次执行生成的关联 id，随 emit 事件传播，供因果链查询（P-014 未定；非规范术语，仅是讨论名） |
| accepted | 决策记录的状态词：已拍板（不用于 S/T 规格条目） |
| unverified | S/T 规格条目已写、尚无实现门禁；当前 S-001..S-024 与规范正文 |
| verified | S/T 规格条目已通过验收命令；当前 **0 条** |
| pending | R-\* 需求条目：结论未定；当前 PENDING 除已定稿项外的条目 |
| 候选偏离 | 与主规范有张力但未取得用户签字，**不计为已登记 deviation** |

## 4. 决策记录索引

| id | 状态 | 一句话 | 文件 |
| --- | --- | --- | --- |
| D-001 | accepted | 调用统一空格；括号只作分组与 fn 参数表；judge 为用户 | [D-001](../decisions/D-001.md) |
| D-002..D-014 | accepted | B1/B2/B3 battle 判决（文法、语义、安全） | [决策索引](../decisions/README.md) |
| D-014 | accepted | 参数约束分档（必做/不做/deferred） | [D-014](../decisions/D-014.md) |
| D-015 | accepted | 错误格式统一；judge 为裁判席（用户未参与） | [D-015](../decisions/D-015.md) |
| D-016 | accepted | 值层：`string + 标量` 拼接、`json_array.length` | [D-016](../decisions/D-016.md) |
| D-017 | accepted | 嵌套 `into` 允许，内层 `$` 覆盖、退出恢复 | [D-017](../decisions/D-017.md) |
| D-018 | accepted | `# dsl-version:` 接受 `1`，其他值报错 | [D-018](../decisions/D-018.md) |
| D-019 | accepted | `par` 保留为关键字，出现即 `not_implemented` | [D-019](../decisions/D-019.md) |
| D-020 | accepted | AST 节点、稳定 `sexpr`、UTF-8 字节列与错误阶段 | [D-020](../decisions/D-020.md) |

未决问题仍登记在待定条目里，避免伪装成 accepted：P-013/P-014、P-020/P-021（undecidable）。P-007/P-009/P-010/P-017/P-018/P-019 已收口。

- Q1–Q10 与 P0/P1 清单：[docs/spec/PENDING.md](../spec/PENDING.md)
- 各方意见与倾向：[dsl-discussion.md](../design/dsl-discussion.md)

## 5. 规格索引

| 条目 | 行为 | 状态 | 文件 |
| --- | --- | --- | --- |
| 正文 | Rill DSL 规范 `v0.1 rev.1`（词法/文法/语义/安全/运行时/示例/里程碑） | unverified | [dsl/README.md](../spec/dsl/README.md) |
| S-001 | 调用形态：空格参数，括号仅分组 | unverified | [S-001](../spec/S-001-call-form.md) |
| S-002..S-024 | 文法、语义、安全、错误、值层的可验收条目 | unverified | [规格索引](../spec/README.md) |
| P-001..P-023 | 未决问题清单 | pending / partial | [PENDING](../spec/PENDING.md) |

## 6. 候选偏离（未签字，不计为已登记 deviation）

| # | 条款 | 现状 | 为什么不硬套 | 收敛 |
| --- | --- | --- | --- | --- |
| C-1 | DOC-S2 单份文档 ≤300 行 | `docs/design/dsl-spec-v0.1.md` 516 行、`docs/design/dsl-discussion.md` 521 行 | v0.1 是用户提供的基线原文，拆分等于改写原文；讨论稿是单一问题清单，拆开会出现重复与断链 | 定稿时把 v0.1 归档为历史输入，讨论稿按主题拆到 `docs/spec/` 与 `docs/decisions/` |
| C-2 | G0 实例化项（`docs/session-map.md`、`tools/check.sh`、`docs/snippets/`、Issue 前缀） | 均未建；`AGENTS.md` 的实例化表已如实写“未建” | 仓库尚无实现、无门禁、无多会话 phase；现在造门禁会把未拍板的语法固化成规则 | M1 开工前补 session-map 与最小 `tools/check.sh`，门禁只检查文档链接与规范 pin |
| C-3 | G4 snippet 渲染 | 无 `docs/snippets/`，文档中的代码块是待定语法示例 | 未定稿语法不能进可执行 snippet，否则等于提前验收 | 定稿并实现 M1 后，把 §8 示例迁入 snippet 与 golden |
| C-4 | 6.6 T-7 先红后绿 | 当前是纯文档仓库，无实现任务 | 无行为改动，无需红证；硬套会产生空提交 | M1 首个实现任务起执行 T-7 |

以上四条都**没有**用户签字，因此不写入 `AGENTS.md` 的 `deviation:` 段；它们是待用户裁决的候选偏离。

## 7. 当前状态与入口

- 规范原文基线：`docs/design/dsl-spec-v0.1.md`（历史输入，不改写）
- 规范正文：`docs/spec/dsl/`（`v0.1 rev.1`，unverified）
- 讨论稿：`docs/design/dsl-discussion.md`（非规范）
- 规格层：`docs/spec/`
- 决策层：`docs/decisions/`
- 仓库治理：`AGENTS.md`（v1.7.0 生成块原样入库）

下一步：M0 只做门禁与文档基线；原先三处 `provisional` 已由 D-017/D-018/D-019 收口，正文无临时文本。M1 落地后把 S-001..S-024 的验收命令从 `尚未落盘` 换成真实门禁。
