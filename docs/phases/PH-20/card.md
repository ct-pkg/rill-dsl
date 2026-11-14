# PH-20 立项卡：CT Agent 宿主（P8）

> 状态：正常开卡。CT 重写轨道第 8 层。体系见 `docs/phases/README.md`，
> 上游 `docs/planning/rill-0.1.0-ct-rewrite-roadmap.md`。语言规范 `docs/RILL-0.1.0.md`（0.1.1，只读）。
> **CT 缺陷命中点**：PH-51（接口派发，同 PH-19）；无 JSON 库（本卡自建最小编解码）。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-20`，目录 `docs/phases/PH-20/` |
| 目标 | CT 版在 Agent profile 上把工具/角色/limits 映射到同一 `HostCapabilities`，14 个 Agent fixture 全绿。 |
| 范围 | 做什么：工具→能力适配、role/principal、ExecLimits、最小 JSON、14 个 fixture、host 层对拍。不做什么：生产工具/安全策略、真实审批、并发调度、语法改动。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | PH-19 的 `HostCapabilities` 函数指针表；PH-16 的 `Value`；PH-15 的 profile/工具表；`testdata/0.1.0/host/agent/`。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `20`（目标产品版本 `0.20.0`）。 |
| 已知风险 | PH-51 派发、JSON 转义/UTF-8、`[error]` 塞结构化错误；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| 进程→`run`/`exec` 工具；文件→`read`/`write`；env→上下文注入 | 不直接调 OS（能力全部经工具） |
| role/principal 与 ExecLimits；Shell 的 role 可为空 | 不实现生产权限/白名单/审批 |
| 最小 JSON：字符串转义、UTF-8、数字、对象/数组 | 不引入第三方 JSON 库 |
| 14 个 Agent fixture + host 层对拍 | 不改 parser/lexer、不改 golden |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `ct/src/host/agent.h.ct` | Agent 能力声明 |
| `ct/src/host/agent.m.ct` | 工具→能力映射、role/limits |
| `ct/src/json.h.ct` | 最小 JSON 编解码接口 |
| `ct/src/json.m.ct` | 转义/UTF-8/数字/容器实现 |
| `docs/planning/rill-0.1.0-ct-defect-workarounds.md` | 追加 JSON 与 PH-51 的实测与代价（PH-15 建立） |
| `docs/reviews/diff/PH-20.md` | 本阶段差异报告 |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-20-T1 | `ct/src/host/agent.h.ct`、`ct/src/host/agent.m.ct` | `feat(ct): PH-20-T1 Agent 能力映射` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --show host/shared/read-send` | M | E-1,E-2 |
| PH-20-T2 | `ct/src/host/agent.m.ct`（role/limits） | `feat(ct): PH-20-T2 角色与 limits` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --check-fakes` | S | E-3 |
| PH-20-T3 | `ct/src/json.h.ct`、`ct/src/json.m.ct` | `feat(ct): PH-20-T3 最小 JSON` | `git revert <sha>` | `python3 tools/diff/diff.py --layer json` | M | E-4 |
| PH-20-T4 | 14 个 Agent fixture 接管清单 | `test(ct): PH-20-T4 Agent fixture 对齐` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --bucket host` | M | E-1,E-2 |
| PH-20-T5 | `docs/reviews/diff/PH-20.md` 与 workarounds 追加 | `docs(diff): PH-20-T5 Agent 差异报告` | `git revert <sha>` | `python3 tools/diff/diff.py --layer host --profile agent` | S | E-5,E-6,E-7 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | 14 个 Agent fixture 全部通过 | `--bucket host` 的 agent 子集退出 0 |
| E-2 | 同源 fixture 的 AST 与 Shell 相等；差异只允许结果层并登记 | `--bucket host` + registry |
| E-3 | `[error]` 的 `$` 仍是字符串；结构化错误走 `host_meta`/工具值 | `$` 类型断言 |
| E-4 | JSON 输出可被标准解析器接受（转义/UTF-8/数字） | `python3 -m json.tool` 退出 0 |
| E-5 | 没有 parser/lexer 改动 | `git diff --quiet v0.14.0 -- ct/rill_ct.ct` 退出 0 |
| E-6 | host 层对拍 14/14，0 未解释差异 | `docs/reviews/diff/PH-20.md` |
| E-7 | 任务清单每项可独立验收（T-6） | 收口对照表逐项贴 `verify` 原始输出 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | PH-19 的能力表与函数指针派发；PH-15 的工具/profile 表；`tool_server.py`（可继续作为外部进程）。 |
| 风险 1 | **PH-51**：接口用指针接收者会在链式调用点错值。绕法同 PH-19：函数指针表 + 值接收者。代价 +100–200 行派发。 |
| 风险 2 | 无 JSON 库：自写约 500–800 行；转义/UTF-8 易错。触发信号：E-4 的解析器拒绝输出。 |
| 风险 3 | 工具的错误结构塞进 `$`。触发信号：`[error]` 的 `$` 是对象。 |
| 风险 4 | 把 role 设成所有宿主必选：Shell 无角色。触发信号：`--profile shell` 失败。 |

## 6. 收口与 tag

- 收口附 `docs/reviews/diff/PH-20.md` 与 `docs/reviews/closeout-20.md`。
- 版本 `0.20.0`；tag 按 `docs/phases/README.md` §4，本卡不自动打 tag、不 push。
- 收口后 PH-21 才可开工。
