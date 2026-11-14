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
