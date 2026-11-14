# PH-10 红证与转绿记录

> 基线：`0244597`（复核卡）。逐任务先写测试、跑红，再实现、跑绿。
> 规范缺口见 `docs/phases/PH-10/card.md` §8；实现说明见
> `docs/planning/rill-0.1.0-shell-profile.md`。

## PH-10-T1 进程能力

- 红提交：`test(host): PH-10-T1 红`（baseline `0244597`）
- 红命令：`python3 tests/phase10/test_process.py`
- 红输出：

```text
Traceback (most recent call last):
  File ".../tests/phase10/test_process.py", line 15, in <module>
    from rill.host.shell import (
ModuleNotFoundError: No module named 'rill.host'
exit=1
```

- 绿提交：`feat(host): PH-10-T1 进程能力`
- 绿命令与输出：`python3 tests/phase10/test_process.py` →
  `PASS phase10 process: 成功/非零/stdin 文本与二进制/timeout/拒绝`（exit 0）

## PH-10-T2 文件与环境

- 红提交：`test(host): PH-10-T2 红`（baseline `566854d`）
- 红输出：

```text
ImportError: cannot import name 'EnvCapability' from 'rill.host.shell'
exit=1
```

- 绿提交：`feat(host): PH-10-T2 文件与环境`
- 绿命令与输出：`python3 tests/phase10/test_fs_env.py` →
  `PASS phase10 fs/env: 读/写/拒绝/env 命中与缺失`（exit 0）

## PH-10-T3 宿主接线

- 红提交：`test(host): PH-10-T3 红`（baseline `a717e36`）
- 红输出：

```text
ImportError: cannot import name 'ShellHost' from 'rill.host.shell'
exit=1
```

- 绿提交：`feat(host): PH-10-T3 宿主接线`
- 绿命令与输出：`python3 tests/phase10/test_wiring.py` →
  `PASS phase10 wiring: 映射边界/真实宿主/fakes 优先/未映射动词`（exit 0）
- 红后修正：红提交里的 fake write 用例写成 `<write> out.txt "x"`，解析期就报
  `E-PARSE-UNEXPECTED`（该路径在红阶段未执行到）；绿提交改成
  `<read> in.txt |> <write> out.txt`，红证仍以 ImportError 为准。

## PH-10-T4 stdio 与退出码

- 红提交：`test(host): PH-10-T4 红`（baseline `8b658aa`）
- 红输出：

```text
ImportError: cannot import name 'ExitCapability' from 'rill.host.shell'
exit=1
```

- 绿提交：`feat(host): PH-10-T4 stdio 与退出码`
- 绿命令与输出：`python3 tests/phase10/test_stdio_exit.py` →
  `PASS phase10 stdio/exit: send→stderr、退出码表、fakes 协议、Bytes 输出`（exit 0）
- 红后修正（语义）：能力拒绝从 `ok=false` 改为 run 诊断。原因是 §4.10 的隐式
  `[error]` 会把失败错误串改写成 `RILL DSL ERROR`，`ok=false` 到顶层已丢失
  `slot.operation`；只有诊断能保住“缺哪个能力”。T3 的 denial 用例随之改为断言
  `CapabilityDenied`；`eval_simple` 的 `$` 语义未改。

## PH-10-T5 fixture 与说明

- 红提交：`test(host): PH-10-T5 红`（baseline `d09fd20`）
- 红输出：

```text
FileNotFoundError: [Errno 2] No such file or directory:
  '.../testdata/0.1.0/host/shell'
exit=1
```

- 绿提交：`feat(host): PH-10-T5 fixture 与说明`
- 绿命令与输出：`python3 tests/phase10/test_host_fixtures.py` →
  `PASS phase10 fixtures: 12 例五类能力 + AST 一致 + e2e 真脚本`（exit 0）
- 红后修正：E-2 要求 `ProcessResult.code` 可观察，但 `_apply_tail` 与
  `eval_program` 收口时丢弃了 `host_meta`；绿提交让它穿过段尾与程序收口，
  `$` 仍只投影 value/错误串。

## 全量

- `bash tools/check-0.1.0.sh` → compliance `83 passed, 0 failed, 0 blocked`；
  smoke `2 passed`；`VERDICT: PASS (exit 0)`。
- `tests/phase3..phase10` 的 25 个测试脚本全部 exit 0。
- E-5：`git diff --quiet d686ca3 -- src/rill/lexer.py src/rill/parser.py` → exit 0。
