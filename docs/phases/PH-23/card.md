# PH-23 立项卡：P-025=B（shape_version=2，签名层不识别类型前缀）

> 状态：正常开卡（2026-11-16）。依据 [D-024](../../decisions/D-024.md) 的
> §判决 1–6；本卡只实现该裁定，不改值层 TypeRegistry，不改调用语法。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-23`，目录 `docs/phases/PH-23/` |
| 目标 | 删除两侧常量位的类型前缀剥离；常量位按 AST 字面原文比较；`shape_version=2` 只进定义侧 `FnDef.shape` 首位；两侧 `SHAPE_VERSION` 常量与 loader 版本断言落地；PH-22 的 E-26 被取代但不回改。 |
| 范围 | 做什么：`src/rill/shape.py`、`src/rill/loader.py`、CT `common.h.ct`/`loader.h.ct`、4 份 AST golden、§4.18 一句、PH-23 测试与收口。不做什么：值层 TypeRegistry 语义、调用侧语法、P-029、D-022/D-024 正文、PH-22 卡片与收口记录。 |
| 交付物清单 | 见 §2，每项一个路径或一个 golden 集合。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | D-024 已 accepted；PH-22 已收口到 `0.22.0`；4 份 fn AST golden；CT 以 PH-22 收口基线为准。 |
| 规范版本 | `1.10.0`。 |
| version-minor | `23`（目标产品版本 `0.23.0`；本轮不动版本落点）。 |
| 已知风险 | 把 `shape_version` 写进调用侧；只改 Python 不改 CT；把 4 份之外的无冒号 golden 也重录；误改 PH-22 E-26。见 §7。 |

## 1. 范围与 D-024 判据映射

| D-024 判据 | 本卡落点 |
| --- | --- |
| §判决 1 常量位按 `String.value` / `Bare.text` / 数字规范字符串比较 | E-1、T1、T2 |
| §判决 2 `file:x` 与 `text:x` 是不同形状，可共存 | E-4、T4、T6 |
| §判决 3 `shape_version=2` 仅定义侧、首位；两侧 `SHAPE_VERSION` 常量 | E-2、E-3、E-8、E-9 |
| §判决 4 loader 收集时断言版本，不匹配报 `E-LOAD-FN-SHAPE-VERSION` | E-6、E-7、E-10 |
| §判决 5 引号透明：`file:x`/`"file:x"` 同值，`'ok'`/`"ok"`/`ok` 同值 | E-5、T1、T4 |
| §判决 6 PH-22 E-26 被本条取代；PH-22 卡与收口冻结、不回改 | E-18、T6 |

`src/rill/shape.py` 顶部“P-025 未裁定前”的注释随 T1 一并删除；PH-22 卡
[E-26](../PH-22/card.md) 与 [closeout-22](../../reviews/closeout-22.md) 一个字不改。

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `src/rill/shape.py` | 字面原文比较、`SHAPE_VERSION=2`、定义侧首位、注释更新 |
| `src/rill/loader.py` | 定义收集时版本断言、`E-LOAD-FN-SHAPE-VERSION` |
| `ct/src/common/common.h.ct` | CT 形状字面比较与 `SHAPE_VERSION` |
| `ct/src/loader/loader.h.ct` | CT 版本断言与同码错误 |
| `testdata/0.1.0/expected/ast/positive/call/basic.json` 等 4 份 | AST golden 重录（见 §4 E-13） |
| `docs/RILL-0.1.0.md` §4.18 | 补“字面原文、引号透明、前缀不拆分、shape_version”一句 |
| `tests/phase23/` | 红证、正负例、对拍断言 |
| `docs/reviews/diff/registry.md` | 4 条 `golden-change:` |
| `docs/reviews/diff/PH-23.md` | 两侧差异报告 |
| `docs/reviews/closeout-23.md` | 收口对照 |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | 红证 | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PH-23-T1 | `src/rill/shape.py` 字面比较、版本常量、注释 | `test(shape): PH-23-T1 红` → `feat(shape): PH-23-T1 字面原文与 v2` | `git revert <sha>` | `python3 -m pytest tests/phase23/test_shape_literal.py -q` | `red: rc=1, "file:x 与 text:x 同形"` | M | E-1,E-2,E-3,E-5,E-8,E-17 |
| PH-23-T2 | `src/rill/loader.py` 版本断言 | `test(load): PH-23-T2 红` → `feat(load): PH-23-T2 shape 版本断言` | `git revert <sha>` | `python3 -m pytest tests/phase23/test_shape_version_load.py -q` | `red: rc=1, "旧 shape_version 未被拒"` | M | E-6,E-7 |
| PH-23-T3 | CT `common.h.ct`/`loader.h.ct` 对等实现 | `test(ct): PH-23-T3 红` → `feat(ct): PH-23-T3 字面比较与版本断言` | `git revert <sha>` | `python3 tools/diff/diff.py --layer ast --filter fn && python3 tools/diff/diff.py --layer error --filter fn` | `red: rc=1, "CT 仍剥前缀"` | M | E-9,E-10,E-11,E-12 |
| PH-23-T4 | 4 份 fn AST golden 重录 | `test(golden): PH-23-T4 红` → `test(golden): PH-23-T4 重录` | `git revert <sha>` | `bash tools/check-0.1.0.sh --all && grep -q 'golden-change:' docs/reviews/diff/registry.md` | `red: rc=1, "4 份 AST golden 缺 shape_version"` | M | E-13,E-14,E-15 |
| PH-23-T5 | `docs/RILL-0.1.0.md` §4.18 单句 | `docs(spec): PH-23-T5 常量位字面比较` | `git revert <sha>` | `bash -c 'grep -q "字面原文" docs/RILL-0.1.0.md && tools/check.sh g4'` | `no-test: 规范正文单句，无行为改动` | S | E-16,E-19 |
| PH-23-T6 | `tests/phase23/` E-26 取代与对拍用例 | `test(shape): PH-23-T6 红` → `test(shape): PH-23-T6 E-26 取代覆盖` | `git revert <sha>` | `python3 -m pytest tests/phase23/test_e26_superseded.py -q && python3 tools/diff/diff.py --all --filter fn` | `red: rc=1, "旧 E-26 仍期待 E-03"` | M | E-4,E-18,E-20,E-21,E-22 |
| PH-23-T7 | `docs/reviews/closeout-23.md`、`docs/reviews/diff/PH-23.md` | `docs(review): PH-23-T7 收口对照` | `git revert <sha>` | `test -s docs/reviews/closeout-23.md && tools/check.sh all` | `no-test: 收口记录与差异报告` | S | E-23,E-24 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。任务清单每项可独立验收（T-6）。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | `_strip_type_prefix` 删除；`String` 取 `value`、`Bare` 取 `text`、`Number` 取规范字符串，直接比较；不读 TypeRegistry | `test_shape_literal.py` 正例 4 条、负例 2 条全绿 |
| E-2 | Python `SHAPE_VERSION=2`；定义侧 `shape_of(..., template=True)` 首位写 `shape_version` | AST 断言 `list(shape)[0] == "shape_version"` |
| E-3 | `shape_version` 在定义侧 `FnDef.shape` 首位，且只出现一次；调用侧不写 | 正例 `.json`/`.sexpr` 键序断言 |
| E-4 | `file:x` 与 `text:x` 是两个不同形状，可在同一 `//fn` 共存；不再因前缀差异报 E-03 | `test_e26_superseded.py` 正例 |
| E-5 | `file:x` 与 `"file:x"` 同形；`'ok'`/`"ok"`/`ok` 同形；节点种类不参与槽位比较 | 4 组等价断言 |
| E-6 | loader 收集 `FnDef` 时断言 `shape_version == SHAPE_VERSION`；不匹配报 `E-LOAD-FN-SHAPE-VERSION`，位置在定义 span | 负例 `.err.json` 精确 kind/line/col |
| E-7 | 宿主注入/合并带入的 v1 形状同样被 E-06 拦截，不得静默参与匹配 | 注入负例 1 条 |
| E-8 | 调用形状无 `shape_version`；调用侧 AST/golden 除形状值外不变 | `shape_of(call, template=False)` 键集断言 |
| E-9 | CT `SHAPE_VERSION=2`；定义侧首位；常量位不剥前缀；不查 TypeRegistry | CT 单测/对拍通过 |
| E-10 | CT loader 同码 `E-LOAD-FN-SHAPE-VERSION`，位置与 Python 一致 | 错误对拍 0 差异 |
| E-11 | 新前缀用例的 Python/CT AST 对拍 0 差异 | `diff.py --layer ast --filter fn` 退出 0 |
| E-12 | 版本错误与前缀错误的 Python/CT 错误对拍 0 差异 | `diff.py --layer error --filter fn` 退出 0 |
| E-13 | 仅 4 份 golden 重录：`call/basic.json`、`call/bareword-arg.json`、`call/shape-adverb.json`、`call/shape-prep-order.json`；每份 `shape` 首位为 `"shape_version": 2` | `git diff --name-only` 命中集合等于这 4 份 |
| E-14 | 4 条 `golden-change:` 写入 `docs/reviews/diff/registry.md`，含旧值→新值、归属、裁定、first_seen_phase | `grep -c 'GC-23-'` ≥ 4 |
| E-15 | 无冒号常量的其他 fn golden 不重录；`shape-adverb`/`shape-prep-order` 只增版本键，形状内容不变 | `git diff` 逐份核对 |
| E-16 | §4.18 只补一句：“常量位按 AST 字面原文比较；引号不改变形状；类型前缀在签名层不拆分；shape_version=2 仅定义侧” | `grep` 命中，且该节其他行未改 |
| E-17 | `src/rill/shape.py` 顶部“P-025 未裁定前”注释删除，改为 D-024 口径 | `grep -c "P-025 未裁定前"` = 0 |
| E-18 | PH-22 E-26 与 closeout-22 逐字未改；新测试断言旧行为被 D-024 §判决 6 取代 | `git diff --exit-code` 对两文件退出 0；`test_e26_superseded.py` 绿 |
| E-19 | 不改 D-022/D-024 正文、不改调用语法、不改值层 TypeRegistry | 提交路径白名单断言 |
| E-20 | `tests/phase23/` 覆盖字面、前缀、引号、版本、加载错误、E-26 反转各至少 1 条 | `pytest tests/phase23 -q` 退出 0 |
| E-21 | `tools/check-0.1.0.sh --all` 全绿，0 pending | 退出 0 |
| E-22 | `tools/diff/diff.py --all --filter fn` 0 未解释差异 | 退出 0；差异全部登记 |
| E-23 | `tools/check.sh all` 全绿；`g1/g4/g8` 不因本卡转红 | 退出 0 |
| E-24 | `closeout-23.md` 逐项 T1…T7 verify 原文；`version-minor=23`、目标 `0.23.0`；实际 bump 留到收口提交 | 收口对照表与 `git show` 一致 |

## 5. 样例计划

| 样例 | 内容 | 门禁 |
| --- | --- | --- |
| `tests/phase23/fixtures/prefix-shapes.ri` | `file:x` 与 `text:x` 两个定义 + 两次调用；断言两个形状共存 | `pytest tests/phase23/test_e26_superseded.py -q` |
| `tests/phase23/fixtures/quote-transparent.ri` | `file:x`/`"file:x"`、`'ok'`/`"ok"`/`ok` 各一组 | `test_shape_literal.py -q` |
| `tests/phase23/fixtures/v1-shape.json` | 手工 v1 形状注入，断言 `E-LOAD-FN-SHAPE-VERSION` | `test_shape_version_load.py -q` |
| 4 份 AST golden | 见 E-13；键序含 `shape_version` | `check-0.1.0.sh --all` |

golden 格式沿用现有 AST JSON；新增键只允许 `shape_version`，且必须首位。不另造格式。

## 6. 红证与提交节奏

- T1/T2/T3/T4/T6 先提交 `test(...): PH-23-T<n> 红`，只含夹具、断言与红证；实现/重录提交随后转绿。
- 红证正文写 `baseline: <sha>`、命令、原始输出、退出码；`red: rc=<N>, "<失败文案>"` 必须来自真实运行。
- T5/T7 为纯规范/收口任务，写 `no-test` 理由，由 VERIFY 签字。
- 每项任务一次实现提交、一个路径集合、可单独 `git revert`；不得把 Python、CT、golden 混在一个提交。
- 首个实现提交后 §3/§4 冻结；要改只能关闭 PH-23 另开。

## 7. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | D-024 §判决 1–6；PH-22 的 `shape.py`/`loader.py`/CT 基线；4 份 fn AST golden；`tools/diff/diff.py`；`docs/reviews/diff/registry.md`。 |
| 风险 1 | 把 `shape_version` 写进调用侧：早期探针断言 `shape_of(call, template=False)` 无该键；E-8 守住。 |
| 风险 2 | 只改 Python：T3 先以 CT 仍剥前缀建红；E-11/E-12 对拍 0 差异。 |
| 风险 3 | 顺手重录无冒号 golden：E-13 用 `git diff --name-only` 限定为 4 份；E-15 逐份核对。 |
| 风险 4 | 回改 PH-22 E-26/收口：E-18 用 `git diff --exit-code` 对两文件守住；D-024 §判决 6 只在新卡引用。 |
| 风险 5 | P-029 被顺手裁定：调用侧版本握手不在本卡；E-8 只断言“不写”，不实现握手。 |

## 8. 退出条件

- **收口状态**：E-1…E-24 全绿；T1…T7 每项有 verify 原始输出；`tools/check.sh all` 与
  `tools/check-0.1.0.sh --all` 退出 0；`closeout-23.md` 与 `diff/PH-23.md` 完成。
- **判定人**：VERIFY 逐条认定；REVIEW 复核；用户签收口记录与 `0.23.0` 版本移动。
- **PH-24 前提**：PH-23 收口、`0.23.0` 落地；P-029 另开卡，不并入本卡。

## 9. 卡内裁定与未决

| 编号 | 事项 | 裁定/去向 |
| --- | --- | --- |
| C-1 | PH-22 E-26 | 冻结不回改；本卡 E-18 断言被 D-024 §判决 6 取代 |
| C-2 | `shape_version` 位置 | 仅定义侧、首位；调用侧不写（D-024 §判决 3） |
| C-3 | 引号透明 | `String.value` / `Bare.text` / 数字规范字符串；不按节点种类区分（D-024 §判决 5） |
| C-4 | 4 份 golden | 仅 `call/basic`、`call/bareword-arg`、`call/shape-adverb`、`call/shape-prep-order`；无冒号常量不重录 |
| U-1 | P-029 调用侧版本握手 | 未决，不阻塞本卡；E-8 只保证调用侧不写版本 |
| U-2 | D-022 的 P-025 条件句 | 过时表述不改；D-024 §判决 6 为现行口径 |
