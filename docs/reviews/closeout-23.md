# PH-23 收口（P-025=B / D-024）

- 日期：2026-11-16
- 判定：**收口 PASS**
- 依据：[D-024](../decisions/D-024.md) §判决 1–6；[PH-23 卡](../phases/PH-23/card.md)
- 版本：`0.22.0` → `0.23.0`；tag `v0.23.0`（annotated，指向本收口提交）
- 基线：PH-22 收口 `0.22.0`（`47e2a68`）；本相开工前 `main` 为 `91ff990`

## 1. 任务对照

| 任务 | 提交 | verify 原始结果 |
| --- | --- | --- |
| T1 | 红 `cba0cc3` / 绿 `cf94008` | `pytest tests/phase23/test_shape_literal.py -q` → 7 passed |
| T2 | 红 `66cb3a5` / 绿 `bbddfc6` | `pytest tests/phase23/test_shape_version_load.py -q` → 5 passed |
| T3 | 红 `552a12a` / 绿 `c3292dd` | `pytest tests/phase23/test_ct_shape_version.py -q` → 1 passed；ast/error `--filter fn` 均 `total diffs: 0` |
| T4 | `8799158` | `bash tools/check-0.1.0.sh --all` → `compliance 89 passed, 0 failed`，`VERDICT: PASS` |
| T5 | `a42a269` | `bash tools/check.sh g4` → PASS；§4.18 单句已改，其他行未动 |
| T6 | 红 `9be6354` / 绿 `5235a8b` | `pytest tests/phase23 -q` → 16 passed；`check-0.1.0.sh --all` → 89 passed |
| T7 | 本提交 | `bash tools/check.sh all` → `overall: PASS` |

## 2. 退出判据 E-1…E-24

| 判据 | 结果 | 证据 |
| --- | --- | --- |
| E-1 Python 字面比较 | PASS | T1 测试；`shape_const_value` 去前缀 |
| E-2 定义侧首位 shape_version | PASS | 4 份 AST golden；T2 测试 |
| E-3 调用侧不写版本 | PASS | 4 份调用 golden 无该键 |
| E-4 E-26 取代覆盖 | PASS | `test_e26_superseded.py` 3 项；跨前缀 E-04 |
| E-5 重复字面量 E-03 | PASS | 同字面常量/引号透明仍报 E-03 |
| E-6 Python loader 断言 | PASS | `test_shape_version_load.py` 5 项 |
| E-7 宿主注入 v1 被拒 | PASS | Python/CT 两侧版本断言测试 |
| E-8 引号透明 | PASS | `file:x` 与 `"file:x"` 同形 |
| E-9 CT 字面比较 | PASS | `shape_strip_type` 已删除；`shape_const_value` 原文比较 |
| E-10 CT loader 断言 | PASS | `load_check_shape_version`，`E-LOAD-FN-SHAPE-VERSION` |
| E-11 CT 错误码与位置 | PASS | 定义 span；`test_ct_shape_version.py` |
| E-12 两侧对拍 | PASS | ast 10 源 / error 8 源 7 诊断，均 0 差异 |
| E-13 4 份 AST golden | PASS | `GC-23-01…GC-23-04` |
| E-14 registry 登记 | PASS | `docs/reviews/diff/registry.md` 4 行 |
| E-15 其他 golden 未改 | PASS | `check-0.1.0.sh --all` 89 passed |
| E-16 §4.18 单句 | PASS | “按 AST 字面原文比较……类型前缀在签名层不拆分” |
| E-17 过时注释 | PASS | `grep 'P-025 未裁定前' src/rill/shape.py` → 0 |
| E-18 PH-22 冻结 | PASS | `git diff 91ff990 -- PH-22/card.md closeout-22.md` 为空 |
| E-19 D-022/D-024 未改 | PASS | 同上 diff 为空 |
| E-20 pytest tests/phase23 | PASS | 16 passed |
| E-21 check-0.1.0 --all | PASS | 89 passed，VERDICT PASS |
| E-22 全层对拍 | PASS | `tools/diff/diff.py --all` → `total diffs: 0` |
| E-23 tools/check.sh all | PASS | `overall: PASS` |
| E-24 本收口文件 | PASS | 本文件 |

## 3. 差异与豁免

- 差异登记：`GC-23-01…GC-23-04`，全部为 golden 修订（新增 `shape_version` 键）。
- 无 `AD-23-*` 豁免；全层对拍 0 未解释差异。

## 4. 风险与遗留

- `RILL-001` / `BL-003`：C-8 `Opaque` 证据通道仍是 Python 归档、不可复跑；
  不阻塞 PH-23，按 0.1.1 backlog 处理。
- `v0.22.0` tag message 未含收口 sha，属历史已知缺口；本相不改写历史。
- `pytest` 在验环境中通过 `pip install --user pytest` 安装；仓库不新增运行时依赖。

## 5. 结论

PH-23 收口，产品 `0.23.0`，tag `v0.23.0`。PH-22 的 E-26 由 D-024 §判决 6
取代，PH-22 卡与 `closeout-22.md` 保持逐字未改。
