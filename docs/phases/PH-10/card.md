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
| `src/rill/host/__init__.py` | Shell 宿主包入口 |
| `src/rill/host/shell.py` | 能力清单、五类能力、真实 VerbRegistry |
| `src/rill/cli.py` | `run --profile shell [--host-profile <path>]`、真实宿主接线、退出码 |
| `src/rill/loader.py` | shell profile 的 `run` / `env` 动词集（parser 不感知宿主） |
| `testdata/0.1.0/host/shell/` | 五类能力成功/失败 fixture（12 例）、能力清单、端到端真脚本 |
| `tests/phase10/` | 可失败单测 5 个 + 共用夹具 |
| `docs/planning/rill-0.1.0-shell-profile.md` | 动词映射表、能力清单、manifest/CLI 形态、与 Agent 对照 |
| `docs/reviews/phase10-red.md` | 逐任务红证与转绿记录 |

fixture 不叫 `source.rill` / `case.json`，避免被 harness 当成 `--fakes` run 用例：
本 phase 的 fixture 由 `tests/phase10/test_host_fixtures.py` 在临时 cwd 里驱动真实宿主。

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-10-T1 | `src/rill/host/shell.py`（能力清单 + 进程能力） | `feat(host): PH-10-T1 进程能力` | `git revert <sha>` | `python3 tests/phase10/test_process.py` | M | E-1,E-2 |
| PH-10-T2 | `src/rill/host/shell.py`（文件/env + 能力拒绝） | `feat(host): PH-10-T2 文件与环境` | `git revert <sha>` | `python3 tests/phase10/test_fs_env.py` | M | E-1 |
| PH-10-T3 | `src/rill/host/shell.py`（真实 VerbRegistry）+ `src/rill/cli.py`（`--host-profile`、fakes 优先、agent 无宿主）+ `src/rill/loader.py`（shell 动词集） | `feat(host): PH-10-T3 宿主接线` | `git revert <sha>` | `python3 tests/phase10/test_wiring.py` | M | E-1,E-4 |
| PH-10-T4 | `src/rill/host/shell.py`（stdio/退出码）+ `src/rill/cli.py`（退出码、`Bytes` 输出） | `feat(host): PH-10-T4 stdio 与退出码` | `git revert <sha>` | `python3 tests/phase10/test_stdio_exit.py` | M | E-2,E-3 |
| PH-10-T5 | `testdata/0.1.0/host/shell/`（12 fixture + 3 能力清单 + e2e）+ `docs/planning/rill-0.1.0-shell-profile.md` | `feat(host): PH-10-T5 fixture 与说明` | `git revert <sha>` | `python3 tests/phase10/test_host_fixtures.py` | M | E-1,E-4,E-6 |

依赖顺序：T1 → T2 → T3 → T4 → T5。T3 的 CLI 接线压着 T4（退出码）与 T5（fixture 执行），
所以在 T3 之前 T1/T2 只测能力对象，不测 CLI。verify 一律是可失败的单测命令；
`--show` / `--kind` / `--check-fakes` 这类只打印或只校验资产的命令不作为验收依据。

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | 五类能力各有至少 1 个成功 + 1 个失败 fixture | `test_host_fixtures.py`：12 例逐条断言 ok/value/error/退出码 |
| E-2 | `ProcessResult.code/stdout/stderr` 可观察；stdin 文本与二进制各 1 例 | `test_process.py`：字段断言 + `Bytes` 透传 |
| E-3 | 顶层未处理失败产生非 0 退出码，具体码由能力清单给出 | `test_stdio_exit.py`：`exit_codes` 换成 7 后退出码必须是 7 |
| E-4 | 同一 fixture 的 AST 与 agent profile 相等 | `test_host_fixtures.py`：逐 fixture 比对两个 profile 的 AST |
| E-5 | 没有 parser/lexer 改动 | `git diff --quiet d686ca3 -- src/rill/lexer.py src/rill/parser.py` 退出 0 |
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

## 8. 规范缺口与实现裁定（不改变规范正文）

下列各条在规范里没有唯一表述。裁定只写进本表，不写进 `docs/RILL-0.1.0.md`；
红证与实现位置见 `docs/reviews/phase10-red.md`。

| # | 位置 | 缺口 | 本 phase 的实测与裁定 |
| --- | --- | --- | --- |
| 1 | §4.10 | 独立 `[ok] $x { ... }` / `[error] $x { ... }` 的行为未定义 | **实测：仍报 `E-RUN-UNSUPPORTED`**，不阻塞本 phase 的真脚本（真脚本只用尾随块）。登记为后续 CR |
| 2 | §4.16 / §五 | `read` / `run` / `env` 是否属于 0.1.1 动词集 | **实测：`run` / `env` 只加进 shell profile 的加载期动词集**；agent profile 仍报 `E-LOAD-VERB-UNKNOWN`。动词名是宿主注册表内容，parser 不变 |
| 3 | §4.9 / §4.16 | 进程 argv 怎么从 DSL 值来 | **实测：`run` 的宾语是一个字符串，宿主用 `shlex.split` 切 argv**；DSL 不新增引号/通配符语法 |
| 4 | §4.8 | 进程结果放哪里 | **实测：`value` = stdout（UTF-8 文本；非法 UTF-8 为 `Bytes`），`host_meta.process = {argv, code, stdout, stderr, timed_out}`**；`$` 不出现结构化结果 |
| 5 | §4.10 / §五 | 未处理失败的退出码从哪来 | **实测：能力清单的 `exit_codes {ok, unhandled}` 映射**，默认 `{0, 1}`；`[error]` 处理后走 `ok` 映射。DSL 不写数字 |
| 6 | §4.2 | `send` 在 Shell 宿主写到哪里 | **实测：写 stderr**（避免污染 `run` 的 JSON stdout 协议），并在 `host_meta.stdio.channel` 记录 `stderr` |
| 7 | §4.7 / §4.10 | 危险操作（`write` / 进程 spawn）如何授权 | **实测：外部能力清单 `--host-profile` 的 `allow` 声明**；未声明时 `rill run` 直接给 `E-HOST-CAPABILITY-DENIED` 诊断（退出 2），消息写明 `slot.operation`。不用 `ok=false` 是因为 §4.10 的隐式 `[error]` 会把错误串改写成 `RILL DSL ERROR`，丢掉能力名。脚本内不能声明授权（§五.1） |
| 8 | §五.8 | 有真实映射的动词之外怎么处理 | **实测：`search` / `parse` / `replace` / `contains` / `review` 无真实映射**，调用即 `E-RUN-VERB-UNREGISTERED`（stage=run），不静默成功 |
| 9 | §4.16 | `Bytes` / `Opaque` 能否出现在最终 `run` 输出 | **实测：`Bytes` 序列化为 `{"$bytes": "<base64>"}`，`Opaque` 为 `{"$opaque": tag}`**；二进制不经过 `$` 字符串 |
| 10 | §4.16 | stdin 初始值 | **实测：`run` 的 stdin = 管道/`$` 输入的字符串（`Bytes` 直接写字节）**；没有输入时 stdin 为空 |
| 11 | §五 | agent profile 没有真实宿主 | **实测：不带 `--fakes` 时返回 `E-RUN-HOST-UNAVAILABLE`（退出 2）**；PH-11 接真实 Agent 能力。PH-11-T7 已让该错误码退役，见 PH-11 卡 §7 #14 |
| 12 | §4.10 | `--fakes` 与真实宿主的退出码不一致 | **实测：`--fakes` 保持 harness 协议退出 0/2/3；只有真实宿主按 `exit_codes` 返回 1**。同一脚本失败时两种模式退出码不同，登记缺口。**PH-11-T7 已收口：`--fakes` 未处理失败退出 1，harness SUT 接受“退出 1 + `{"ok": false}`”，见 PH-11 卡 §7 #12** |
| 13 | §4.5 | 进程 timeout / env 覆盖 / `stat`/`list` | **实测：进程默认 10s timeout，可 `timed_out` 观察；环境变量只继承不覆盖；`stat`/`list` 不映射**，后续 CR |
