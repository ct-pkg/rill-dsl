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
- 实现说明：`fmt` 依赖 PH-5 未交付的最小 `src/rill/formatter.py`（卡 §7 #1）；
  `--compress` / `--display` 的 AST 等价由 T3 的 round-trip 门禁扩大覆盖。

## PH-12-T2 全样例门禁

- 红提交：`test(cli): PH-12-T2 红`（baseline `b54e50d`）
- 红命令：`python3 tests/phase12/test_all_gate.py`
- 红输出：

```text
Traceback (most recent call last):
  File ".../tests/phase12/test_all_gate.py", line 70, in <module>
    main()
  File ".../tests/phase12/test_all_gate.py", line 63, in main
    case_all_is_green()
  File ".../tests/phase12/test_all_gate.py", line 28, in case_all_is_green
    assert result.returncode == 0, (
AssertionError: ('check-0.1.0.sh --all 退出 2', '', 'usage: check-0.1.0.sh ... error: unrecognized arguments: --all\n')
exit=1
```

- 直接复现：`bash tools/check-0.1.0.sh --all` →
  `check-0.1.0.sh: error: unrecognized arguments: --all`（exit 2）
- 绿提交：`feat(cli): PH-12-T2 全样例门禁`
- 绿命令与输出：`python3 tests/phase12/test_all_gate.py` →
  `PASS phase12 all: --all 全桶绿 + pending 0`（exit 0）；
  `bash tools/check-0.1.0.sh --all` 头部为
  `gate     : all buckets; pending=0, retired=4, problems=无`，
  尾部为 `compliance: 83 passed ... / smoke: 2 passed ... / pending: 0 not run`
  （exit 0）。
- 说明：`retired=4` 是 `pending/` 下 4 个 `retired: true` 的转正痕迹目录，
  harness 不发现、不执行；E-2 以 `pending: 0 not run` 为准（卡 §7 #6）。

## PH-12-T3 round-trip 门禁

- 红提交：`test(fmt): PH-12-T3 红`（baseline `6b3f26b`）
- 红命令：`python3 tests/phase12/test_roundtrip.py`
- 红输出：

```text
Traceback (most recent call last):
  File ".../tests/phase12/test_roundtrip.py", line 88, in <module>
    main()
  File ".../tests/phase12/test_roundtrip.py", line 72, in main
    case_gate_script_exists()
  File ".../tests/phase12/test_roundtrip.py", line 39, in case_gate_script_exists
    assert os.path.isfile(GATE), "缺少 round-trip 门禁：%s" % GATE
AssertionError: 缺少 round-trip 门禁：.../tools/check-fmt.sh
exit=1
```

- 绿提交：`feat(fmt): PH-12-T3 round-trip 门禁`
- 绿命令与输出：`bash tools/check-fmt.sh --roundtrip` →
  `PASS phase12 roundtrip: compress→display→compress AST 等价（71 个 fixture）`
  （exit 0）；同一入口的失败用例由 `assert not failures` 覆盖，
  任一阶段的 AST 不等都会列出前 5 个 `(path, stage)`。
- 说明：71 = 可解析正例（去掉 tokens-only 用例）+ host 脚本；tokens-only
  用例不是合法 program，不纳入 round-trip（卡 §7 #1）。

## PH-12-T4 双 profile 对照

- 红提交：`test(host): PH-12-T4 红`（baseline `9636b84`）
- 红命令：`python3 tests/phase12/test_host_matrix.py`
- 红输出：

```text
Traceback (most recent call last):
  File ".../tests/phase12/test_host_matrix.py", line 76, in <module>
    main()
  File ".../tests/phase12/test_host_matrix.py", line 70, in main
    case_ph12_acceptance_section()
  File ".../tests/phase12/test_host_matrix.py", line 42, in case_ph12_acceptance_section
    assert "## 9. PH-12 双 profile 验收" in doc, "缺少 PH-12 验收章节"
AssertionError: 缺少 PH-12 验收章节
exit=1
```

- 绿提交：`feat(host): PH-12-T4 双 profile 对照`
- 绿命令与输出：`python3 tests/phase12/test_host_matrix.py` →
  `PASS phase12 matrix: 五类能力 + PH-12 验收 + host 桶绿`（exit 0）
- 补充证据：`bash tools/check-0.1.0.sh --bucket host` →
  `PASS host/shared/read-send ...`（1 passed, 0 failed）；
  `python3 tests/phase11/test_agent_fixtures.py` →
  `PASS phase11 fixtures: agent 五类能力 + role/limits/type + AST 一致`

## PH-12-T5 验收报告

- 红提交：`test(acceptance): PH-12-T5 红`（baseline `e6be23e`）
- 红命令：`python3 tests/phase12/test_acceptance_doc.py`
- 红输出：

```text
Traceback (most recent call last):
  File ".../tests/phase12/test_acceptance_doc.py", line 92, in <module>
    main()
  File ".../tests/phase12/test_acceptance_doc.py", line 84, in main
    case_four_lists_exist()
  File ".../tests/phase12/test_acceptance_doc.py", line 39, in case_four_lists_exist
    doc = read_doc()
  File ".../tests/phase12/test_acceptance_doc.py", line 22, in read_doc
    assert os.path.isfile(DOC), "缺少验收报告：%s" % DOC
AssertionError: 缺少验收报告：.../docs/planning/rill-0.1.0-acceptance.md
exit=1
```

- 绿提交：`docs(acceptance): PH-12-T5 验收报告`
- 绿命令与输出：`python3 tests/phase12/test_acceptance_doc.py` →
  `PASS phase12 acceptance: 四类清单 + 真实计数 85/83/pending 0`（exit 0）
- 说明：报告里的计数直接由 `--all --json` 复算，避免手抄漂移。
