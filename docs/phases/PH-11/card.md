# PH-11 立项卡：智能体宿主能力层（Host 轨）

> 状态：正常开卡。体系见 `docs/phases/README.md`。
> 对齐：`docs/planning/rill-0.1.0-phase-plan.md` phase 11；roadmap phase 11「Agent 宿主能力层」。
> 规范版本快照：`1.9.0`。语言规范：`docs/RILL-0.1.0.md`（0.1.1，只读）。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-11`，目录 `docs/phases/PH-11/` |
| 目标 | 把工具/角色/limits 映射到同一 `HostCapabilities`，证明两个宿主只差能力层。 |
| 范围 | 做什么：工具注册表→能力适配、角色/principal、ExecLimits、`run --profile agent`、能力矩阵。不做什么：生产工具/安全策略、真实审批/白名单、真实并发调度、role 语义回灌 parser。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | PH-10 的接口与 Shell 实现；PH-4 的 HostProfile 校验；PH-9 的函数绑定。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `11`（收口目标产品版本 `0.11.0`）。 |
| 已知风险 | role 变所有宿主必选；`[error]` 字符串塞不下工具错误结构；工具绑定与函数绑定混用；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| 进程：映射为 `run`/`exec` 工具，不直接 spawn，返回 `{value, ok}` | 不做真实进程池/限流 |
| 文件：映射为 `read`/`write`，workspace root + path constraint | 不越过工具做 OS 文件访问 |
| env：映射为内核配置/上下文注入，不暴露任意 env | 不做生产密钥注入 |
| stdio：工具返回值、`send`/emit 通道 | 不提供 OS stdin/stdout |
| 角色/limits：Role/Verb/Type 表与 ExecLimits；Shell 的 role 可为空 | 不把 agent role 带回 parser/AST |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `src/rill/host/agent.py` | 工具注册表→能力适配、角色/limits |
| `src/rill/cli.py` | `rill run --profile agent` |
| `testdata/0.1.0/host/agent/` | 与 Shell 同源 fixture + agent 专属能力 |
| `docs/planning/rill-0.1.0-host-matrix.md` | 五类能力在两种宿主下的形态与差异 |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-11-T1 | `src/rill/host/agent.py`（工具→进程/stdio） | `feat(host): PH-11-T1 工具能力适配` | `git revert <sha>` | `bash tools/check-0.1.0.sh --show host/shared/read-send` | M | E-1,E-3 |
| PH-11-T2 | `src/rill/host/agent.py`（fs/env） | `feat(host): PH-11-T2 工具文件与环境` | `git revert <sha>` | `bash tools/check-0.1.0.sh --kind host-ast-equal` | M | E-1 |
| PH-11-T3 | `src/rill/host/agent.py`（role/limits） | `feat(host): PH-11-T3 角色与 limits` | `git revert <sha>` | `bash tools/check-0.1.0.sh --check-fakes` | M | E-3 |
| PH-11-T4 | `testdata/0.1.0/host/agent/` | `feat(host): PH-11-T4 Agent fixture` | `git revert <sha>` | `bash tools/check-0.1.0.sh --bucket host` | S | E-1 |
| PH-11-T5 | `docs/planning/rill-0.1.0-host-matrix.md` | `docs(host): PH-11-T5 能力矩阵` | `git revert <sha>` | `git diff --quiet HEAD -- src/rill/lexer.py src/rill/parser.py` | S | E-2,E-4,E-5 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | Agent profile 能跑完与 Shell 同源 fixture，AST 相等 | `--bucket host` 全绿 + AST 逐节点比对 |
| E-2 | 能力矩阵五类各有 Shell/Agent 两列，差异有文字说明 | `host-matrix.md` 五节齐全 |
| E-3 | `[error]` 仍只拿字符串；结构化错误走 `host_meta`/工具值 | `$` 类型断言 |
| E-4 | 没有 parser/lexer 改动 | `git diff --quiet HEAD -- src/rill/lexer.py src/rill/parser.py` 退出 0 |
| E-5 | 任务清单每项可独立验收（T-6） | 收口对照表逐项贴 `verify` 原始输出 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | PH-10 的 `HostCapabilities` 槽位与方法签名；`profiles/agent.json`；`fakes/tools.json` 的 fake 工具；PH-9 的函数绑定（不重叠）。 |
| 风险 1 | role 变成所有宿主必选：Shell 无角色。触发信号：`--profile shell` 因缺 role 失败。 |
| 风险 2 | 工具错误结构塞进 `$`：`$` 只能是字符串。触发信号：`[error]` 的 `$` 是对象。 |
| 风险 3 | 工具绑定与函数绑定混用：函数绑定留在 PH-9。触发信号：agent 侧需要 FnTable 才能解析工具调用。 |

## 6. 收口与 tag

- 收口时产品版本 `0.11.0`；annotated tag `v0.11.0`，message 含 `PH-11` 与收口提交 sha 前 7 位。
- 只推 tag，不推分支、不对外发布。收口对照表：`docs/reviews/closeout-11.md`（收口时新建）。
