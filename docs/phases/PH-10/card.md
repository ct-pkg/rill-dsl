# PH-10 立项卡：Shell 宿主能力层（Host 轨）

> 状态：正常开卡。体系见 `docs/phases/README.md`。
> 对齐：`docs/planning/rill-0.1.0-phase-plan.md` phase 10；roadmap phase 10「Shell 宿主能力层」。
> 规范版本快照：`1.9.0`。语言规范：`docs/RILL-0.1.0.md`（0.1.1，只读）。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-10`，目录 `docs/phases/PH-10/` |
| 目标 | 在 Mac 上把 0.1.1 当脚本语言跑起来：实现真实 OS 能力，不改语法、parser 与求值规则。 |
| 范围 | 做什么：进程/文件路径/env/stdio/退出码五类能力、`run --profile shell`、Shell 动词注册、双 profile AST 一致。不做什么：OS 管道进语法、Windows、信号/流式/PTY、生产权限。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | PH-6 的 `Value`/`ExecOutcome`；PH-1 的 `HostCapabilities`/`HostProfile` 形状；PH-4 的 profile 校验。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `10`（收口目标产品版本 `0.10.0`）。 |
| 已知风险 | `\|>` 与 OS 管道混淆；退出码/stderr 塞进 `$`；二进制值有损；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| 进程：spawn/exec、argv/cwd/env/timeout、捕获 stdout/stderr、`ProcessResult` | 不把 argv 引号/通配符写进 DSL 语法 |
| 文件与路径：read/write/stat/list、相对/绝对、`..`、符号链接、权限错误 | 不把 workspace root 强加给 Shell |
| env：子进程继承/覆盖、读取当前 env、进程级隔离 | 不做全局可变环境 |
| stdio：stdin 文本/`Bytes`、stdout/stderr 捕获、重定向走进程能力 | 不让 `\|>` 承担 OS 管道 |
| 退出码：成功 0、未处理失败非 0、`[error]` 后按 profile 策略；只留映射 | 不在 DSL 写死退出码数字 |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `src/rill/host/shell.py` | 五类能力的 OS 实现 |
| `src/rill/cli.py` | `rill run --profile shell` |
| `testdata/0.1.0/host/shell/` | 五类能力各成功/失败 fixture |
| `docs/planning/rill-0.1.0-shell-profile.md` | 能力清单、manifest/CLI 形态、与 Agent 对照 |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-10-T1 | `src/rill/host/shell.py`（进程能力） | `feat(host): PH-10-T1 进程能力` | `git revert <sha>` | `bash tools/check-0.1.0.sh --show host/shared/read-send` | M | E-1,E-2 |
| PH-10-T2 | `src/rill/host/shell.py`（文件/env） | `feat(host): PH-10-T2 文件与环境` | `git revert <sha>` | `bash tools/check-0.1.0.sh --kind host-ast-equal` | M | E-1 |
| PH-10-T3 | `src/rill/host/shell.py`（stdio/退出码） | `feat(host): PH-10-T3 stdio 与退出码` | `git revert <sha>` | `bash tools/check-0.1.0.sh --check-fakes` | M | E-1,E-3 |
| PH-10-T4 | `testdata/0.1.0/host/shell/` 五类 fixture | `feat(host): PH-10-T4 Shell fixture` | `git revert <sha>` | `bash tools/check-0.1.0.sh --bucket host` | S | E-4 |
| PH-10-T5 | `docs/planning/rill-0.1.0-shell-profile.md` | `docs(host): PH-10-T5 Shell profile 说明` | `git revert <sha>` | `git diff --quiet HEAD -- src/rill/lexer.py src/rill/parser.py` | S | E-5,E-6 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | 五类能力各有至少 1 个成功 + 1 个失败 fixture | `host/shell/` 十例全绿 |
| E-2 | `ProcessResult.code/stdout/stderr` 可观察；stdin 文本与二进制各 1 例 | 字段断言 + `Bytes` 透传 |
| E-3 | 顶层未处理失败产生非 0 退出码，具体码由 profile 表给出 | `run` 退出码断言 |
| E-4 | 同一 fixture 的 AST 与 agent profile 相等 | `--bucket host` 的 AST 比对 |
| E-5 | 没有 parser/lexer 改动 | `git diff --quiet HEAD -- src/rill/lexer.py src/rill/parser.py` 退出 0 |
| E-6 | 任务清单每项可独立验收（T-6） | 收口对照表逐项贴 `verify` 原始输出 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | PH-6 的 `Value::Bytes/Opaque` 与 `ExecOutcome.host_meta`；`profiles/shell.json`；PH-4 的能力声明校验。 |
| 风险 1 | `\|>` 被当 OS 管道：DSL 管道只传 value。触发信号：文档或错误提示把两者混写。 |
| 风险 2 | 退出码/stderr 塞进 `[error]` 的 `$`：`$` 只能是错误串。触发信号：`$` 出现结构化进程结果。 |
| 风险 3 | 二进制有损编码：PH-6 未预留 `Bytes` 时会被迫转字符串。触发信号：stdin 二进制 fixture 失败。 |
| 风险 4 | 脚本侧声明授权：0.1.1 §五.1 明确禁止。触发信号：fixture 出现授权头。 |

## 6. 收口与 tag

- 收口时产品版本 `0.10.0`；annotated tag `v0.10.0`，message 含 `PH-10` 与收口提交 sha 前 7 位。
- 只推 tag，不推分支、不对外发布。收口对照表：`docs/reviews/closeout-10.md`（收口时新建）。
