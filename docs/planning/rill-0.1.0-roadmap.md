# RILL 0.1.0 Roadmap：从规范到可运行实现

> 命名取法：`rill-0.1.0-` 前缀表示本组文档只服务 `docs/RILL-0.1.0.md`（内容版本 0.1.1），与仓库现有 `docs/planning/roadmap.md`（面向 `docs/spec/dsl/` 的 `v0.1 rev.1`）区分；`roadmap` 记阶段/依赖/并行，`phase-plan` 记每阶段执行细节，故拆两份。
>
> 依据：[RILL 语言规范 0.1.1](../RILL-0.1.0.md)、[修订简报](../RILL-0.1.0-brief.md)、`docs/review/` 下评审记录。
> 适用范围：0.1.0 系列（当前 0.1.1）。仓库现有 [planning/roadmap.md](roadmap.md) 面向 `docs/spec/dsl/` 的 `v0.1 rev.1`，两套不混用；本文件不改旧路线图，也不改 0.1.1 正文。
> 资源假设：单人；每阶段按约一周工作量切分；这里只排工作量和依赖，不承诺日历。另：§0 是立项时快照，当前入口与样例见 [README](../../README.md)。
>

## 编号说明

phase 1–12 是**阅读顺序**，不是**执行顺序**。硬前置只有 phase 1 → 2 → 3；到 phase 3 之后分成多条可并行的线：

- phase 4、phase 5、phase 6 可以同时开工；
- phase 7 在 phase 6 后，与 phase 4/5 并行；
- phase 8 在 phase 7 后，与 phase 5 并行；
- phase 9 在 phase 8、phase 4 后，与 phase 5、phase 10/11 并行；
- phase 10 在 phase 6 与 phase 1 的 host contract 后，与 phase 7/8/9、phase 11 并行；
- phase 11 在 phase 10、phase 4 后，与 phase 7/8/9 并行；
- phase 12 是汇合点，依赖 phase 4、phase 5、phase 9、phase 11。

## 0. 仓库现状与硬缺口

| 项 | 现状 | 对排期的影响 |
| --- | --- | --- |
| lexer / parser / 解释器 | 没有 | phase 1 之后从零开始；phase 2/3 不能用“改造现有实现”估算 |
| 0.1.1 样例集 | 没有 | `docs/examples/` 的 7 篇面向旧 `v0.1 rev.1`，使用 `let` / `fn` / `\|?` / `# allow:` 等不同语法，只能当场景清单 | 
| AST / token golden | 没有 | phase 2/3 的退出判据必须在 phase 1 先有 harness，否则不可验证 |
| fake 工具 / 工具注册表 | 没有 | phase 6 起需要；不能用真实文件系统/网络替代 |
| CLI | 没有 | `rill tokenize` / `parse` / `check` / `run` / `fmt` 都要在对应阶段新建 |
| 实现语言与仓库落点 | 未定 | phase 1 记录选型；未定之前 phase 2 不开工 |

结论：phase 3 的“全样例 AST 通过”和 phase 12 的“端到端通过”在 phase 1 交付前**不可验证**，不能提前排进日程。

## 0.1 双宿主硬约束（需求，不是建议）

RILL 的早期目标有两个宿主：

1. **智能体宿主**：项目内部使用，能力来自工具注册表、角色/权限、ExecLimits；
2. **Shell 宿主**：在 Mac 上直接当脚本语言用，能力来自进程、文件系统、环境变量、标准输入输出、退出码。

两者**共用同一份语法、同一个 parser、同一套 AST**；差异只在能力层（host adapter），不在词法/语法/求值规则。

排期必须遵守：

- **phase 2/3 零宿主耦合**：lexer/parser 不得 import 角色、工具、权限、进程、文件系统；主语槽只保留语法形态，不判断“这是 agent 角色还是 OS 用户”。
- **phase 4 通过 HostProfile 校验**：`rill check` 接受一个宿主 profile；agent profile 提供 Role/Verb/Type 表，shell profile 提供 OS 用户、路径策略、进程能力。core loader 不硬编码任何一方。
- **phase 6 起留值口子**：`Value` 从第一天保留 `Opaque`/`Bytes` 变体，避免 Shell 宿主接二进制/流时改运行时核心。
- **phase 12 双 profile 验收**：同一 fixture 在两个 profile 上必须得到相同 AST；运行结果只在能力可等价时比较，不等价处标记 host-specific。
- **禁止语法的宿主特判**：任何“反正只在智能体里跑”或“反正在 shell 里跑”的语法放宽/收紧，必须回到 0.1.1 正文重审，不能写进 parser 分支。

## 0.2 实现状态与重写去向（2026-11-15 补记）

上表 §0 是 0.1.1 规划期的历史快照（当时 lexer/parser/解释器确为 0），保留不改。当前状态：

| 项 | 状态 |
| --- | --- |
| Python 参考实现 | `src/rill/`，PH-12 基线 0.12.0；PH-22 收口后产品 0.22.0；PH-1…PH-12 已收口；**永久保留为参考实现与对拍基准**，不随 CT 版淘汰。PH-5 的 `E-3`/`E-5` 于 2026-11-15 裁定移出 0.1.0（见 §0.3），故不是 12 卡全绿 |
| CT 正式实现 | P1 已收口（PH-13：token golden 12/12、82 个源 token 对拍 0 差异）；P2 起未开始 |
| 实现语言账 | R-005 已从 pending 翻面为 decided：CT 为正式实现，Python 为长期参考实现 |
| 重写路线图 | `docs/planning/rill-0.1.0-ct-rewrite-roadmap.md`（PH-13…PH-21，P1…P9） |
| fixture / golden | 语言中立，继续作为**第三方基准**复用；不得为迁就任一实现修改 |
| 对拍 | 每阶段收口固定附 `docs/reviews/diff/PH-<n>.md`；脚本在 `tools/diff/`（PH-13 首次建立） |

本文件 phase 1–12 的编号、依赖与并行结论不因重写而改变；CT 重写另立续号，不改写历史。

## 0.3 PH-5 判据移出记录（2026-11-15）

- `PH-5` 的 `E-3`（fmt golden，三类长词）与 `E-5`（`Bytes`/`Opaque` 格式化断言）
  经用户裁定**移出 0.1.0，记入 0.1.1 遗留**；不是暂缓，也不计为通过。
- 去向：`docs/planning/rill-0.1.1-backlog.md` 的 `BL-001`/`BL-002`；
  逐条账目见 `docs/phases/PH-5/card.md` §7 与
  `docs/reviews/rill-0.1.0-completion-audit.md`。
- 因此 0.1.0 的准确口径是：**12 张 phase 卡已交付，但 PH-5 记 4/6，不是全绿**。
- 本记录只补状态与去向，不改 phase 1–12 的编号、依赖与并行结论。

## 0.4 PH-22 追加（2026-11-15）
- 触发/编号/结案：用户裁定去掉 `@ "name"`，签名 = 动词 + 状语 + 介词形状键（[D-022](../decisions/D-022.md)）；PH-22 接 PH-21，`version-minor=22`；PH-22 前未发布、无历史 tag，2026-11-15 按路径 A 重编号到 0.22.0；自 PH-22 起 `d=0`，PH-23 起按 V-1 得 0.23.0；`d=10` 仅作 PH-13…PH-21 历史注脚（[PH-22 卡](../phases/PH-22/card.md) §9）。
- 范围/依赖：规范正文、Python/CT 实现、语料与编辑器；不改宿主能力，不裁定 P-025/P-026。Python 基线 PH-12；CT 以 PH-21 收口为准；不改变 phase 1–12 的编号与并行结论。

## 1. 完成定义

本路线图的“可运行实现”指：

- `rill parse` 能把 0.1.1 样例解析为稳定 AST，错误带行/列与稳定错误码；
- `rill run` 能在 fake 工具上执行 0.1.1 语义：SVO、`|>`、`[into]/[ok]/[error]`、`{value, ok}`、`each`、`parallel`、`//fn` 函数；
- 非 pending 的 0.1.1 样例全部有 golden；pending 样例以 `xfail-pending` 显式登记，不假装通过；
- 压缩态与展示态可机械互转，回读 AST 等价；
- 规范正文不改；任何语义改动先走 CR 并重定 golden；
- 同一份 fixture 在 agent profile 与 shell profile 上得到相同 AST；能力差异只出现在 host adapter 的返回值，不改变 parser 接受的语法集。

不在本路线图：真实工具接入、权限/审批/白名单、真实 LLM 生成质量评估、性能与并发优化、旧 `v0.1 rev.1` 的兼容实现。

## 2. 阶段总览

| 阶段 | 轨道 | 目标一句话 | 依赖 | 可并行 | 退出锚点 |
| --- | --- | --- | --- | --- | --- |
| phase 1 | 基线 | 冻结输入、建 0.1.1 样例集与门禁骨架 | 无 | 无 | 12+ fixtures、harness 可运行、选型记录落盘 |
| phase 2 | Parser | 词法：符号、关键字、引号、`//map`/`//fn` 头、标记符 | phase 1 | 无（phase 3 依赖它） | token golden 全绿；`//map {` 与 `//map` 注释分流正确；map 行模式与 `E-01` 正确 |
| phase 3 | Parser | 完整 §三 产生式与 AST | phase 2 | 无（phase 4/5/6 依赖它） | AST golden 全绿；条件位/调用/独立介词块可归约 |
| phase 4 | Parser | 加载期校验与诊断（不执行） | phase 3 | 与 phase 5、phase 6 | 负例全部有稳定错误码；map/fn 表校验完成 |
| phase 5 | Parser | 展示/压缩互转与回读 | phase 3 | 与 phase 7/8/9 | 压缩→展示→压缩 AST 等价；长词/转义 property 通过。**E-3/E-5 已裁定移出 0.1.0（§0.3），不计通过** |
| phase 6 | Runtime | 值模型、`{value, ok}`、`$` 基准 | phase 3 | 与 phase 4、phase 5 | truthy/falsy、ok 传播、默认 break 单测全绿 |
| phase 7 | Runtime | 简单语句、尾随块、段输出 | phase 6 | 与 phase 4、phase 5 | 段输出 4 种情形 + `[into]` 失败顺序全绿 |
| phase 8 | Runtime | 管道、`if`、`each`、`break` | phase 7 | 与 phase 5 | 管道只传 value；each 数组/失败继续；break 场域全绿 |
| phase 9 | Runtime | `parallel`、`[results]`、`//fn` 函数 | phase 8、phase 4 | 与 phase 5、phase 10/11 | 分支结果数组、函数绑定/默认值/返回全绿 |
| phase 10 | Host | Shell 宿主能力层：进程/文件路径/env/stdio/退出码 | phase 6、phase 1 host contract | 与 phase 7/8/9、phase 11 | 五类能力各有 golden；同一 AST 在 shell profile 可执行 |
| phase 11 | Host | 智能体宿主能力层：工具/角色/limits 映射到同一 HostCapabilities | phase 10、phase 4 | 与 phase 7/8/9 | agent profile 与 shell profile 共用 AST；能力差异只在结果 |
| phase 12 | 集成 | 双宿主集成：CLI + 全样例 + golden + 双 profile 一致性 | phase 4、phase 5、phase 9、phase 11 | 无 | 非 pending 样例全通过；pending 列 xfail；双 profile AST 相等；round-trip 通过 |
| PH-22（追加） | 语言变更 | 函数签名去名：签名 = 动词 + 状语 + 介词构成的形状键，见 D-022 | PH-12；CT 以 PH-21 收口状态为准 | 无 | 已收口：E-1…E-28 全绿；产品 0.22.0、tag `v0.22.0`；Python/CT 对拍 0 未解释差异；旧 `@ "name"` 清零 |
| PH-23（追加） | 语言变更 | P-025=B：签名层不识别类型前缀，常量位按 AST 字面原文比较，`shape_version=2` 仅定义侧（[D-024](../decisions/D-024.md)） | PH-22 收口 `0.22.0`；CT 以 PH-22 收口基线为准 | 无 | 已收口：E-1…E-24 全绿；产品 0.23.0、tag `v0.23.0`；全层对拍 0 差异；PH-22 E-26 已取代不回改 |

## 3. 两条横切主线

语义上只有两条横切主线：**Parser**（词法+语法）与 **Runtime**（求值+运行时）。宿主轨是双宿主约束落在能力层的实现，不是第三条语义主线；它不改语法，也不改求值规则。

### 3.1 词法与语法（Parser）

**范围**：`//map{}` / `//fn{}` 头、符号扫描、关键字、引号/转义、`短词 标记符 长词`、§三 全部产生式、AST、加载期校验、展示/压缩格式化。

**最先闭合的点**（没有它后面全是猜）：

1. `//` 与 `//map` / `//fn` 的边界：`//map{`、`//map {`、`// map {` 都是头；`//map` 后无 `{` 是注释（0.1.1 §3.1）。
2. 标记符的词法：`//map{}` 块内每行按 `短词 + 第一个非短词字符（标记符）+ 行尾（长词）` 切分，该行不启动动词扫描；标记符仅 `'` / `` ` `` / `<`，非法标记报 `E-01`（0.1.1 §3.2）。
3. 关键字优先：`if` / `else-if` / `each` / `parallel` / `break` 在语句起始先于“主语”匹配（评审 I-01/I-02/I-03）。

**第二批闭合点**（phase 3 出口前）：

- `verb_call := [subject] <动词> ...`：恢复可选主语，否则 `if $cfg <contains> debug=true` 不可归约（0.1.1 §三；评审 I-04/R-24）；
- `arg := value`：调用实参不再是占位符（0.1.1 §三；评审 R-14/R-17）；
- `prep_block_stmt`：独立 `[into] $cfg {}` / `[ok] $x {}` 是语句（评审 R-03/I-09）；
- 多介宾短语 `prep_phrase*`：`[with] prod … [in] $file`（评审 R-01）；
- `[results]` 只允许 `parallel` 块级（评审 R-02）。

**最先会踩的坑**：`[into]/[ok]/[error]` 的介词身份与块头身份（I-08/I-09）、`[in]` 循环头与介词位（I-05）、`else-if` 零空格（I-03）、`//map` 标记符（R-18/R-20）。phase 2/3 的 golden 要直接覆盖这些，不留给集成阶段。

### 3.2 求值与运行时（Runtime）

**范围**：SVO 求值、`{value, ok}` 成败通道、`$` 指代、`[into]/[ok]/[error]` 顺序与段输出、`|>`、`if`/`each`/`break`、`parallel`/`[results]`、`//fn` 调用。

**最先闭合的点**：

1. **`{value, ok}` 是唯一成败通道**：动词返回 `{value, ok}`；`[ok]` 只在 `ok == true` 触发，`[error]` 只在 `ok == false` 触发；`$` 分别是 `value` 与错误串（0.1.1 §4.10；评审 R-06/C-10）。没有它，尾随块和管道都没有统一语义。
2. **管道只传 `value`**：`ok` 在段内被 `[ok]/[error]` 消费，下游只拿 value（0.1.1 §4.6；评审 I-38/R-08）。这条不定，`|>` 的每个下游都要重新猜输入。
3. **段输出顺序**：`[into] → [ok]/[error] → 段输出 → |> 下游`，并落到 4 种默认输出（0.1.1 §4.11；评审 I-27/I-28/I-30）。

**第二批闭合点**：

- `$` 的基准指代：`[into]` / each / `[ok]` / `[error]` / parallel branch / `[results]` / 无介宾语句（0.1.1 §4.8；评审 I-24/R-07/R-08/R-09/R-12）；
- `[into]` 失败是否走用户 `[error]`、后续 `[into]` 是否执行（I-14/R-26）；
- 多分支同时失败取哪个错误、分支内 `[error]` 处理过是否还算失败（I-18/R-13）；
- 函数返回值、去重参数绑定、尾部默认值（R-16/R-17）。

### 3.3 双宿主能力层（宿主轨）

Parser 和 Runtime 只认 `HostCapabilities` 接口；Shell 与 Agent 各自实现，不把宿主能力写进语法。

| 能力 | Shell 宿主形态 | 智能体宿主形态 | 共用接口 |
| --- | --- | --- | --- |
| 进程调用 | spawn/exec，argv、cwd、env、timeout；返回 `ProcessResult{code, stdout, stderr}` | `run`/`exec` 动词经 VerbRegistry；返回 `{value, ok}`，不直接碰 OS | `ProcessCapability` |
| 文件与路径 | OS 文件系统；相对/绝对路径、cwd、符号链接、权限 | `read`/`write` 工具；workspace root + path constraint | `FsCapability` |
| 环境变量 | 子进程继承/覆盖；进程级 `Env` | 内核配置/上下文注入；不暴露任意 env | `EnvCapability` |
| 标准输入输出 | stdin/stdout/stderr 流；重定向 | 工具返回值、`send`/emit 通道 | `StdioCapability` |
| 退出码 | 进程退出码；成功 0，未处理失败非 0 | 不产生 OS 退出码；映射为 `DslResult`/工具错误 | `ExecOutcome.exit_code`（宿主映射） |
| 能力边界声明 | 外部 manifest/CLI profile；脚本不写授权头 | 内核角色/工具白名单；脚本不写授权头 | `HostProfile.capabilities` |
| 错误传播 | `ok=false` → 非 0 退出；`[error]` 只拿错误串；`code/stderr` 走 host value | `ok=false` → 工具错误/DslResult；`[error]` 只拿错误串 | `ExecOutcome` |

#### 3.3.1 必须现在留的口子（以后改不动）

1. **`HostCapabilities` 接口**：process / fs / env / stdio / exit 五组能力；Parser 不得直接 import 其中任何一个。
2. **`HostProfile`**：能力声明与权限边界的外部载体（Shell：manifest/CLI；Agent：内核配置/角色表）；DSL 脚本无权声明（0.1.1 §五.1）。
3. **`ExecOutcome`**：`{value, ok, error, host_meta?}`；`exit_code` 由宿主映射，DSL 不定义数字码。
4. **`Value::Opaque` / `Value::Bytes`**：phase 6 就预留；Shell 的二进制 stdin/stdout、文件内容、进程输出需要它，后补会改运行时核心。
5. **`ProcessResult` 形状**：`code` / `stdout` / `stderr` 三个字段；不作为 `[error]` 的 `$`，而是宿主值。
6. **parser 纯度门禁**：phase 2/3 的依赖图不得出现 host/process/fs/role 模块；CI 加一条 import 检查。
7. **类型槽**：`类型:值` 只作为裸词进入 AST；拆分与校验由 `HostProfile` / TypeRegistry 负责，Shell 映射 `file`/`dir`/`net`，Agent 映射工具类型；parser 不认识任何具体类型名。

#### 3.3.2 可以推迟到第二个宿主接入时再定

- Shell 侧具体动词名与调用形态（`run`/`exec`/`sh`）、argv 引号规则、shebang/manifest 的具体格式；
- 流式读写、信号处理、超时后强杀、Windows 路径与进程模型；
- 具体退出码数字（只留映射钩子，不在 0.1.1 写死）；
- Agent 侧工具集、角色表、审批/白名单的具体策略（0.1.1 已声明为边界）；
- `parallel` 的真实调度、进程池大小、背压。

#### 3.3.3 0.1.1 正文里与“双宿主通用”冲突的地方

| 位置 | 写法 | 冲突点 | 计划处理 |
| --- | --- | --- | --- |
| §4.1、§五 | 主语是“角色 + 权限的载体”，默认当前角色；RoleRegistry | Shell 没有角色，只有 OS 用户；这是智能体专属形态 | phase 4 把 role 抽象为 `principal`：agent=角色，shell=OS 用户；role 校验改为 profile 可选 |
| §五.1 | “脚本无权声明授权头” | Shell 脚本本身就是程序，能力边界需要 manifest/CLI 声明；原句默认了“内核在外部” | 改为“脚本不声明；由 HostProfile 声明”，Shell 用 manifest/CLI，Agent 用内核配置 |
| §4.10 | `[error]` 的 `$` 是错误信息字符串，无结构化字段 | Shell 需要 stderr 与退出码；全塞进字符串会丢结构 | 保留 `$` 为字符串；另用 `ProcessResult`/`ExecOutcome.host_meta` 暴露，phase 6 留口 |
| §4.10–§4.11 | 顶层失败“中断整个 program”，未定义退出码 | Shell 需要可预测的退出码；Agent 不需要 OS 退出码 | `ExecOutcome.exit_code` 由 HostCapabilities 映射；0.1.1 不写死数字 |
| §4.6 | `\|>` 是 DSL 值管道 | Shell 用户会误以为是 OS 管道；两者语义不同 | 文档与 phase 10 明确：`\|>` 只传 DSL value；OS 管道由 `ProcessCapability` 的 stdin/stdout 表达 |
| §4.16–§4.17 | 值只有 STRING/NUMBER/数组/对象/null；映射与展示按文本处理 | Shell 的二进制/流没有值形态 | phase 6 预留 `Bytes/Opaque`；phase 5 只对文本值做格式化，二进制走 host 值 |
| §4.14 | `parallel` 是语言结构，调度未定义 | Shell 需要进程并发；Agent 需要工具并发/限流 | 语义保持 logical parallel；调度放 `HostCapabilities`，phase 10/11 各自实现 |

## 4. 依赖图

```text
phase 1
   └─ phase 2 ── phase 3 ──┬─ phase 4 ─────────────┐
                 ├─ phase 6 ── phase 7 ── phase 8 ── phase 9 ── phase 12
                 ├─ phase 5 ────────────────┤
                 └─ phase 10 ── phase 11 ──────────┘
```

- 实线依赖：phase 2→phase 3→phase 6→phase 7→phase 8→phase 9→phase 12；phase 3→phase 4；phase 3→phase 5；phase 6→phase 10→phase 11；phase 4→phase 11。
- phase 4 与 phase 5/6 可在 phase 3 后并行；phase 10 在 phase 6 后与 phase 7/8/9 并行；phase 11 在 phase 10+phase 4 后与 phase 9 并行；phase 12 需要 phase 4、phase 5、phase 9、phase 11。
- 单人执行时按关键路径 phase 1→phase 2→phase 3→phase 6→phase 7→phase 8→phase 9→phase 12 推进；phase 4 插在 phase 7/8 之间，phase 10/11 插在 phase 6 之后、phase 9 之前。不要同时开 phase 10 和 phase 7：两者都改 `ExecOutcome` 的 host 字段，先冻结 `HostCapabilities` 接口。

## 5. 关键路径与并行边界

**关键路径**：语义关键路径为 phase 1 → phase 2 → phase 3 → phase 6 → phase 7 → phase 8 → phase 9 → phase 12（8 个阶段）；含宿主轨共 12 个阶段（phase 1、phase 2–5、phase 6–9、phase 10–11、phase 12）。phase 4 不在关键路径上，但它卡 phase 9/11/12；phase 5 不在关键路径上，但它卡 phase 12；phase 10/11 在 phase 6 之后与 phase 7–9 并行，单人时插在 phase 6 与 phase 9 之间。

**可并行**：

- phase 4（加载期校验）与 phase 6（值模型）：都只依赖 phase 3 的 AST，互不改同一接口；phase 4 产出 `HostProfile`/`MapTable`/`FnTable`/`VerbTable`，phase 6 产出 `Value`/`ExecResult`，接口在 phase 3 结束时冻结。
- phase 5（格式化）与 phase 7/8/9：格式化只读 AST，不改求值器；长词/转义规则与 phase 6 的 `STRING` 节点共用定义，需在 phase 5 开工前对齐节点形态。
- phase 10（Shell 能力）与 phase 7/8/9：phase 10 只实现 `HostCapabilities` 的 OS 版本，不改 DSL 求值规则；如果 phase 10 需要 `Value::Bytes/Opaque`，在 phase 6 接口里已预留。
- phase 11（Agent 能力）与 phase 9：phase 11 只把工具/角色/limits 映射到同一接口；phase 11 依赖 phase 4 的 profile 校验，但不依赖 phase 9 的 parallel 细节。

**不可并行**：

- phase 2 与 phase 3：词法 token 边界未定，parser 无法开工。
- phase 6→phase 7→phase 8→phase 9：每一层都改同一求值器的核心数据结构（`{value, ok}`、段输出、`$` 栈），并行会反复改接口。
- phase 10 与 phase 7：两者都改 `ExecOutcome` 的 host 字段；先冻结 `HostCapabilities` 与 `ExecOutcome`，再分别开工。
- phase 9 与 phase 4 的 map/fn 表：phase 9 依赖 phase 4 的加载期解析结果；如果两人并行，先冻结表结构。

## 6. 评审坑 → 阶段对照

排期时把评审已经暴露的坑直接变成对应阶段的退出负例；不要留到 phase 12 才发现。

| 评审条目 | 落到阶段 | 防再踩措施 |
| --- | --- | --- |
| I-01/I-02/I-03 关键字、产生式、`else-if` | phase 2/3 | 关键字表单测；§三 产生式逐条 AST golden；`else-if` 零空格用例 |
| I-08/I-09/R-03 介词 vs 块头、独立形式 | phase 3/4 | `]` 位置三分表；`prep_block_stmt`；`<merge> feature [into] main` 与 `[into] $cfg {}` 都进 golden |
| R-01/R-02 多介宾、parallel 管道 | phase 3 | `prep_phrase*` 与 `parallel_clause [|> ...]` 各 2 例 |
| I-04/R-24 `verb_call` 主语/条件位 | phase 3 | `if $cfg <contains> debug=true` AST 必须可归约 |
| R-10/R-11 each 头与裸词 | phase 3/4 | 头表达式与 body 切分用例；裸词 value 按 A2 合法，phase 4 加 `W-01` 提示 |
| I-05 `[in]` 双位置 | phase 3 | each 头与 body 内 `[in]` 各 1 例 |
| I-29/R-05 尾随块数量 | phase 3 | 重复 `[ok]/[error]` 解析期拒绝 |
| I-14/R-26 `[into]` 失败 vs `[error]` | phase 7 | 首个 `[into]` 失败 + 用户 `[error]` 的执行轨迹 golden |
| I-27/I-28/I-30 段输出/覆盖 | phase 7 | 4 种段输出 + 跨段 `[error]` 各 1 例 |
| I-24/R-07/R-08/R-09 `$` 指代 | phase 6/7/8 | 每个语境 1 个 `$` golden；嵌套最近块优先 |
| I-18/R-12/R-13 parallel 汇合/失败 | phase 9 | 分支成功/未处理失败/已处理失败三态 + `[results]` 数组 |
| I-37/R-17/R-28 调用绑定 | phase 4/9 | 去重参数位、默认值、未声明函数、`arg := value` 负例 |
| I-32/R-18~R-22 map/展示 | phase 2/5 | 含空格长词、引号、`'`/`` ` ``/`<` 三类标记、前缀歧义负例 |
| R-23 `.name` vs dotfile | phase 4 | `.env` 作宾语 vs `.host` 作 self 字段各 1 例 |
| R-27 顶层失败 | phase 7 | 顶层失败终止 program，不进入下一条语句 |
| 双宿主耦合 | phase 2/3/4/10/11 | phase 2/3 依赖图禁 host 模块；phase 4 用 HostProfile；phase 10/11 共用 AST |

## 7. 原未决项的裁决结果

### 7.1 裸词在 value 位——已裁定 A2

- **裁定**：0.1.1 采用 A2，`value := STRING | NUMBER | 裸词 | $变量 | .字段`；裸词按 `STRING` 处理，词面即值，不查变量、不查映射表。
- **落点**：§三 `value`、§二 值行、§4.13、§4.15、§4.18；`§4.15` 的“字面量”改为 `value` 分支。
- **示例**：`each $f [in] xs`、`break done`、`@ "name" bare` 保留原样，均合法。
- **提示**：phase 4 增加 `W-01`（`each [in]` 裸词按字符串处理，警告不报错），见 0.1.1 §4.20。
- **阻塞解除**：phase 3、phase 8、phase 9、phase 10/11、phase 12 不再因本项阻塞；phase 1 的 `pending/` 不再登记裸词用例。

### 7.2 `//map` 的 `<` 与动词定界符——已裁定 B1

- **裁定**：0.1.1 采用 B1，`//map{}` 块内进入行模式：每行按 `短词 + 第一个非短词字符（标记符）+ 行尾（长词）` 切分，该行不启动动词扫描。
- **落点**：§3.1、§3.2、§4.17；标记符仅 `'` / `` ` `` / `<`。
- **错误**：非法标记报 `E-01`「map_entry 标记符非法」；正文出现 `r<read` 这类主语 + 未闭合动词报 `E-02`「动词未闭合；映射定义必须在 `//map{}` 块内」。
- **阻塞解除**：phase 2 不再单列 `<` 标记 pending；phase 3、phase 4、phase 5、phase 10/11、phase 12 的 `<r>`/golden 用例按正常正例纳入。

## 8. 不在本路线图

- 生产级权限/审批/白名单、真实 LLM 生成质量、性能与调度优化：不在本路线图。
- Shell 宿主的进程/文件/路径/env/stdio/退出码**在 phase 10 范围内**，用真实 OS 能力；Agent 宿主的工具/角色/limits 映射**在 phase 11 范围内**，用 fake 工具与 profile 验证，不接生产安全策略。
- 旧 `v0.1 rev.1` 的语法兼容：`docs/spec/dsl/` 与 `docs/examples/` 不属于本路线图的实现目标。

## 9. 变更与门禁规则

1. 0.1.1 正文冻结；A2/B1 已落文，后续改动先开 CR，不在代码里私自解释。
2. 每个阶段先有红例，再有实现；退出判据以命令退出码和 golden 为准，不以“看起来对”为准。
3. pending 用例必须显式标记，不得从通过率中静默剔除；phase 12 报告要同时给出通过数和 xfail 数。
4. 阶段交付物与阶段计划中的文件名一致；改阶段范围先改计划，再改代码。

## 附录：新旧阶段对照

| 旧编号 | 新编号 | 名称 |
| --- | --- | --- |
| P0 | phase 1 | 基线、样例与门禁骨架 |
| P1 | phase 2 | 词法 |
| P2 | phase 3 | 语法与 AST |
| P3 | phase 4 | 加载期校验与诊断 |
| P4 | phase 5 | 展示/压缩互转与回读 |
| R1 | phase 6 | 值模型与 `{value, ok}` |
| R2 | phase 7 | 简单语句、尾随块与段输出 |
| R3 | phase 8 | 管道、`if`、`each`、`break` |
| R4 | phase 9 | `parallel` 与 `//fn` 函数 |
| H1 | phase 10 | Shell 宿主能力层 |
| H2 | phase 11 | Agent 宿主能力层 |
| I1 | phase 12 | 双宿主集成 |

早期会话标题里的“Phase 0 基座”“Phase 1 词法”是既成事实；与本文对不上号时，以本表为准。
