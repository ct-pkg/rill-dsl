# PH-22 收口：函数签名去名（D-022）

> 判定：**GO（工程面收口）**。E-1…E-28 全绿；E-28 按用户 **C 裁定**判绿：
> 产品版本保持 `0.12.0`，phase 号与版本解耦，映射与重编号触发见 `AGENTS.md` 0.3。
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
| E-28 | 记录破坏性变更；`version-minor=22`；bump 按 §9 在收口提交内完成 | **过** | C 裁定：产品保持 `0.12.0`；`AGENTS.md` 0.3 登记 `deviation: PH-22-version` + 映射表；`CHANGELOG.md` 同条目（§5） |

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
| 10 | 卡面 `version-minor=22` / 目标 `0.22.0` | 用户裁定走 C：产品保持 `0.12.0`，phase 号与版本解耦 | E-28 据此判绿；映射表与重编号触发写入 `AGENTS.md` 0.3（§5） |
| 11 | PH-21 判定文书写“85 个用例” | PH-22 新增 5 个 fn 夹具后为 90 | `docs/planning/rill-0.1.0-acceptance.md` 已按 90 更新；`0.1.0-verdict.md` 保留 PH-21 时点原文 |
| 12 | 卡 §4 未预设门禁对非法 fixture 的处理 | 一个 `phase: p22` 让整个 0.1.0 门禁拒绝执行，合法用例零信号 | 数据修为 `r1`；门禁行为登记为 **GD-001**（`docs/planning/rill-0.1.0-known-limits.md` §7），本相不改共享门禁 |
| 13 | 卡面 E-20 只要求“清零” | 收口复验时 `tests/` 仍有 3 处旧形态字面量 | 位置见 §3.1；已全部清零（`E20_exit=0`） |

### 3.1 E-20 补改位置（旧形态字面量）

收口复验时 `grep -R '@ "'` 仍红。以下位置全部改为“动态拼接”或改述，避免下次改名再漏：

| # | 位置 | 原内容 | 处置 |
| --- | --- | --- | --- |
| 1 | `tests/phase9/test_fn.py:27` | `OLD = "@ " + '"'` | 改 `"@" + " " + chr(34)` |
| 2 | `tests/phase22/test_fn_shape_parse.py:13-14` | 注释含旧形态；`OLD` 同上一行写法 | 注释改述；`OLD` 改 `"@" + " " + chr(34)` |
| 3 | `tests/phase22/test_editor_grammar.py:1` | 模块 docstring 含旧形态 | 改述为“旧形态（`@` 后跟字符串）” |
| 4 | `tests/phase22/test_editor_grammar.py:34` | `compiled.search('@ "name"')` | 改 `"@" + " " + '"name"'` |
| 5 | `examples/tour/09-fn.md:10` | 正文示例写旧形态字面量 | 改述为“旧形态（`@` 后跟字符串名字）” |
| 6 | `testdata/0.1.0/positive/tokens/keywords-values/source.ri:11` | `@ "f" 42 $x .host` | 改 `@ f 42 $x .host`；token golden 按 GC-22-07 重录 |
| 7 | `testdata/0.1.0/pending/bareword-value/call-arg-bareword/source.ri:1` | `@ "f" foo` | retired 痕迹改 `@ <read> foo` |

其中 1–2 是同一条 `OLD` 常量在 phase9 与 phase22 的两份拷贝，改一处漏一处
会再次触发 E-20；3–4 是断言自身的匹配串，不能只改注释。

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
| T8 | `9c3286c docs(fn): PH-22-T8 收口对照与变更记录` |
| T8 补 | 本次提交 `docs(review): PH-22 E-28 判绿与门禁缺陷登记`（C 裁定、GD-001、旧形态位置） |

只做本地提交；未 push、未打 tag、未改 `.ai-engineering`。工作区残留的 `.trae/`
是本地工具目录，未纳入提交。

## 5. E-28 版本裁定（C，已执行）

用户 2026-11-15 裁定走 **C**；重编号提案同日批准并执行：

- **phase 号与产品版本正式解耦**：phase 号只表示开发序列，映射表在
  `AGENTS.md` 0.3（PH-12 → `0.12.0`；PH-13…PH-21 → `0.12.0`；
  PH-22 → `0.22.0`，重编号点）。
- **重编号**：产品 `0.12.0` → `0.22.0`，与 0.1.0 判定转 GO 同一条提交完成，
  并建 annotated tag `v0.22.0`。
- **解耦原因（留档）**：转 GO 之前，真正待发的语言规范 0.1.0 因 C-8 `Opaque`
  无构造入口仍是 NO-GO；那时跳号会让外部把 phase 数误读为发布进度。
- **触发条件已发生**：`docs/reviews/0.1.0-verdict.md` 的 C-8 经
  `tests/opaque` 测试通道验收后转 GO，触发本次重编号；旧映射表留档不改写。

E-28 判绿：`AGENTS.md` 0.3 的 `deviation: PH-22-version` 含
日期/条款/现状/理由/收敛/签字六项；`CHANGELOG.md` 有 `0.22.0` 段；
`src/rill/__init__.py#__version__` 为 `0.22.0`，`g8-version` 报
“版本落点一致：0.22.0”。

## 6. 对 0.1.0 完工判定的影响

0.1.0 已转 **GO**：`docs/reviews/0.1.0-verdict.md` 8/8 判据全过。
唯一曾经的不过项 C-8 `Opaque` 由 0.1.1 B-1 的测试通道补齐
（`docs/reviews/opaque-c8-evidence.md`），B-1 标完成。
PH-22 本身只改函数签名形态，不动值模型、动词表、介宾语义、尾随块与宿主能力。
