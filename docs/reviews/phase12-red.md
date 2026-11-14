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

## PH-12-T6 已知限制

- 红提交：`test(acceptance): PH-12-T6 红`（baseline `1c34c21`）
- 红命令：`python3 tests/phase12/test_known_limits_doc.py`
- 红输出：

```text
Traceback (most recent call last):
  File ".../tests/phase12/test_known_limits_doc.py", line 81, in <module>
    main()
  File ".../tests/phase12/test_known_limits_doc.py", line 74, in main
    case_sections_exist()
  File ".../tests/phase12/test_known_limits_doc.py", line 27, in case_sections_exist
    doc = read_doc()
  File ".../tests/phase12/test_known_limits_doc.py", line 21, in read_doc
    assert os.path.isfile(DOC), "缺少已知限制：%s" % DOC
AssertionError: 缺少已知限制：.../docs/planning/rill-0.1.0-known-limits.md
exit=1
```

- 绿提交：`docs(acceptance): PH-12-T6 已知限制`
- 绿命令与输出：`python3 tests/phase12/test_known_limits_doc.py` →
  `PASS phase12 limits: 生产/并发/pending/formatter/基线 20 FAIL`（exit 0）
- 说明：基线 FAIL 数由测试现场复跑 `tools/check.sh all` 并计数，
  与文档中的 20 对齐；分类见 `rill-0.1.0-known-limits.md` §5。

## 阶段收口：§4 退出判据实测（E-1..E-7）

> 执行日期 `2026-11-15`；基线 `HEAD = 8b1cb74`，工作树干净。以下命令均为
> 收口时现场执行，退出码与输出照录；上文历史红证不重写、不补造。

### E-1 全部正例通过；负例全部按预期错误码失败

```console
$ bash tools/check-0.1.0.sh --all
RILL 0.1.0 harness
root     : testdata/0.1.0
sut      : python3 -m rill
gate     : all buckets; pending=0, retired=4, problems=无
sut(smoke): python3 tools/rill_stub/rill.py
profiles : agent, shell
fixtures : 85 (positive 56, negative 26, host 1, smoke 2)

PASS    host/shared/read-send (host-ast-equal)  AST 在 shell / agent 下相等
PASS    negative/load/fn-arity-too-few (error)  load E-LOAD-FN-ARITY@6:1
PASS    negative/load/fn-arity-too-many (error)  load E-LOAD-FN-ARITY@6:1
PASS    negative/load/fn-default-not-tail (error)  load E-LOAD-FN-DEFAULT-NOT-TAIL@2:1
PASS    negative/load/fn-name-case (error)  load E-LOAD-FN-UNDECLARED@6:1
PASS    negative/load/map-duplicate-short (error)  load E-LOAD-MAP-DUP-SHORT@3:1
PASS    negative/load/unknown-function (error)  load E-LOAD-FN-UNDECLARED@1:1
PASS    negative/load/unknown-verb (error)  load E-LOAD-VERB-UNKNOWN@1:1
PASS    negative/parse/break-verb-value (error)  parse E-PARSE-BREAK-VALUE@1:7
PASS    negative/parse/duplicate-error (error)  parse E-PARSE-DUP-ERROR@1:47
PASS    negative/parse/duplicate-ok (error)  parse E-PARSE-DUP-OK@1:44
PASS    negative/parse/fn-def-in-body (error)  parse E-PARSE-FN-DEF-BODY@1:1
PASS    negative/parse/missing-block (error)  parse E-PARSE-MISSING-BLOCK@1:30
PASS    negative/parse/results-as-prep (error)  parse E-PARSE-RESULTS-CONTEXT@1:14
PASS    negative/parse/results-in-branch (error)  parse E-PARSE-RESULTS-CONTEXT@2:18
PASS    negative/parse/results-in-simple (error)  parse E-PARSE-RESULTS-CONTEXT@1:14
PASS    negative/parse/results-outside-parallel (error)  parse E-PARSE-RESULTS-CONTEXT@1:14
PASS    negative/parse/unknown-prep (error)  parse E-PARSE-UNKNOWN-PREP@1:15
PASS    negative/tokenize/bad-escape-bare (error)  tokenize E-LEX-BARE-ESCAPE@1:9
PASS    negative/tokenize/bad-escape-string (error)  tokenize E-LEX-ESCAPE@1:10
PASS    negative/tokenize/map-bad-marker (error)  tokenize E-01@2:4
PASS    negative/tokenize/map-missing-short (error)  tokenize E-LEX-MAP-ENTRY@2:1
PASS    negative/tokenize/map-space-before-marker (error)  tokenize E-01@2:4
PASS    negative/tokenize/map-unclosed (error)  tokenize E-LEX-MAP-UNCLOSED@1:1
PASS    negative/tokenize/unclosed-map-ref (error)  tokenize E-LEX-MAP-REF@1:8
PASS    negative/tokenize/unclosed-quote (error)  tokenize E-LEX-QUOTE@1:8
PASS    negative/tokenize/unclosed-verb (error)  tokenize E-02@1:1
PASS    positive/block/into-independent (ast)  ast 与 golden 一致
PASS    positive/block/trailing (ast)  ast 与 golden 一致
PASS    positive/break/bareword-value (ast)  ast 与 golden 一致
PASS    positive/break/capture (ast)  ast 与 golden 一致
PASS    positive/call/bareword-arg (ast)  ast 与 golden 一致
PASS    positive/call/basic (ast)  ast 与 golden 一致
PASS    positive/check/each-bareword-w01 (warning)  W-01 已提示，check 退出 0
PASS    positive/check/host-profiles (check)  check 通过（shell / agent）
PASS    positive/comments/not-header (ast)  ast 与 golden 一致
PASS    positive/each/bareword-value (ast)  ast 与 golden 一致
PASS    positive/each/ok-error (ast)  ast 与 golden 一致
PASS    positive/if/else-if (ast)  ast 与 golden 一致
PASS    positive/map/header (ast)  ast 与 golden 一致
PASS    positive/map/space-header (ast)  ast 与 golden 一致
PASS    positive/map/verb-marker (ast)  ast 与 golden 一致
PASS    positive/parallel/results (ast)  ast 与 golden 一致
PASS    positive/pipe/multi-line (ast)  ast 与 golden 一致
PASS    positive/prep/ok-as-prep (ast)  ast 与 golden 一致
PASS    positive/quotes/escapes (ast)  ast 与 golden 一致
PASS    positive/run/call/defaults (run)  运行结果与声明一致
PASS    positive/run/call/return-last (run)  运行结果与声明一致
PASS    positive/run/control/break-pipe (run)  运行结果与声明一致
PASS    positive/run/control/each-level-error (run)  运行结果与声明一致
PASS    positive/run/control/each-round-failure (run)  运行结果与声明一致
PASS    positive/run/control/each-value (run)  运行结果与声明一致
PASS    positive/run/control/if-subject (run)  运行结果与声明一致
PASS    positive/run/control/pipe-segment-error (run)  运行结果与声明一致
PASS    positive/run/control/pipe-three (run)  运行结果与声明一致
PASS    positive/run/into/failure-error (run)  运行结果与声明一致
PASS    positive/run/into/order (run)  运行结果与声明一致
PASS    positive/run/parallel/results-array (run)  运行结果与声明一致
PASS    positive/run/parallel/three-state (run)  运行结果与声明一致
PASS    positive/run/pipe/downstream (run)  运行结果与声明一致
PASS    positive/run/pipe/failure-stops (run)  运行结果与声明一致
PASS    positive/run/segment/failure-error (run)  运行结果与声明一致
PASS    positive/run/segment/failure-plain (run)  运行结果与声明一致
PASS    positive/run/segment/success-ok (run)  运行结果与声明一致
PASS    positive/run/segment/success-plain (run)  运行结果与声明一致
PASS    positive/simple/adverb (ast)  ast 与 golden 一致
PASS    positive/simple/assign (ast)  ast 与 golden 一致
PASS    positive/simple/prep-phrases (ast)  ast 与 golden 一致
PASS    positive/simple/read-write (ast)  ast 与 golden 一致
PASS    positive/simple/subject-var (ast)  ast 与 golden 一致
PASS    positive/tokens/comments-and-headers (tokens)  tokens 与 golden 一致
PASS    positive/tokens/compact (tokens)  tokens 与 golden 一致
PASS    positive/tokens/fields (tokens)  tokens 与 golden 一致
PASS    positive/tokens/keywords-values (tokens)  tokens 与 golden 一致
PASS    positive/tokens/map-entries (tokens)  tokens 与 golden 一致
PASS    positive/tokens/map-refs (tokens)  tokens 与 golden 一致
PASS    positive/tokens/map-verb-marker (tokens)  tokens 与 golden 一致
PASS    positive/tokens/numbers (tokens)  tokens 与 golden 一致
PASS    positive/tokens/punctuation (tokens)  tokens 与 golden 一致
PASS    positive/tokens/quotes (tokens)  tokens 与 golden 一致
PASS    positive/tokens/space-header (tokens)  tokens 与 golden 一致
PASS    positive/tokens/strings-and-escapes (tokens)  tokens 与 golden 一致
PASS    positive/value/five-branches (ast)  ast 与 golden 一致
PASS    smoke/dual-profile (host-ast-equal)  AST 在 shell / agent 下相等
PASS    smoke/echo-ast (ast)  ast 与 golden 一致

summary
  compliance: 83 passed, 0 failed, 0 blocked, 0 draft
  smoke:     2 passed, 0 failed, 0 blocked, 0 draft
  pending:   0 not run (A 0, B 0)
VERDICT: PASS (exit 0)
EXIT=0
```

判读：`positive` 56 例全部 PASS（ast 23 / tokens 12 / run 19 / check 1 /
warning 1）；`negative` 26 例全部 PASS，且每条都带声明中的 stage 与错误码
（如 `tokenize E-LEX-QUOTE@1:8`、`parse E-PARSE-MISSING-BLOCK@1:30`、
`load E-LOAD-VERB-UNKNOWN@1:1`），无“失败但错误码不符”的用例。结论：满足。

### E-2 pending 数量为 0

`--all` 原文（见 E-1）：

```text
gate     : all buckets; pending=0, retired=4, problems=无
pending:   0 not run (A 0, B 0)
```

独立复核 retired 痕迹数：

```console
$ grep -rl '"retired": true' testdata/0.1.0/pending | wc -l
       4
```

`retired: true` 目录只作转正痕迹，harness 不发现、不执行；E-2 以
`pending: 0 not run (A 0, B 0)` 为准。

记录偏差：卡片 §7 #6 写“5 个 `{"retired": true}` 目录”，实测为 4 个；
`git log --oneline -- testdata/0.1.0/pending` 只有初始落库 `ff534e1`，
不存在第 5 个。以实测 4 为准，`rill-0.1.0-acceptance.md` §3 与
`rill-0.1.0-known-limits.md` 也均为 4；卡片 §7 未回改，列入遗留项。
结论：满足。

### E-3 round-trip 全绿

```console
$ bash tools/check-fmt.sh --roundtrip
PASS phase12 roundtrip: compress→display→compress AST 等价（71 个 fixture）
EXIT=0
```

结论：满足（退出码 0）。

### E-4 同 fixture 双 profile AST 相等；host-specific 差异全部有记录

```console
$ bash tools/check-0.1.0.sh --bucket host
RILL 0.1.0 harness
root     : testdata/0.1.0
sut      : python3 -m rill
profiles : agent, shell
fixtures : 1 (host 1)
filters  : bucket=host

PASS    host/shared/read-send (host-ast-equal)  AST 在 shell / agent 下相等

summary
  compliance: 1 passed, 0 failed, 0 blocked, 0 draft
  smoke:     0 passed, 0 failed, 0 blocked, 0 draft
  pending:   0 not run (A 0, B 0)
VERDICT: PASS (exit 0)
EXIT=0
```

差异表锚点：

```console
$ grep -n "### 9.2 host-specific 差异清单\|结论：六项差异" docs/planning/rill-0.1.0-host-matrix.md
154:### 9.2 host-specific 差异清单
165:结论：六项差异全部落在能力层，parser 与 AST 不感知宿主；同一 fixture 的
```

E-1 的全量输出还含 `smoke/dual-profile (host-ast-equal) PASS`。结论：满足。

### E-5 `bash tools/check-0.1.0.sh --all` 退出 0

命令与完整原始输出见 E-1；末行 `VERDICT: PASS (exit 0)`，退出码 0。
结论：满足。

### E-6 不修改 0.1.1 正文

```console
$ git diff --quiet HEAD -- docs/RILL-0.1.0.md; echo "EXIT=$?"
EXIT=0
$ git status --porcelain -- docs/RILL-0.1.0.md
$ git log --oneline -1 -- docs/RILL-0.1.0.md
d96806a docs(spec): 落库 RILL 0.1.1 正文与评审、规划材料
```

CR 清单：无。本 phase 未提出、也未执行任何规范正文变更；卡片 §7 的 9 条
缺口与裁定只写在卡片 §7，未写入 `docs/RILL-0.1.0.md`。结论：满足。

### E-7 任务清单每项可独立验收（T-6）

| 任务 | verify 命令 | 原始输出 | 退出码 | 红 / 实现提交 |
| --- | --- | --- | --- | --- |
| PH-12-T1 | `python3 tests/phase12/test_cli_contract.py` | `PASS phase12 cli: 四子命令/退出码分层/fmt 回读` | 0 | `ef88846` / `b54e50d` |
| PH-12-T2 | `python3 tests/phase12/test_all_gate.py` | `PASS phase12 all: --all 全桶绿 + pending 0` | 0 | `7842ba1` / `6b3f26b` |
| PH-12-T3 | `bash tools/check-fmt.sh --roundtrip` | `PASS phase12 roundtrip: compress→display→compress AST 等价（71 个 fixture）` | 0 | `808607b` / `9636b84` |
| PH-12-T4 | `python3 tests/phase12/test_host_matrix.py` | `PASS phase12 matrix: 五类能力 + PH-12 验收 + host 桶绿` | 0 | `136ba12` / `e6be23e` |
| PH-12-T5 | `python3 tests/phase12/test_acceptance_doc.py` | `PASS phase12 acceptance: 四类清单 + 真实计数 85/83/pending 0` | 0 | `de05df8` / `1c34c21` |
| PH-12-T6 | `python3 tests/phase12/test_known_limits_doc.py` | `PASS phase12 limits: 生产/并发/pending/formatter/基线 20 FAIL` | 0 | `16e5a1c` / `f48071f` |

逐任务独立复跑（同一批次，原文）：

```console
=== python3 tests/phase12/test_cli_contract.py ===
PASS phase12 cli: 四子命令/退出码分层/fmt 回读
EXIT=0
=== python3 tests/phase12/test_all_gate.py ===
PASS phase12 all: --all 全桶绿 + pending 0
EXIT=0
=== python3 tests/phase12/test_host_matrix.py ===
PASS phase12 matrix: 五类能力 + PH-12 验收 + host 桶绿
EXIT=0
=== python3 tests/phase12/test_acceptance_doc.py ===
PASS phase12 acceptance: 四类清单 + 真实计数 85/83/pending 0
EXIT=0
=== python3 tests/phase12/test_known_limits_doc.py ===
PASS phase12 limits: 生产/并发/pending/formatter/基线 20 FAIL
EXIT=0
```

提交可追溯（12 个提交均为 HEAD 祖先）：

```console
$ for s in ef88846 b54e50d 7842ba1 6b3f26b 808607b 9636b84 \
    136ba12 e6be23e de05df8 1c34c21 16e5a1c f48071f; do
    git merge-base --is-ancestor "$s" HEAD && echo "$s ancestor=yes"; done
ef88846 ancestor=yes
b54e50d ancestor=yes
7842ba1 ancestor=yes
6b3f26b ancestor=yes
808607b ancestor=yes
9636b84 ancestor=yes
136ba12 ancestor=yes
e6be23e ancestor=yes
de05df8 ancestor=yes
1c34c21 ancestor=yes
16e5a1c ancestor=yes
f48071f ancestor=yes
```

卡片 §3/§4 自首个实现提交 `b54e50d` 起未被修改
（`git diff b54e50d..HEAD -- docs/phases/PH-12/card.md` 为空）。结论：满足。

## 收口结论

| 判据 | 结果 |
| --- | --- |
| E-1 | PASS（56 正例 / 26 负例全过） |
| E-2 | PASS（pending=0；retired 痕迹 4） |
| E-3 | PASS（71 个 fixture，exit 0） |
| E-4 | PASS（host 桶 1/1；差异 6 条入表） |
| E-5 | PASS（`--all` exit 0） |
| E-6 | PASS（`git diff --quiet` exit 0；CR 无） |
| E-7 | PASS（6 项 verify 全 exit 0） |

**判定：GO。** PH-12 满足 §4 全部退出判据；门禁原始数字为
`fixtures 85 / compliance 83 passed / smoke 2 passed / pending 0 /
retired 4 / FAIL 0 / BLOCK 0 / DRAFT 0`。
