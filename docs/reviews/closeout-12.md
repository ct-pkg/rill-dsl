# PH-12 收口对照表

> 基线 `4d7b213`（复核卡）；实现提交 `ef88846..f48071f`；PH-11 复核补记后
> 重新跑过全部门禁。只本地提交，不 push、不打 tag。红证与逐任务记录见
> `docs/reviews/phase12-red.md`。

## 1. 判定

**GO。** 四个子命令可用；85 个 fixture 全过；同源 AST 跨 profile 相等；
round-trip 全绿；文档门禁的 21 个 FAIL 均为既有基线，不冒充通过。

## 2. 退出判据

| ID | 条件 | 原始证据 | 结果 |
| --- | --- | --- | --- |
| E-1 | 正例通过；负例按预期错误码失败 | `--all` → 83 compliance + 2 smoke passed；0 failed | PASS |
| E-2 | pending 为 0 | `pending: 0 not run (A 0, B 0)`；retired 4 不计 | PASS |
| E-3 | round-trip 全绿 | `bash tools/check-fmt.sh --roundtrip` → 71 个 fixture，exit 0 | PASS |
| E-4 | 同 fixture 双 profile AST 相等 | `--bucket host` → `PASS host/shared/read-send`；差异 6 条入表 | PASS |
| E-5 | `--all` 退出 0 | `VERDICT: PASS (exit 0)` | PASS |
| E-6 | 不改 0.1.1 正文 | `git diff --quiet HEAD -- docs/RILL-0.1.0.md` → 0；CR 无 | PASS |
| E-7 | 每项可独立验收 | 6 项 verify 均 exit 0（见 §3） | PASS |

## 3. 任务 verify

| 任务 | verify | 原始输出 | 退出码 |
| --- | --- | --- | --- |
| PH-12-T1 | `python3 tests/phase12/test_cli_contract.py` | `PASS phase12 cli: 四子命令/退出码分层/fmt 回读` | 0 |
| PH-12-T2 | `python3 tests/phase12/test_all_gate.py` | `PASS phase12 all: --all 全桶绿 + pending 0` | 0 |
| PH-12-T3 | `bash tools/check-fmt.sh --roundtrip` | `PASS phase12 roundtrip: ...（71 个 fixture）` | 0 |
| PH-12-T4 | `python3 tests/phase12/test_host_matrix.py` | `PASS phase12 matrix: 五类能力 + PH-12 验收 + host 桶绿` | 0 |
| PH-12-T5 | `python3 tests/phase12/test_acceptance_doc.py` | `PASS phase12 acceptance: 四类清单 + 真实计数 85/83/pending 0` | 0 |
| PH-12-T6 | `python3 tests/phase12/test_known_limits_doc.py` | `PASS phase12 limits: ... 基线 21 FAIL` | 0 |

## 4. PH-11 复核补记对本阶段的影响

| 影响点 | 处理 | 验证 |
| --- | --- | --- |
| `--fakes` 未处理失败改为退出 1 | harness 的 SUT 接受“退出 1 + `{"ok": false}`”，run 用例仍 PASS | `python3 tests/phase12/test_all_gate.py` |
| Agent 工具改为真实子进程 | 同源 AST 不变；host 桶仍 PASS | `--bucket host` |
| host-matrix 增加真实传输/principal/陈账章节 | PH-12 文档一致性断言仍通过 | `python3 tests/phase12/test_host_matrix.py` |
| `phase12-red.md` 增至 433 行 | 文档门禁基线从 20 改为 21，如实登记 | `python3 tests/phase12/test_known_limits_doc.py` |

## 5. 全量计数与仍不可用

```text
fixtures 85（positive 56 / negative 26 / host 1 / smoke 2）
compliance 83 passed；smoke 2 passed；failed 0；blocked 0；draft 0
pending 0；retired 4；--all exit 0
doc gate 21 FAIL（DOC-S2 9 + 断链 9 + 未定义版本 3，均为既有基线）
```

仍不可用：生产工具/审批/白名单、真实并发调度、Agent 读真实 OS 环境变量、
独立 `[ok]` / `[error]` 形式语句（用尾随块绕开）、旧 `v0.1 rev.1` 兼容。
