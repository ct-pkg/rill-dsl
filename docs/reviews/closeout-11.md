# PH-11 收口对照表

> 基线 `87c63c2`；复核补记 `a5deb4e`；真实传输与陈账见 §8。只本地提交，
> 不 push、不打 tag。红证见 `docs/reviews/phase11-red.md`，能力矩阵见
> `docs/planning/rill-0.1.0-host-matrix.md`。

## 1. 判定

**GO。** 两个宿主共用同一份语法/parser/AST/Interpreter；Agent 的 canonical
工具是真实子进程；`--fakes` 失败退出码与真实 Shell 宿主一致；占位错误码
`E-RUN-HOST-UNAVAILABLE` 已退役。

## 2. 退出判据

| ID | 条件 | 原始证据 | 结果 |
| --- | --- | --- | --- |
| E-1 | Agent 跑完同源 fixture，AST 相等 | `python3 tests/phase11/test_agent_fixtures.py` → `PASS ... AST 一致`（exit 0） | PASS |
| E-2 | 能力矩阵五类两列 + 差异 | `python3 tests/phase11/test_matrix_doc.py` → `PASS ... 传输/陈账`（exit 0） | PASS |
| E-3 | `[error]` 仍只拿字符串 | `python3 tests/phase11/test_tools_process_stdio.py` → `PASS ... 工具错误只进字符串`（exit 0） | PASS |
| E-4 | 没有 parser/lexer 改动 | `git diff --quiet 84cf917 -- src/rill/lexer.py src/rill/parser.py` → exit 0 | PASS |
| E-5 | 每项可独立验收 | T6–T8 的 verify 原始输出见 §3 | PASS |
| E-8 | 工具调用真的走出进程 | `python3 tests/phase11/test_tool_transport.py` → `PASS ... pid/日志可观察`；真实脚本见 §4 | PASS |
| E-9 | fakes 退出码一致；错误码退役 | `python3 tests/phase11/test_host_contract.py` → `PASS ... fakes 退出码、错误码退役`（exit 0） | PASS |
| E-10 | 共用核心；调用方可识别能力体系 | AST 双 profile sha256 相同；`payload.host.profile/principal` 见 §4 | PASS |

## 3. 复核补记任务

| 任务 | verify | 原始输出 | 退出码 | 红 / 实现提交 |
| --- | --- | --- | --- | --- |
| PH-11-T6 | `python3 tests/phase11/test_tool_transport.py` | `PASS phase11 transport: command 工具走真实子进程、pid/日志可观察` | 0 | `29a29b0` / `a5506df` |
| PH-11-T7 | `python3 tests/phase11/test_host_contract.py` | `PASS phase11 contract: fakes 退出码、错误码退役、host 身份、共享核心` | 0 | `5ca83c5` / `f2876d4` |
| PH-11-T8 | `python3 tests/phase11/test_matrix_doc.py` | `PASS phase11 matrix: 五类能力 Shell/Agent 两列 + 文字差异 + 传输/陈账` | 0 | `3801286` / `258b95b` |

## 4. 真实脚本证据

命令（cwd = `testdata/0.1.0/host/agent`）：

```console
$ PYTHONPATH=<repo>/src RILL_TOOL_LOG=/tmp/rill-agent-calls.log \
    python3 -m rill run real-transport.rill --profile agent \
    --host-profile profiles/agent.json
{"ok": true, "value": "region=cn\n", "error": null,
 "host_meta": {"stdio": {"tool": "send", "channel": "tool", "text": "region=cn\n"},
               "tool_meta": {"transport": {"kind": "process", "tool": "send",
                                           "pid": 52738,
                                           "argv": ["python3", "tools/tool_server.py"],
                                           "code": 0}}},
 "host": {"profile": "agent", "principal": {"kind": "role", "name": "engineer"}}}
EXIT=0
```

工具侧日志（每次调用是独立进程）：

```text
{"args": {"path": "config.txt"}, "pid": 52737, "tool": "read"}
{"args": {"text": "region=cn\n"}, "pid": 52738, "tool": "send"}
```

AST 双 profile（同一份 `real-transport.rill`）：

```text
shell: ef2d0db2cba190b64ba39050c1e88f320e7670b9f2652cc26b0f10f1db38d809
agent: ef2d0db2cba190b64ba39050c1e88f320e7670b9f2652cc26b0f10f1db38d809
```

## 5. 四条硬要求的结论

| 要求 | 结论 |
| --- | --- |
| Agent 不能只靠 `--fakes` 冒充 | canonical manifest 的四个工具都是 `command` 工具；真实脚本的 read/send 各自跑在独立 pid；单测 fixture 的 `queue` 桩只证明映射，不冒充“能用” |
| 两宿主共用语法与执行核心 | parser/lexer/loader 不 import 宿主；CLI 只有一处 `Interpreter(`；AST 逐节点相等；五个槽位两宿主同签名 |
| 能力清单与 principal | 同一套 `HostCapabilities` 槽位；ShellPolicy 是 operation grant，AgentPolicy 的 role 是 principal；调用方读 `payload.host.profile/principal` |
| `E-RUN-HOST-UNAVAILABLE` | 已退役；`src/` 不再出现；缺/坏 manifest 报 `E-RUN-HOST-PROFILE`（退出 2） |

## 6. 陈账

| 陈账 | 处理 |
| --- | --- |
| `--fakes` 失败退出 0（缺口 #12） | 收掉：未处理失败退出 1；harness SUT 接受“退出 1 + `{"ok": false}`” |
| 独立 `[ok] $x {}` / `[error] $x {}` | 本版仍不支持；报 `E-RUN-UNSUPPORTED` 并提示改用尾随块；不阻塞 Agent 脚本 |

## 7. 仍不可用的能力

- Agent 读真实 OS 环境变量：不可用，只读 manifest `context`。
- 生产工具网关、审批、白名单、密钥注入：不接。
- Agent 未处理失败的 OS 退出码：固定 0，调用方读 `payload.ok`。
- `parallel` 分支数/搜索深度限流：未实现。
- 独立 `[ok]` / `[error]` 形式语句：未实现，用尾随块绕开。
- 远端工具传输：不提供；`command` 工具是本机子进程。

## 8. 全量计数

```text
harness --all : compliance 83 passed / 0 failed / 0 blocked / 0 draft
                smoke 2 passed / 0 failed；pending 0；exit 0
phase tests   : tests/phase3..phase12 全部 PASS
doc gate      : 21 FAIL（DOC-S2 9 + 断链 9 + 未定义版本 3；均为既有基线，
                其中 docs/reviews/phase12-red.md 收口补证后计入 DOC-S2）
```
