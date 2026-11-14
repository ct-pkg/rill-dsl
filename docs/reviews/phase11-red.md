# PH-11 红证与转绿记录

> 基线：`87c63c2`（复核卡）。逐任务先写测试、跑红，再实现、跑绿。
> 规范缺口见 `docs/phases/PH-11/card.md` §7；实现说明见
> `docs/planning/rill-0.1.0-host-matrix.md`。

## PH-11-T1 工具能力适配

- 红提交：`test(host): PH-11-T1 红`（baseline `87c63c2`）
- 红命令：`python3 tests/phase11/test_tools_process_stdio.py`
- 红输出：

```text
Traceback (most recent call last):
  File ".../tests/phase11/test_tools_process_stdio.py", line 27, in <module>
    from rill.host.agent import (
ModuleNotFoundError: No module named 'rill.host.agent'
exit=1
```

- 同步红命令：`python3 tests/phase10/test_wiring.py`
- 同步红输出（agent 动词集仍是 PH-10 的旧裁定）：

```text
Traceback (most recent call last):
  ...
  File ".../tests/phase10/test_wiring.py", line 233, in case_shell_verbs_are_profile_scoped
    tables = loader.check_program(parse_source('<run> "echo hi"\n'), profile)
  File ".../src/rill/loader.py", line 189, in _check_nodes
    raise LoadError(
rill.errors.LoadError: 未知动词 'run'；0.1.0 动词集见 PH-4 卡 §8
exit=1
```

- 绿提交：`feat(host): PH-11-T1 工具能力适配`
- 绿命令与输出：`python3 tests/phase11/test_tools_process_stdio.py` →
  `PASS phase11 tools: run/exec→工具、send→工具、工具错误只进字符串`（exit 0）；
  `python3 tests/phase10/test_wiring.py` →
  `PASS phase10 wiring: 映射边界/真实宿主/fakes 优先/未映射动词`（exit 0）
- 红后修正（行为取代）：PH-10 的 `case_agent_without_host_is_diagnostic` 断言
  agent 无宿主；PH-11 起 agent 有真实宿主，改为断言 `ok=false` 且
  `host_meta.tool_meta.tool.code = E-HOST-TOOL-UNREGISTERED`。红阶段该用例
  仍因旧实现通过，未进入红证；这是 PH-10 缺口 11 的正式接管。
- 红后修正（断言）：顶层未处理失败按 §4.10 统一成 `RILL DSL ERROR`，
  工具错误串不会出现在 payload.error；红阶段的两条 CLI 断言改为读
  `host_meta`，工具错误串本身仍由 `test_tool_failure_is_string` 直接断言。
  该断言修正单独提交为 `test(host): PH-11-T1 红后断言修正`，不改变实现。

## PH-11-T2 工具文件与环境

- 红提交：`test(host): PH-11-T2 红`（baseline `30b0fa0`）
- 红命令：`python3 tests/phase11/test_fs_env.py`
- 红输出：

```text
Traceback (most recent call last):
  File ".../tests/phase11/test_fs_env.py", line 23, in <module>
    from rill.host.agent import (
ImportError: cannot import name 'AgentEnvCapability' from 'rill.host.agent'
exit=1
```

- 绿提交：`feat(host): PH-11-T2 工具文件与环境`
- 绿命令与输出：`python3 tests/phase11/test_fs_env.py` →
  `PASS phase11 fs/env: workspace 约束、类型表、context-only env`（exit 0）

## PH-11-T3 角色与 limits

- 红提交：`test(host): PH-11-T3 红`（baseline `47d6f3f`）
- 红命令：`python3 tests/phase11/test_role_limits.py`
- 红输出：

```text
Traceback (most recent call last):
  File ".../tests/phase11/test_role_limits.py", line 23, in <module>
    from rill.host.agent import (
ImportError: cannot import name 'AgentRoleError' from 'rill.host.agent'
exit=1
```

- 绿提交：`feat(host): PH-11-T3 角色与 limits`
- 绿命令与输出：`python3 tests/phase11/test_role_limits.py` →
  `PASS phase11 role/limits: 角色诊断、steps/time/bytes 超限`（exit 0）
- 红后修正：time 用例的假时钟初值从 `[0, 0, 0.001, 0.02]` 改为
  `[0, 0, 0.02]`。实现按“每次调用前检查墙钟”计时，原来的第三个数
  只到 1ms，不足以越过 10ms 上限；用 20ms 让第三次调用稳定变红。
  红证仍以 ImportError 为准。

## PH-11-T4 Agent fixture

- 红提交：`test(host): PH-11-T4 红`（baseline `b9d5424`）
- 红命令：`python3 tests/phase11/test_agent_fixtures.py`
- 红输出：

```text
Traceback (most recent call last):
  File ".../tests/phase11/test_agent_fixtures.py", line 37, in fixture_dirs
    assert os.path.isdir(HOST_ROOT), "缺少 agent fixture 目录：%s" % HOST_ROOT
AssertionError: 缺少 agent fixture 目录：.../testdata/0.1.0/host/agent
exit=1
```

- 绿提交：`feat(host): PH-11-T4 Agent fixture`
- 绿命令与输出：`python3 tests/phase11/test_agent_fixtures.py` →
  `PASS phase11 fixtures: agent 五类能力 + role/limits/type + AST 一致`（exit 0）
- 红后修正（语义）：fixture 首次跑绿时暴露两处槽位取法，
  `engineer <send> "ok"` 把主语当成了消息；按 PH-11 卡 §7 #10 改为
  object 优先。`process-tool-fail` 的 `[error]` 块收口按 PH-7 规则
  回退到失败段的 `host_meta`，所以断言改为 `process.tool` 而不是
  `stdio.tool`。红证仍以 fixture 目录缺失为准。

## PH-11-T5 能力矩阵

- 红提交：`test(host): PH-11-T5 红`（baseline `7fd5357`）
- 红命令：`python3 tests/phase11/test_matrix_doc.py`
- 红输出：

```text
Traceback (most recent call last):
  File ".../tests/phase11/test_matrix_doc.py", line 20, in read_doc
    assert os.path.isfile(DOC), "缺少能力矩阵：%s" % DOC
AssertionError: 缺少能力矩阵：.../docs/planning/rill-0.1.0-host-matrix.md
exit=1
```

- 绿提交：`docs(host): PH-11-T5 能力矩阵`
- 绿命令与输出：`python3 tests/phase11/test_matrix_doc.py` →
  `PASS phase11 matrix: 五类能力 Shell/Agent 两列 + 文字差异`（exit 0）

## PH-11-T6 工具真实传输（复核补记）

- 红提交：`test(host): PH-11-T6 红`（baseline `a5deb4e`）
- 红命令：`python3 tests/phase11/test_tool_transport.py`
- 红输出：

```text
Traceback (most recent call last):
  ...
TypeError: __init__() got an unexpected keyword argument 'cwd'
exit=1
```

- 绿提交：`feat(host): PH-11-T6 工具真实传输`
- 绿命令与输出：`python3 tests/phase11/test_tool_transport.py` →
  `PASS phase11 transport: command 工具走真实子进程、pid/日志可观察`（exit 0）
- 覆盖：`command` 工具由宿主 spawn；请求/响应走 JSON stdin/stdout；
  `host_meta.transport.pid` 与工具侧 `RILL_TOOL_LOG` 的 pid 相等且不等于
  CLI 进程；canonical `profiles/tools.json` 的 `read` 读到真实 `config.txt`。

## PH-11-T7 宿主契约收口（复核补记）

- 红提交：`test(host): PH-11-T7 红`（baseline `a5506df`）
- 红命令：`python3 tests/phase11/test_host_contract.py`
- 红输出：

```text
AssertionError: (0, '{"ok": false, "value": null, "error": "RILL DSL ERROR", "host_meta": {}}\n', '')
exit=1
```

- 绿提交：`feat(host): PH-11-T7 宿主契约收口`
- 绿命令与输出：`python3 tests/phase11/test_host_contract.py` →
  `PASS phase11 contract: fakes 退出码、错误码退役、host 身份、共享核心`（exit 0）
- 覆盖：`--fakes` 未处理失败退出 1；harness 接受“退出 1 + `{"ok": false}`”；
  `src/` 不再出现 `E-RUN-HOST-UNAVAILABLE`；`payload.host.profile/principal`
  可观察；parser/lexer/loader 不 import 宿主；CLI 只有一处 `Interpreter(`；
  独立 `[ok]` / `[error]` 的报错提示改用尾随块。

## PH-11-T8 能力矩阵与陈账（复核补记）

- 红提交：`test(host): PH-11-T8 红`（baseline `f2876d4`）
- 红命令：`python3 tests/phase11/test_matrix_doc.py`
- 红输出：

```text
AssertionError: 矩阵缺少真实传输说明 'command 工具'
exit=1
```

- 绿提交：`docs(host): PH-11-T8 能力矩阵与陈账`
- 绿命令与输出：`python3 tests/phase11/test_matrix_doc.py` →
  `PASS phase11 matrix: 五类能力 Shell/Agent 两列 + 文字差异 + 传输/陈账`（exit 0）
- 附带修正：`phase12-red.md` 在 PH-12 收口时增至 433 行，文档门禁基线从
  20 变为 21；`test_known_limits_doc.py` 与 known-limits 同步为 21，
  不删除证据。

