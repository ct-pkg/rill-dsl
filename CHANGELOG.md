# CHANGELOG

> 版本规则见 `AGENTS.md` 6.7。本项目 phase 号与产品版本已解耦，映射见
> `AGENTS.md` 0.3；本文件只记已经落地的行为变更。

## 0.23.0 — 2026-11-16（PH-23 收口 / P-025=B）

### Changed

- 函数签名常量位不再剥离 `类型:值` 前缀：按 AST 字面原文比较（`String.value` /
  `Bare.text` / 数字规范字符串）；`file:x` 与 `text:x` 是不同形状，可共存；
  跨前缀调用报 `E-04`。依据 `docs/decisions/D-024.md`。
- 引号透明：`file:x` 与 `"file:x"` 同形；常量槽不按节点种类区分。
- 定义侧 `FnDef.shape` 首位新增 `shape_version: 2`；Python/CT 各持
  `SHAPE_VERSION = 2`；loader 收集时断言，不匹配报 `E-LOAD-FN-SHAPE-VERSION`。
- PH-22 的 E-26 被 D-024 §判决 6 取代；PH-22 卡与 `closeout-22.md` 未改。

### Notes

- 版本：产品 `0.22.0` → `0.23.0`（PH-23 收口）。4 份 AST golden 重录并登记
  `GC-23-01…GC-23-04`；全层对拍 `total diffs: 0`。

## 0.22.0 — 2026-11-15（PH-22 收口 / 0.1.0 判定转 GO / 重编号点）

### Breaking

- 函数定义与调用去掉字符串名字：`@` 后直接写 `verb_call`。签名由模板第一段机械导出的
  形状键构成（动词词面、主语/宾语位身份、常量值、状语名集合、介词名与顺序）；参数变量名、
  默认值、状语值不进签名。依据 `docs/decisions/D-022.md`，正文见 `docs/RILL-0.1.0.md` §4.18。
- 旧形态 `@ "name"` 一律解析期 `E-07`，不保留按名字查找的回退路径；`@` 后不得以字符串
  开头（常量主语写裸词，参数主语写 `$变量`）。
- 新增错误码：`E-03` 同块同形、`E-04` 未声明形状、`E-05` 调用二义、`E-06` 重复参数位
  值不等、`E-07` 旧形态。`E-LOAD-FN-ARITY` 与 `E-LOAD-FN-DEFAULT-NOT-TAIL` 继续有效。

### Fixed

- PD-1：`$"-x"` 在 CT 侧不再误判为不相邻；`$` 的相邻宽度为 1。
- PD-2：`"n="$v` 在 CT 侧按 §4.16 解析为拼接；Python 参考实现按 A 案冻结，两侧差异
  以 `testdata/0.1.0/directed/pd2/case.json#expected_diff` 登记。
- 统一宽度口径：`Token.raw_len` 由 lexer 写入，parser 的 `p_adjacent` 与 formatter 的
  `f_raw_width` 只读该字段。

### Notes

- 本相不停留在“名字 + 字符串匹配”；同形冲突在加载期显式报错，不做静默覆盖。
- 版本：产品 `0.12.0` → `0.22.0`（2026-11-15 重编号点）。触发条件是 0.1.0 判定转 GO；
  phase 号与产品版本解耦，映射与历史留档见 `AGENTS.md` 0.3。
- 0.13.0…0.21.0 为 PH-13…PH-21 的计划版本，从未发布；PH-22 重编号结案后恢复 V-1（PH-23 → 0.23.0），本文件不补假条目。
- 0.1.0 判定：C-8 `Opaque` 经 `tests/opaque` 测试通道验收（透传同一性 + truthy +
  边界不有损），0.1.0 由 NO-GO 转 GO。`src/rill` 实现零改动，仅 `__version__` 随本版移动。
