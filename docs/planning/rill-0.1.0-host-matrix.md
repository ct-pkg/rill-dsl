# 双宿主能力矩阵（PH-11）

> 规范正文见 `docs/RILL-0.1.0.md`（只读）。本文件只记录两个宿主在
> `HostCapabilities` 五个槽位上的实现形态与差异；缺口编号对应
> `docs/phases/PH-11/card.md` §7，改动前先读那张表。

## 0. 共同点

两个宿主共用同一份语法、同一个 parser、同一套 AST；`rill run --profile shell`
与 `rill run --profile agent` 只在加载期动词集与能力实现上分叉：

- 五个槽位固定为 process / fs / env / stdio / exit，Parser 不 import 任何宿主模块；
- 两个 profile 的 AST 逐节点相等（`tests/phase11/test_agent_fixtures.py` 对每个
  fixture 比对，`testdata/0.1.0/host/shared/read-send/` 是同一份源码）；
- `--fakes` 优先于两个真实宿主，退出码保持 harness 协议（0/2/3）；
- Shell 的能力清单来自 `--host-profile` 的 shell manifest；Agent 的 manifest
  额外声明 `roles` / `types` / `context` / `limits` / `tools`。

两个宿主的差异只允许出现在“能力怎么做”，不允许出现在“脚本怎么写”。

## 1. 进程调用

| 维度 | Shell 宿主 | Agent 宿主 | 差异 |
| --- | --- | --- | --- |
| 调用方式 | `ProcessCapability.run` 直接 spawn/exec，argv 由 `shlex.split` 切分 | `run` / `exec` 工具经 `ToolRegistry` 调用 | Agent 不创建进程，也不切 argv |
| 成功结果 | `value` = stdout；`host_meta.process` 带 argv/code/stdout/stderr | 工具值即 `$`；`host_meta.process.tool` 记录工具名与命令 | Agent 的 ProcessResult 是工具值，不是宿主捕获 |
| 失败结果 | 非零退出、timeout、spawn 失败都转 `ok=false` | 工具返回 `ok=false` + 错误串 | 都没有结构化错误塞进 `$` |
| 副作用 | 真实命令产生真实副作用 | 只改工具注册表状态 | 同一条 `<run>` 在两个宿主下副作用不同 |

`|>` 仍然只是 DSL 值管道，不是 OS 管道。Agent 的 `run` 工具 stdin 只来自
`$`/管道输入（文本），没有 OS stdin。Shell 的进程 timeout 是能力清单/默认 10s；
Agent 的同类约束由 `limits.time_ms` 承担，见 §6。

## 2. 文件与路径

| 维度 | Shell 宿主 | Agent 宿主 | 差异 |
| --- | --- | --- | --- |
| 路径解析 | cwd 相对解析；绝对路径、`..`、符号链接交给 OS | workspace root 相对解析；相对/绝对路径都必须落在 root 内 | Agent 在宿主侧先做路径约束 |
| 读写实现 | 真实 `open`；`read` 返回文本或 `Bytes` | `read` / `write` 工具；宿主不碰 OS 文件 | Agent 的返回值完全由工具决定 |
| 类型槽 | 不拆分 `类型:值` | `file:` 按 `types.file = path` 校验；`net:` 是 text | Agent 有 TypeRegistry，Shell 没有 |
| 越界/失败 | OS 错误转 `E-HOST-FS-*` | 越界 `E-HOST-FS-OUTSIDE`；工具错误按工具串返回 | 越界是工具错误，不是 OS 错误 |

Agent 的 `read`/`write` 只把 workspace 相对路径交给工具，`host_meta.fs` 记录
`tool/path/root/type`；fixture 里真实文件存在也不会被读，证明没有越过工具。

## 3. 环境变量

| 维度 | Shell 宿主 | Agent 宿主 | 差异 |
| --- | --- | --- | --- |
| 来源 | 当前进程 `os.environ` | manifest 的 `context` 对象 | Agent 只看内核注入的上下文 |
| 写入 | 子进程 env 合并/覆盖 | 不支持写 | Agent 没有全局可变环境 |
| 缺失 | `E-HOST-ENV-MISSING` | `E-HOST-ENV-MISSING` | 错误码相同，来源不同 |
| 任意读取 | 允许读当前进程可见的变量 | 只允许 `context` 里声明的键 | `os.environ` 对 Agent 不可见 |

`<env> NAME` 在 Shell 下是新进程快照；在 Agent 下是 manifest 的只读上下文。
fixture `env-context-only` 用真实 OS 变量证明 Agent 读不到未注入的键。

## 4. 标准输入输出

| 维度 | Shell 宿主 | Agent 宿主 | 差异 |
| --- | --- | --- | --- |
| stdin | 真实 stdin 文本/`Bytes`；`run` 工具接收管道值 | `run` 工具的 stdin 来自 `$`/管道文本 | Agent 没有 OS stdin |
| stdout | 进程 stdout 捕获；非法 UTF-8 变 `Bytes` | 工具返回值即段值 | Agent 没有 OS stdout |
| `send` | 写 stderr，`host_meta.stdio.channel = stderr` | 调 `send`/`emit` 工具，`channel = tool` | 同一动词，两个落点 |
| 输出污染 | 与 `run` 的 JSON stdout 协议隔离 | 完全不写 OS fd | Agent 的 `run` 结果不会被 stdio 污染 |

`send` 在 Agent 下优先取 object（主语是角色），`engineer <send> "ok"` 的值是
`"ok"`；`write` 的内容只取管道输入，避免把角色名当文件内容（卡 §7 #10）。

## 5. 退出码

| 维度 | Shell 宿主 | Agent 宿主 | 差异 |
| --- | --- | --- | --- |
| 成功 | `exit_codes.ok`，默认 0 | 0 | 都是 0 |
| 未处理失败 | `exit_codes.unhandled`，默认 1 | 0；payload 仍 `ok=false` | Agent 不产生 OS 退出码（卡 §7 #5） |
| 诊断 | CLI/加载/能力拒绝退出 2 | 角色/加载/manifest 错误退出 2 | 诊断协议不变 |
| `--fakes` | 0/2/3（harness 协议） | 0/2/3（harness 协议） | 假宿主绕过真实退出码 |
| 归属 | 能力清单决定数字 | 固定“脚本完成即 0” | DSL 不写任何数字 |

Agent 的“失败”是可观察的 `{ok: false}`，不是进程退出状态；调用方读 payload，
不要读 shell 的 `$?` 判断脚本成败。

## 6. 角色、类型与 limits（Agent 专属）

| 维度 | Shell 宿主 | Agent 宿主 | 差异 |
| --- | --- | --- | --- |
| principal | OS 用户，无 role | manifest `role` + `roles` 表 | role 不是所有宿主必选（卡 §7 #2） |
| 校验阶段 | 不做角色校验 | parse 之后、exec 之前校验字面量主语 | 未知/越权走 run 诊断 |
| 类型表 | 无 | `types` 映射 `path` / `text` | 只有 Agent 拆分 `类型:值` |
| ExecLimits | 只有进程 timeout | `limits.steps/time_ms/bytes` | Agent 有执行预算（卡 §7 #3） |
| 超限 | 进程 timeout 转 `ok=false` | `E-HOST-LIMIT-*` + `host_meta.limits` | 不截断值，失败关闭 |

`steps` 数工具调用次数，`time_ms` 是墙钟毫秒，`bytes` 是工具结果 JSON 的 UTF-8
字节数；`parallel` 分支数与搜索深度尚未限流，登记为后续 CR。

## 7. fixture 与验收

| 项 | 位置/命令 | 说明 |
| --- | --- | --- |
| 同源源码 | `testdata/0.1.0/host/shared/read-send/source.rill` | Agent 的 `shared-read-send/script.rill` 与它逐字相同 |
| Agent fixture | `testdata/0.1.0/host/agent/` | 14 例：五类能力成功/失败 + role/limits/type |
| canonical manifest | `.../agent/profiles/agent.json` + `tools.json` | 角色、类型、context、limits、工具注册表 |
| 单测 | `python3 tests/phase11/test_agent_fixtures.py` | 逐 fixture 断言 ok/value/error/exit/host_meta + AST 相等 |
| harness | `bash tools/check-0.1.0.sh --bucket host` | 同源 AST 用例仍全绿 |

`run` 能否真实跑脚本要分宿主看：

| 问题 | Shell | Agent |
| --- | --- | --- |
| 能跑 DSL 脚本吗 | 能 | 能 |
| 能读真实文件吗 | 能 | 不能，只调 `read` 工具 |
| 能起真实进程吗 | 能 | 不能，只调 `run`/`exec` 工具 |
| 能读真实环境变量吗 | 能 | 不能，只读 `context` |
| 失败有 OS 退出码吗 | 有（能力清单） | 没有，固定 0 |

## 8. 已知限制

- 不接生产工具、审批、白名单与真实并发调度（本 phase 边界）。
- `limits` 只实现 steps/time/bytes；超限失败关闭，不截断，不实现 parallel 分支数/
  搜索深度。
- Agent 的失败不产生非 0 退出码，只体现在 payload；Shell 的 `--fakes` 与真实宿主
  退出码仍可能不同（PH-10 卡 §8 #12）。
- 动态主语（`$var` 角色）按默认角色处理；类型表只有 `path` / `text` 两种约束。
- PH-10 的 `docs/planning/rill-0.1.0-shell-profile.md` §4 里“Agent 预留”的表述
  以本文件为准；PH-10 卡 §8 #2 的 agent 动词集裁定由 PH-11 卡 §7 #6 取代。

## 9. PH-12 双 profile 验收

本节只记录 PH-12 的验收结果，不重复 §1–§6 的能力形态；缺口裁定见
`docs/phases/PH-12/card.md` §7。

| 判据 | 命令 | 原始结果 |
| --- | --- | --- |
| 同源 AST | `bash tools/check-0.1.0.sh --bucket host` | `PASS host/shared/read-send`；1 passed, 0 failed |
| Agent 五类能力 | `python3 tests/phase11/test_agent_fixtures.py` | `PASS phase11 fixtures: ... AST 一致`（exit 0） |
| round-trip | `bash tools/check-fmt.sh --roundtrip` | `PASS ... 71 个 fixture`（exit 0） |
| 全样例 | `bash tools/check-0.1.0.sh --all` | 85 fixtures；83 compliance + 2 smoke passed；pending 0 |
| 文档一致性 | `python3 tests/phase12/test_host_matrix.py` | `PASS phase12 matrix`（exit 0） |

### 9.1 run 能否真实跑脚本

| 问题 | Shell | Agent |
| --- | --- | --- |
| 能跑 RILL 脚本吗 | 能 | 能 |
| 能否读真实文件 | 能 | 不能，只调 `read` / `write` 工具 |
| 能否起真实进程 | 能 | 不能，只调 `run` / `exec` 工具 |
| 能否读真实环境变量 | 能 | 不能，只读 manifest `context` |
| 未处理失败是否有 OS 退出码 | 有，数字由能力清单给出 | 没有，固定 0，payload 仍 `ok=false` |
| 同源 AST | 相等 | 相等 |

“能跑脚本”只说明脚本被解析并执行；Shell 的副作用是真实的，Agent 的副作用
只发生在工具注册表里。两者能力不等价，不得用一方的结果推断另一方。

### 9.2 host-specific 差异清单

| # | 差异点 | Shell 实际 | Agent 实际 | 是否影响语法/AST |
| --- | --- | --- | --- | --- |
| 1 | `run` / `exec` 落点 | 真实进程 | 工具调用 | 不影响语法/AST |
| 2 | `read` / `write` 落点 | OS 文件 | `read` / `write` 工具 | 不影响语法/AST |
| 3 | `env` 来源 | 当前进程 `os.environ` | manifest `context` | 不影响语法/AST |
| 4 | `send` 通道 | stderr | `send` / `emit` 工具 | 不影响语法/AST |
| 5 | 未处理失败退出码 | 非 0（能力清单） | 0（payload `ok=false`） | 不影响语法/AST |
| 6 | 角色、类型与 limits | 无 role；只有进程 timeout | `roles` / `types` / `limits` | 不影响语法/AST |

结论：六项差异全部落在能力层，parser 与 AST 不感知宿主；同一 fixture 的
AST 在 shell / agent 下逐节点相等。差异没有一条被写进语法或 AST。
