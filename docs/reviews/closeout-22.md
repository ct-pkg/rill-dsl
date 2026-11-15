# PH-22 收口：函数签名去名（D-022）

> 判定：**工程面 GO；E-28 未判绿**。E-1…E-27 全过；E-28 的
> `MAJOR.MINOR.PATCH` 落点按卡 §9 属用户签字项，本相不自行收敛（见 §5）。
> 全层对拍 `total diffs: 0`；90 个样例 `compliance 88 + smoke 2`，`pending 0`。
> 本记录只写实测结果；与卡面不一致处按原样登记在 §3。

## 1. 退出判据（E-1…E-28）

| ID | 条件（摘要） | 结果 | 证据 |
| --- | --- | --- | --- |
| E-1 | 规范去名；EBNF/§4.18/§4.20/§五…§八 同步；E-03…E-07 | **过** | §2.1：`grep_absence_exit=0`、`E03_E07_count=11`、`g4_exit=0` |
| E-2 | `@` 后直接 `verb_call`；旧形态 E-07 且位置在字符串 token | **过（计数偏差）** | §2.2：parse 10 项全绿（正 6 / 负 4；卡面写 5/4，见 §3-4） |
| E-3 | `FnDef` 无 `name`；形状字段白名单；`\|>` 后不入签名 | **过** | `test_fn_def_fields_are_whitelisted`、`test_pipe_tail_is_not_in_signature`；`.sexpr` golden 逐字相等 |
| E-4 | 参数名/默认值/状语值不进签名；三种常量写法同值 | **过** | `test_duplicate_shape_differs_only_by_param_name/_default/_adverb_value`、`test_const_forms_share_one_value` |
| E-5 | 同块同形 → E-03，指向后一个定义，Hint 给首个定义行 | **过** | `negative/load/fn-shape-dup` → `load E-03@5:1`；Hint 断含“第 2 行” |
| E-6 | 0 候选 → E-04，位置在 `@`，Hint 列同动词形状，不含名字 | **过** | `negative/load/fn-shape-undeclared` → `load E-04@1:1`；断言无“同名” |
| E-7 | 多候选 → E-05，列出全部候选行号 | **过** | `negative/load/fn-shape-ambiguous` → `load E-05@7:1`；Hint 含第 2、5 行 |
| E-8 | 按形状位绑定；仅尾部可省；中间跳过 → arity；默认值按位 | **过** | `test_arity_missing_required_tail_position`、`test_arity_middle_skip`、`test_tail_default_can_be_omitted` |
| E-9 | 状语按名称集合匹配；多/少一个 → E-04 | **过** | `test_adverb_order_is_ignored`、`test_adverb_extra_name_is_undeclared` |
| E-10 | 介词按名称与顺序；尾随块块标记不进签名 | **过** | `test_prep_order_matters`、`test_trailing_block_is_not_in_signature` |
| E-11 | 重复参数位各次值必须相等；不等 E-06；无空位语法 | **过** | `test_repeated_param_equal_is_accepted`、`test_repeated_param_conflict_is_rejected` |
| E-12 | 直接 `<verb>` 行为不变；函数调用仍须带 `@` | **过** | `test_direct_verb_call_is_not_a_function_call`；原有 run fixture 全绿 |
| E-13 | 旧形态不回退；一律 E-07 | **过（计数偏差）** | 4 条负例（调用/定义/混合/无参）；卡面写 3，见 §3-4 |
| E-14 | parse 正负例全绿 | **过** | §2.2 `PASS phase22 parse: 10 项` |
| E-15 | loader 各错误至少 1 条 | **过** | §2.3 `PASS phase22 load: 17 项` |
| E-16 | eval 重复绑定/默认值/尾随块/返回值各至少 1 条 | **过** | §2.4 `PASS phase22 eval: 9 项` |
| E-17 | CT/Python fn AST 0 差异 | **过** | §2.5 ast `sources=8 ok=8 diffs=0` |
| E-18 | CT/Python fn 错误 0 差异 | **过** | §2.5 error `sources=6 diagnostics=6 diffs=0` |
| E-19 | CT/Python fn 求值 0 差异 | **过** | §2.5 eval `sources=2 ok=2 diffs=0` |
| E-20 | `examples/`、`testdata/0.1.0/`、`tests/` 无旧形态字面量 | **过** | §2.6 `E20_exit=0`（复验时曾红，见 §3-5） |
| E-21 | `09-fn` 可运行；`examples/phase22` 入门禁 | **过** | §2.6 `check-0.1.0.sh --all` PASS；`run.sh` CT/Py 双 PASS |
| E-22 | golden 变更全部登记 | **过** | `docs/reviews/diff/registry.md`：GC-22-01…07、AD-22-01/02 |
| E-23 | 编辑器匹配 `@ <verb>`；JSON 合法 | **过** | §2.7 `PASS phase22 editor: 2 项` |
| E-24 | 三条总门禁全绿 | **过** | §2.8 |
| E-25 | T1…T8 逐项 verify 原文 | **过** | 本文 §2 |
| E-26 | 类型前缀不进签名 | **过** | `test_type_prefix_does_not_change_shape` → E-03 |
| E-27 | 不做兼容层；旧脚本 E-07 且给迁移提示 | **过** | 4 条 E-07 负例；定义用例断言提示含 `verb_call` |
| E-28 | 记录破坏性变更；`version-minor=22`；bump 按 §9 在收口提交内完成 | **未判** | `CHANGELOG.md` 与 `version-minor=22` 已落；`MAJOR.MINOR.PATCH` 待用户三选一签字（§5） |

## 2. 任务逐项 verify（原始输出）

### 2.1 T1：规范去名

```console
$ bash -c '! grep -q "按名字精确匹配" docs/RILL-0.1.0.md'; echo $?
0
$ grep -c "E-0[3-7]" docs/RILL-0.1.0.md
11
$ bash tools/check.sh g4
NOTE  g4: PARTIAL — snippet 渲染/编译（g4-snippets）与 applies-to 时效检查在 Phase 1 后启用

== overall: PASS ==
```

补充提交 `5250664` 在 §4.18 增写“`@` 后不得以字符串开头：常量主语写裸词、
参数主语写 `$变量`、无主语直接写 `<动词>`”，并把示例改成去名形态。

### 2.2 T2：解析

```console
$ python3 tests/phase22/test_fn_shape_parse.py
PASS phase22 parse: 10 项
$ echo $?
0
```

### 2.3 T3：形状表与加载期错误

```console
$ python3 tests/phase22/test_fn_shape_load.py
PASS phase22 load: 17 项
$ echo $?
0
```

### 2.4 T4：绑定与重复参数冲突

```console
$ python3 tests/phase22/test_fn_shape_eval.py
PASS phase22 eval: 9 项
$ echo $?
0
```

### 2.5 T5：CT 对拍

```console
$ python3 tools/diff/diff.py --layer ast --filter fn
   sources=8 ok=8 diagnostics=0 expected=0 diffs=0
   RESULT: PASS
== total diffs: 0

$ python3 tools/diff/diff.py --layer error --filter fn
   sources=6 ok=0 diagnostics=6 expected=0 diffs=0
   RESULT: PASS
== total diffs: 0

$ python3 tools/diff/diff.py --layer eval --filter fn
   sources=2 ok=2 diagnostics=0 expected=0 diffs=0
   RESULT: PASS
== total diffs: 0
```

### 2.6 T6：语料迁移与 0.1.0 门禁

```console
$ bash tools/check-0.1.0.sh --all
gate     : all buckets; pending=0, retired=4, problems=无
fixtures : 90 (positive 60, negative 27, host 1, smoke 2)
summary
  compliance: 88 passed, 0 failed, 0 blocked, 0 draft
  smoke:     2 passed, 0 failed, 0 blocked, 0 draft
  pending:   0 not run (A 0, B 0)
VERDICT: PASS (exit 0)

$ bash -c '! grep -Rq "@ \"" examples testdata/0.1.0 tests'; echo $?
0

$ bash tests/phase22/run.sh
PASS ct examples/phase22
PASS py examples/phase22
$ echo $?
0
```

`check-0.1.0.sh --all` 只覆盖 `testdata/0.1.0` 的 90 个 fixture；
`examples/phase22` 按卡 §5 由 `tests/phase22/run.sh` 双 SUT 驱动。

### 2.7 T7：编辑器语法

```console
$ python3 tests/phase22/test_editor_grammar.py
PASS phase22 editor: 2 项
$ echo $?
0
```

### 2.8 E-24：三条总门禁

```console
$ bash tools/check.sh all
disabled: g2 g3 g5 g7（依赖实现或 ACC/测试资产，当前启用必然失败）
== overall: PASS ==

$ bash tools/check-0.1.0.sh --all
VERDICT: PASS (exit 0)

$ python3 tools/diff/diff.py --all
   sources=89 ok=80 diagnostics=9 expected=0 diffs=0      # token
   sources=89 ok=67 diagnostics=21 expected=1 diffs=0     # ast
   sources=29 ok=1 diagnostics=27 expected=1 diffs=0      # error
   sources=23 ok=22 diagnostics=0 expected=1 diffs=0      # eval
   fixtures=12 diffs=0 directed=5 directed_diffs=0        # host shell
   fixtures=14 diffs=0 directed=1 directed_diffs=0        # host agent
== total diffs: 0
```

`expected=1` 是 PD-2 登记项（Python 参考实现冻结，CT 按 §4.16 解析成功），
按 `expected_diff` 精确匹配两侧摘要，摘要不符即按普通差异失败。

### 2.9 T8：本文

```console
$ test -s docs/reviews/closeout-22.md; echo $?
0
```

## 3. 与卡面偏差

| # | 卡面 | 实际 | 处置 |
| --- | --- | --- | --- |
| 1 | verify 用 `python3 -m pytest tests/phase22/*.py -q` | 环境无 pytest；测试写成 plain python 脚本（同时兼容 pytest） | 按 `python3 tests/phase22/<file>` 验收；T1…T8 判据不变 |
| 2 | T5 verify 依赖 `diff.py --layer ... --filter fn`；T6 用 `--all` | PH-22 前 `diff.py` 只有 `--layer`；`--all`/`--filter` 不存在 | T5 内新增两参数；红证改以 T2…T4 的 Python 侧为准（`phase22-red.md`） |
| 3 | §5 写 `expected/ast/fn-shape/`、`negative/fn-shape/` | harness 固定读 `expected/<ast|tokens>/<rel>.json`，负例按桶落 `negative/load/*` | 沿用现有约定，不另造目录；覆盖集合不变（§2.5） |
| 4 | E-2 正 5/负 4；E-13 负 3 | parse 实际 10 项 = 正 6 + 负 4；旧形态负例 4 条 | 保留多出的正例与“无参旧形态”负例；卡面计数不改 |
| 5 | E-13（要求旧形态负例）与 E-20（语料不得含旧形态）互斥 | 旧形态字面量只允许出现在测试里，且需动态拼接 | E-07 用例用 `"@" + " " + chr(34)` 拼；`negative/parse/fn-def-in-body` 退场（GC-22-06） |
| 6 | 用户要求“Python 参考实现保持冻结” | PH-22 本身要求改 `src/rill`（parser/loader/eval） | 冻结口径按“不为对拍差异改 Python 语义”：PD-2 在 Python 侧保持 `E-PARSE-UNEXPECTED`，只以 `expected_diff` 登记 |
| 7 | D-022 只说“`@` 后写 verb_call” | 常量主语 `@ "name"` 与旧形态不可区分 | 规范补注：`@` 后不得以字符串开头（`5250664`）；属卡内实现裁定，不扩语言面 |
| 8 | 原 `default_tail_can_be_overridden` 用例 | 签名只取模板第一段，第二段参数无法由调用覆盖 | 用例退役，改测“尾部可选介宾可整段省略” |
| 9 | E-20 范围只看 fn 语料 | 全量 grep 把非 fn 夹具一并扫出 | 同步迁移 `positive/tokens/keywords-values`（GC-22-07）与 retired 的 `pending/bareword-value/call-arg-bareword`；`09-fn.md` 改述为“旧形态（`@` 后跟字符串名字）” |
| 10 | 卡面 `version-minor=22` / 目标 `0.22.0` | 产品版本仍 `0.12.0`，`d=10` | E-28 未判绿；§9 A/B/C 待用户签字 |
| 11 | PH-21 判定文书写“85 个用例” | PH-22 新增 5 个 fn 夹具后为 90 | `docs/planning/rill-0.1.0-acceptance.md` 已按 90 更新；`0.1.0-verdict.md` 保留 PH-21 时点原文 |

## 4. 提交

| 任务 | 提交 |
| --- | --- |
| T1 | `e4bf1bb docs(spec): PH-22-T1 函数签名去名`；补注 `5250664 docs(spec): PH-22-T1 补注 @ 后禁字符串主语` |
| T2 | `3796e32 feat(fn): PH-22-T2 解析去名形状` |
| T3 | `e968807 feat(fn): PH-22-T3 形状表与加载期错误` |
| T4 | `0733016 feat(fn): PH-22-T4 绑定与重复参数冲突` |
| T5 | `dfef614 feat(ct): PH-22-T5 函数形状对拍` |
| T6 | `ad42794 test(fn): PH-22-T6 语料去名迁移` |
| T7 | `32cbdbb docs(fn): PH-22-T7 编辑器语法去名` |
| T8 | 本提交 `docs(fn): PH-22-T8 收口对照与变更记录` |

只做本地提交；未 push、未打 tag、未改 `.ai-engineering`。工作区残留的 `.trae/`
是本地工具目录，未纳入提交。

## 5. E-28 与版本偏离（待用户签字）

卡 §9 的三个选项原样保留：

| 方式 | 写法 | 后果 |
| --- | --- | --- |
| A 一次性补号 | `0.22.0`，同一条 deviation 豁免“不许多跳” | 一次跳 10 个 MINOR；CHANGELOG 空段；tag `v0.22.0` |
| B 永久偏移 | `偏移: 10`，收口 `MINOR = 22 - 10 = 12`（`0.12.0`） | 机械可查，但本次收口无可见 minor bump |
| C 将来重编号 | 保持 `0.12.x`，到 `PH-<m>` 时一次跳号 | PH-22 收口仍是 `0.12.0`；届时仍要跳号与空段 |

当前事实：`version-minor=22` 已登记；`src/rill/__init__.py#__version__` 仍为
`0.12.0`；`CHANGELOG.md` 的条目落在 `Unreleased — PH-22`。在上述三选一签字并
写入 `AGENTS.md` 0.3 之前，E-28 不判绿，PH-22 不宣称“收口全绿”。

## 6. 对 0.1.0 完工判定的影响

不变：`docs/reviews/0.1.0-verdict.md` 的 **NO-GO** 仍然成立，唯一不过项是
C-8 `Opaque` 没有构造入口（0.1.1 backlog B-1，明确不在本相范围）。
PH-22 只改函数签名形态，不动值模型、动词表、介宾语义、尾随块与宿主能力。
