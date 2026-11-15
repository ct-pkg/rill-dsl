# PH-19 立项卡：CT Shell 宿主（P7）

> 状态：正常开卡。CT 重写轨道第 7 层。体系见 `docs/phases/README.md`，
> 上游 `docs/planning/rill-0.1.0-ct-rewrite-roadmap.md`。语言规范 `docs/RILL-0.1.0.md`（0.1.1，只读）。
> **CT 缺陷命中点**：PH-51（指针接收者 `.` 调用传 `S**`）——宿主接口必须用函数指针表，见 §1 与 §5。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-19`，目录 `docs/phases/PH-19/` |
| 目标 | CT 版在 Shell profile 上跑通进程/文件/env/stdio/退出码五类能力，12 个 Shell fixture 全绿。 |
| 范围 | 做什么：宿主能力接口（函数指针表）、Shell 五类实现、退出码映射、12 个 fixture、host 层对拍。不做什么：语法/parser 改动、真实权限、Windows、流式/PTY。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | PH-16 的 `Value`/`ExecOutcome`；PH-17 的控制流；PH-15 的 profile 表；`testdata/0.1.0/host/`。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `19`（目标产品版本 `0.19.0`）。 |
| 已知风险 | PH-51 命中接口调用；`\|>` 与 OS 管道混淆；退出码/stderr 塞进 `$`；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| `HostCapabilities` 用**函数指针表**，不用指针接收者 trait | 不用 `.` 方法链派发能力 |
| 进程：argv/cwd/env/timeout、捕获 stdout/stderr、`ProcessResult` | 不把 OS 管道写进 DSL 语法 |
| 文件/路径、env、stdin 文本与 `Bytes`、退出码映射 | 不做 Windows、信号、PTY、流式 |
| 12 个 Shell fixture + host 层对拍 | 不改 parser/lexer、不改 golden |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `ct/src/host/host.h.ct` | 能力槽位与函数指针表（本 phase 首次建立） |
| `ct/src/host/shell.h.ct` | Shell 能力声明 |
| `ct/src/host/shell.m.ct` | 进程/文件/env/stdio/退出码实现 |
| `docs/planning/rill-0.1.0-ct-defect-workarounds.md` | 追加 PH-51 绕法、实测与代价（PH-15 建立，本卡扩展） |
| `docs/reviews/diff/PH-19.md` | 本阶段差异报告 |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-19-T1 | `ct/src/host/host.h.ct`（函数指针表） | `feat(ct): PH-19-T1 宿主能力接口` | `git revert <sha>` | `test -s ct/src/host/host.h.ct` | M | E-6 |
| PH-19-T2 | `ct/src/host/shell.m.ct`（进程） | `feat(ct): PH-19-T2 Shell 进程能力` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --show host/shared/read-send` | M | E-1,E-2 |
| PH-19-T3 | `ct/src/host/shell.m.ct`（文件/env） | `feat(ct): PH-19-T3 Shell 文件与环境` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --bucket host` | M | E-1 |
| PH-19-T4 | `ct/src/host/shell.m.ct`（stdio/退出码） | `feat(ct): PH-19-T4 stdio 与退出码` | `git revert <sha>` | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --check-fakes` | M | E-1,E-3 |
| PH-19-T5 | `docs/reviews/diff/PH-19.md` 与 workarounds 追加 | `docs(diff): PH-19-T5 host 差异报告` | `git revert <sha>` | `python3 tools/diff/diff.py --layer host --profile shell` | S | E-4,E-5,E-7 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | 12 个 Shell fixture 全部通过 | `--bucket host` 的 shell 子集退出 0 |
| E-2 | `ProcessResult.code/stdout/stderr` 可观察；stdin 文本与二进制各 1 例 | 字段断言 |
| E-3 | 顶层未处理失败非 0 退出；`[error]` 后按 profile 策略 | 退出码逐例断言 |
| E-4 | 同一 fixture 在 shell/agent 的 AST 相等 | `--bucket host` AST 比对 |
| E-5 | 没有 parser/lexer 改动 | `git diff --quiet v0.14.0 -- ct/src/lexer ct/src/parser` 退出 0 |
| E-6 | 能力派发只用函数指针表；无指针接收者方法链 | `test -z "$(grep -nE '\.get\(\)\.get\(' ct/src/host/*.ct)"` |
| E-7 | 任务清单每项可独立验收（T-6） | 收口对照表逐项贴 `verify` 原始输出 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | PH-16 的 `Value::Bytes/Opaque` 与 `ExecOutcome.host_meta`；PH-17 的执行顺序；PH-15 的 profile 表；24 个 host fixture 中的 12 个 Shell 例。 |
| 风险 1 | **PH-51**：指针接收者 `.` 调用发射 `S_f(&p)`（传 `S**`），vtable 点静默错值。绕法：能力槽位用函数指针表/自由函数，`Value` 方法用值接收者或显式 `(*p)`，禁止 `.get().get()`（`ct-lang/docs/reviews/2026-11-15-deepseek-ct-proposal-review.md` 有实测）。代价：手写派发约 +100–200 行，失去方法链语法。 |
| 风险 2 | `\|>` 被当 OS 管道：DSL 管道只传 value。触发信号：文档/错误提示混写。 |
| 风险 3 | 退出码/stderr 塞进 `[error]` 的 `$`：`$` 只能是错误串。触发信号：`$` 出现结构化结果。 |
| 风险 4 | 二进制 stdin 被转文本：PH-16 的 `Bytes` 必须已就位。触发信号：E-2 二进制例失败。 |

## 6. 收口与 tag

- 收口附 `docs/reviews/diff/PH-19.md` 与 `docs/reviews/closeout-19.md`。
- 版本 `0.19.0`；tag 按 `docs/phases/README.md` §4，本卡不自动打 tag、不 push。
- 收口后 PH-20 可全速推进；PH-21 等待 PH-20。
