# 主张层：Rill DSL（讨论阶段）

> 状态：**讨论阶段，未定稿**。本文件只做主张层索引，不替代规范正文。
> 当前唯一已拍板项是 [D-001](../decisions/D-001.md)：「调用统一用空格，括号只作分组」。
> 其余问题全部未决，统一登记在 [docs/spec/PENDING.md](../spec/PENDING.md)，**没有**对应决策记录。

## 1. 目标（一句话）

用最少的 token 让 LLM 表达「单次执行」的工具调用与数据流，并用可机械校验的语法边界把歧义挡在加载期。

来源：`docs/design/dsl-spec-v0.1.md` 开篇（基线原文，尚未重新拍板）。

## 2. 主张条目

| ID | 类型 | 内容 | 状态 | 依据 |
| --- | --- | --- | --- | --- |
| R-001 | 目标 | 以最少 token 表达工具调用与流程编排，语法边界由内核严格控制，安全由三层白名单兜底 | baseline | v0.1 开篇、§1 |
| R-002 | 非目标 | agent 主循环、上下文压缩、记忆/跨脚本状态、审批、调度归内核，不进单次执行语法 | pending | [讨论稿 P1-4](../design/dsl-discussion.md#L269-L276)、[P1-9](../design/dsl-discussion.md#L317-L324) |
| R-003 | 非目标 | MVP 不做并行；`par` 只讨论预留，不产生可执行能力 | pending | [讨论稿 P1-5](../design/dsl-discussion.md#L277-L284)、[P1-10](../design/dsl-discussion.md#L325-L332) |
| R-004 | 非目标 | 不做类型系统、模块/import、try/catch、递归、通用对象字面量、正则字面量 | baseline | v0.1 §9（尚未重新拍板） |
| R-005 | 约束 | 实现语言为 CT；但 CT 只作实现语言，运行期语义（动态值、管道、工具注册、事件）需自建 | pending | [讨论稿 §5](../design/dsl-discussion.md#L349-L366) |
| R-006 | 约束 | 单文件脚本；值是动态的（null/bool/number/string/json_object/json_array） | baseline | v0.1 §4 R5、§9 |
| R-007 | 约束 | 三条隐式规则：隐式 await、隐式管道传参、`$` 指代 into 当前对象 | baseline | v0.1 §1 原则 3 |
| R-008 | 约束 | 文档四层与单份 ≤300 行（DOC-S2）；本仓库当前存在候选偏离，见 §6 | active | `AGENTS.md` 50-57、980 |
| R-009 | 约束 | 未拍板项不得写成 accepted 决策；只能登记为 pending | active | 用户 2026-11-12 指示 |

状态词：

- `baseline`：v0.1 原文里的主张，当前只作讨论基线，**不等于用户已重新拍板**。
- `pending`：方向被评审或用户提过，但结论未定，登记在 PENDING。
- `active`：当前仓库治理规则，已生效。

## 3. 术语

| 术语 | 含义 |
| --- | --- |
| 单次执行 | 一次 `dsl_load` + `dsl_exec` 的生命周期；本规范的范围上限 |
| 工具调用 | 内核注册表里的工具被脚本调用；参数空格分隔，见 S-001 |
| 管道 | `a \|> f b`，把左侧值追加到右侧调用参数末尾；语义仍待定稿 |
| 降级 | `left \|? right`，左侧一次工具调用失败则尝试右侧；优先级与失败单元待定 |
| 结果元数据 | `{ value, truncated, original_size }`，由工具侧产生；DSL 暴露方式待定 |
| into / `$` | 词法作用域绑定；`$` 指代当前绑定值；嵌套与块外规则待定 |
| 策略快照 | 加载时绑定的 allow/deny/emit/registry/constraint 版本，执行期不随热更新改变 |
| trace_id | 一次执行生成的关联 id，随 emit 事件传播，供因果链查询 |
| accepted | 已拍板且已验收；当前 **0 条** |
| unverified | 已拍板但未实现/无门禁；当前 S-001 |
| pending | 未拍板；没有验收判据；当前 PENDING 全部条目 |
| 候选偏离 | 与主规范有张力但未取得用户签字，**不计为已登记 deviation** |

## 4. 决策记录索引

| id | 状态 | 一句话 | 文件 |
| --- | --- | --- | --- |
| D-001 | accepted | 调用统一空格；括号只作分组与 fn 参数表；judge 为用户 | [D-001](../decisions/D-001.md) |

未决问题 **没有** D-* 记录。它们按用户指示登记在待定条目里，避免伪装成 accepted：

- Q1–Q10 与 P0/P1 清单：[docs/spec/PENDING.md](../spec/PENDING.md)
- 各方意见与倾向：[dsl-discussion.md](../design/dsl-discussion.md)

## 5. 规格索引

| ID | 行为 | 状态 | 文件 |
| --- | --- | --- | --- |
| S-001 | 调用形态：空格参数，括号仅分组 | unverified | [S-001](../spec/S-001-call-form.md) |
| P-001..P-019 | 未决问题清单 | pending | [PENDING](../spec/PENDING.md) |

## 6. 候选偏离（未签字，不计为已登记 deviation）

| # | 条款 | 现状 | 为什么不硬套 | 收敛 |
| --- | --- | --- | --- | --- |
| C-1 | DOC-S2 单份文档 ≤300 行 | `docs/design/dsl-spec-v0.1.md` 516 行、`docs/design/dsl-discussion.md` 521 行 | v0.1 是用户提供的基线原文，拆分等于改写原文；讨论稿是单一问题清单，拆开会出现重复与断链 | 定稿时把 v0.1 归档为历史输入，讨论稿按主题拆到 `docs/spec/` 与 `docs/decisions/` |
| C-2 | G0 实例化项（`docs/session-map.md`、`tools/check.sh`、`docs/snippets/`、Issue 前缀） | 均未建；`AGENTS.md` 的实例化表已如实写“未建” | 仓库尚无实现、无门禁、无多会话 phase；现在造门禁会把未拍板的语法固化成规则 | M1 开工前补 session-map 与最小 `tools/check.sh`，门禁只检查文档链接与规范 pin |
| C-3 | G4 snippet 渲染 | 无 `docs/snippets/`，文档中的代码块是待定语法示例 | 未定稿语法不能进可执行 snippet，否则等于提前验收 | 定稿并实现 M1 后，把 §8 示例迁入 snippet 与 golden |
| C-4 | 6.6 T-7 先红后绿 | 当前是纯文档仓库，无实现任务 | 无行为改动，无需红证；硬套会产生空提交 | M1 首个实现任务起执行 T-7 |

以上四条都**没有**用户签字，因此不写入 `AGENTS.md` 的 `deviation:` 段；它们是待用户裁决的候选偏离。

## 7. 当前状态与入口

- 规范原文基线：`docs/design/dsl-spec-v0.1.md`（非定稿）
- 讨论稿：`docs/design/dsl-discussion.md`（非规范）
- 规格层：`docs/spec/`
- 决策层：`docs/decisions/`
- 仓库治理：`AGENTS.md`（v1.7.0 生成块原样入库）

下一步：用户逐条裁决 `docs/spec/PENDING.md` 的 P-001..P-019；拍板前不创建带版本号的新规范。
