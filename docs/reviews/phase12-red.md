# PH-12 红证与转绿记录

> 基线：`4d7b213`（复核卡）。逐任务先写测试、跑红，再实现、跑绿。
> 规范缺口见 `docs/phases/PH-12/card.md` §7；实现说明见
> `docs/planning/rill-0.1.0-acceptance.md` 与
> `docs/planning/rill-0.1.0-known-limits.md`。

## PH-12-T1 CLI 统一

- 红提交：`test(cli): PH-12-T1 红`（baseline `4d7b213`）
- 红命令：`python3 tests/phase12/test_cli_contract.py`
- 红输出：

```text
Traceback (most recent call last):
  File ".../tests/phase12/test_cli_contract.py", line 90, in <module>
    main()
  File ".../tests/phase12/test_cli_contract.py", line 82, in main
    case_help_lists_four_commands()
  File ".../tests/phase12/test_cli_contract.py", line 22, in case_help_lists_four_commands
    assert command in result.stdout, "帮助缺少子命令 %r：%r" % (
AssertionError: 帮助缺少子命令 'fmt'：'usage: rill tokenize <file> | rill parse --dump-ast <file> ...'
exit=1
```

- 绿提交：`feat(cli): PH-12-T1 CLI 统一`
- 绿命令与输出：`python3 tests/phase12/test_cli_contract.py` →
  `PASS phase12 cli: 四子命令/退出码分层/fmt 回读`（exit 0）
