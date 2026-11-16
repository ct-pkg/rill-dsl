# 已裁定差异登记表

> 体例见 `docs/planning/rill-0.1.0-ct-rewrite-roadmap.md` §5。每条差异必须能归到四类之一：
> Python 修 / CT 修 / 规范 CR / 登记豁免（`host-specific`、规范歧义、golden 修订）。
> 未登记的实现差异不得收口。

本表由 PH-13 首次建立。PH-13 token 层 82 个用例两侧 0 差异。

| ID | 类型 | 用例 | 旧值 → 新值 | 归属 | 裁定 | first_seen_phase |
| --- | --- | --- | --- | --- | --- | --- |
| GC-22-01 | golden 修订 | `positive/call/basic`、`bareword-arg` | `FnDef.name` + `CallStmt.args` → `FnDef.shape` + `CallStmt.call` | golden 修订 | PH-22 / D-022；`.sexpr` 重新生成，span 忽略口径不变 | PH-22 |
| GC-22-02 | golden 修订 | `positive/tokens/comments-and-headers` | 定义源改为 `@ $x <read> $x` | golden 修订 | 同上；token 序列随源变化 | PH-22 |
| GC-22-03 | golden 修订 | `expected/run/call-defaults.json`、`call-return-last.json` | 轨迹 `fn.name` → `fn.shape` | golden 修订 | PH-22-T4；轨迹投影只记形状键 | PH-22 |
| GC-22-04 | 用例退场 | `negative/load/fn-name-case` | 名字大小写用例 → 无（名字已移除） | 用例退场 | PH-22；形状匹配由 `fn-shape-*` 覆盖 | PH-22 |
| GC-22-05 | 用例退场 | `negative/load/fn-arity-too-many` | 多传实参 → 无（无位置实参表） | 用例退场 | PH-22；改由 `fn-arity-middle-skip` 覆盖 arity | PH-22 |
| GC-22-06 | 用例退场 | `negative/parse/fn-def-in-body` | 正文定义形状 → 无 | 用例退场 | PH-22 / E-20 与 E-13 冲突：旧形态负例改为测试内动态拼接 | PH-22 |
| AD-22-01 | 登记豁免 | `directed/pd2` | Python `E-PARSE-UNEXPECTED@2:12` ↔ CT 解析成功 | 登记豁免（裁定 A） | PD-2 有意分歧；`expected_diff` 精确匹配，无通配 | PH-22 |
| AD-22-02 | 登记豁免 | `positive/run/call/fn-*` 的裸词/可选介宾 | 无旧值，新增用例 | 登记豁免（新增覆盖） | PH-22 / E-11 / E-8 | PH-22 |
| GC-22-07 | golden 修订 | `positive/tokens/keywords-values` | 第 11 行 `@ "f" 42 $x .host` → `@ f 42 $x .host`；`STRING f` → `BARE f`，同行 `NUMBER/VARIABLE/FIELD/NEWLINE` 列号随宽度左移 | golden 修订 | PH-22-T6 收口补：E-20 清零 `@ "` 后按新词法重录 token 列号 | PH-22 |
| GC-23-01 | golden 修订 | `positive/call/basic` | `FnDef.shape` 首位新增 `"shape_version": 2` | golden 修订 | PH-23-T4 / D-024 §判决 3；形状内容不变 | PH-23 |
| GC-23-02 | golden 修订 | `positive/call/bareword-arg` | `FnDef.shape` 首位新增 `"shape_version": 2` | golden 修订 | 同上 | PH-23 |
| GC-23-03 | golden 修订 | `positive/call/shape-adverb` | `FnDef.shape` 首位新增 `"shape_version": 2` | golden 修订 | 同上；状语名集合与顺序不变 | PH-23 |
| GC-23-04 | golden 修订 | `positive/call/shape-prep-order` | `FnDef.shape` 首位新增 `"shape_version": 2` | golden 修订 | 同上；介词名与顺序不变 | PH-23 |
