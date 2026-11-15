# CHANGELOG

> 版本规则见 `AGENTS.md` 6.7。`version-minor` 与 phase 对应；本文件只记已经落地的
> 行为变更，版本号落点以 `docs/session-map.md` 的「版本落点」为准。

## Unreleased — PH-22 函数签名去名（version-minor=22）

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
- 版本号 bump 方式见 `docs/phases/PH-22/card.md` §9（A/B/C 待用户签字）；
  `version-minor` 已登记为 `22`，实际 `MAJOR.MINOR.PATCH` 落点见
  `docs/reviews/closeout-22.md` §5。
