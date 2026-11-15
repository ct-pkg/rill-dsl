# PH-22 立项卡：函数签名去名（D-022）

> 状态：正常开卡（2026-11-15）。依据 [D-022](../../decisions/D-022.md) 与
> `docs/RILL-0.1.0.md` 0.1.1。本卡只实现“去掉 `@ "name"`、按形状匹配”的变更，
> 不裁定 P-025/P-026，不改宿主能力层。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-22`，目录 `docs/phases/PH-22/` |
| 目标 | 函数定义与调用去掉字符串名字；签名由“动词 + 状语 + 介词”的形状键机械导出；同形冲突、未声明形状、二义、重复参数绑定冲突显式报错；Python 与 CT 双实现同步。 |
| 范围 | 做什么：规范正文去名、AST/parser、loader 形状表、eval 绑定、CT 对拍、语料与编辑器。不做什么：P-025 类型前缀入签名、P-026 对外迁移策略、新动词/状语/介宾语义、宿主能力、性能。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | D-022 已 accepted；Python 0.12.0（PH-12）；CT 以 PH-21 收口状态为准；P-025/P-026 不阻塞本卡实现，但阻塞对外发布口径。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `22`（目标产品版本 `0.22.0`；当前 `0.12.0`，存量落差见 §9）。 |
| 已知风险 | 形状键把不该进的成分放进签名；旧语料残留 `@ "name"`；CT 三处实现漂移；P-025/P-026 被顺手裁定。见 §7。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| 规范正文：§二、§三、§4.18、§4.20、§五、§六、§七、§八的去名条款与 E-03…E-07 | 不把 P-025 的 `类型:值` 前缀纳入签名 |
| AST：`FnDef` 去掉 `name`，增加可机械比较的形状字段 | 不新增 `fn` 关键字，不恢复字符串名字 |
| Parser：`@` 后直接 `verb_call`；旧 `@ "name"` 报解析错误 | 不做兼容层、不做双读 |
| Loader：形状键、同形冲突、未声明、二义、arity、默认值、状语/介词匹配 | 不做最近匹配、优先级或运行时重载 |
| Eval：按参数位绑定；重复参数位值必须相等 | 不引入空位语法或隐式补位 |
| Python 与 CT 同步；语料、样例、编辑器高亮同步 | 不改动词表、介宾语义、尾随块语义、宿主能力 |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `docs/RILL-0.1.0.md` | 去名条款、EBNF、示例、错误表 |
| `src/rill/ast.py`、`src/rill/parser.py` | Python AST 与解析 |
| `src/rill/loader.py` | Python 形状表与加载期错误 |
| `src/rill/eval_fn.py` | Python 函数调用与绑定 |
| `ct/src/parser/parser.h.ct`、`ct/src/loader/loader.h.ct`、`ct/src/eval/eval.h.ct` | CT 对等实现 |
| `tests/phase22/` | 红证、正负例、golden 断言 |
| `testdata/0.1.0/` | fn 相关 fixture/golden 迁移 |
| `examples/tour/09-fn.ri`、`examples/tour/09-fn.md` | 可运行样例与说明 |
| `examples/phase22/` | 本 phase 专属可运行样例与 `expected.out` |
| `editors/vscode/syntaxes/rill.tmLanguage.json` | 高亮改为 `@ <verb>` |
| `CHANGELOG.md`、`docs/reviews/closeout-22.md` | 破坏性变更记录与收口对照 |

## 3. 任务清单

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-22-T1 | `docs/RILL-0.1.0.md` 去名条款与错误表 | `docs(spec): PH-22-T1 函数签名去名` | `git revert <sha>` | `bash -c '! grep -q "按名字精确匹配" docs/RILL-0.1.0.md && grep -q "E-03" docs/RILL-0.1.0.md && tools/check.sh g4'` | M | E-1,E-13 |
| PH-22-T2 | `src/rill/ast.py`、`src/rill/parser.py` 形状 AST 与解析 | `feat(fn): PH-22-T2 解析去名形状` | `git revert <sha>` | `python3 -m pytest tests/phase22/test_fn_shape_parse.py -q` | M | E-2,E-3,E-14,E-27 |
| PH-22-T3 | `src/rill/loader.py` 形状表与加载期错误 | `feat(fn): PH-22-T3 形状表与加载期错误` | `git revert <sha>` | `python3 -m pytest tests/phase22/test_fn_shape_load.py -q` | M | E-4,E-5,E-6,E-7,E-8,E-9,E-10,E-12,E-15,E-26 |
| PH-22-T4 | `src/rill/eval_fn.py` 绑定与重复参数冲突 | `feat(fn): PH-22-T4 绑定与重复参数冲突` | `git revert <sha>` | `python3 -m pytest tests/phase22/test_fn_shape_eval.py -q` | M | E-11,E-16 |
| PH-22-T5 | `ct/src/parser`、`ct/src/loader`、`ct/src/eval` 对等实现 | `feat(ct): PH-22-T5 函数形状对拍` | `git revert <sha>` | `python3 tools/diff/diff.py --layer ast --filter fn && python3 tools/diff/diff.py --layer error --filter fn && python3 tools/diff/diff.py --layer eval --filter fn` | M | E-17,E-18,E-19 |
| PH-22-T6 | `testdata/0.1.0/`、`examples/tour/09-fn.ri`、`examples/tour/09-fn.md` 语料迁移 | `test(fn): PH-22-T6 语料去名迁移` | `git revert <sha>` | `bash tools/check-0.1.0.sh --all && python3 tools/diff/diff.py --all --filter fn` | M | E-20,E-21,E-22 |
| PH-22-T7 | `editors/vscode/syntaxes/rill.tmLanguage.json` 高亮 | `docs(fn): PH-22-T7 编辑器语法去名` | `git revert <sha>` | `python3 -m pytest tests/phase22/test_editor_grammar.py -q` | S | E-23 |
| PH-22-T8 | `CHANGELOG.md`、`docs/reviews/closeout-22.md` | `docs(fn): PH-22-T8 收口对照与变更记录` | `git revert <sha>` | `test -s docs/reviews/closeout-22.md && tools/check.sh all` | S | E-24,E-25,E-28 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结。任务清单每项可独立验收（T-6）。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | 规范正文去掉“函数名是字符串、按名字精确匹配”；§三/§4.18/§4.20/§五/§六/§七/§八 同步，错误表含 E-03…E-07 | `bash -c '! grep -q "按名字精确匹配" docs/RILL-0.1.0.md'` 退出 0；`grep -c "E-0[3-7]" docs/RILL-0.1.0.md` ≥ 5 |
| E-2 | `@` 后直接 `verb_call` 可解析；`@ "name"` 解析期报 E-07，位置在字符串 token | `test_fn_shape_parse.py` 正例 5 条、负例 4 条全绿 |
| E-3 | `FnDef` 无 `name` 字段；形状字段只含动词、主语身份、位身份、常量值、状语名集合、介词名与顺序；`\|>` 之后不入签名 | `.sexpr` golden 逐字相等；字段白名单断言 |
| E-4 | 参数变量名、默认值、状语值不进形状键；`'ok'`/`"ok"`/`ok` 视为同一常量值 | 两个仅差变量名/默认值/状语值的定义 → E-03 |
| E-5 | 同一 `//fn{}` 内形状相同 → E-03，指向后一个定义 span，Hint 给两份形状与首个定义行 | 负例 `.err.json` 含 `E-03`、`line`、`col`、`hint` |
| E-6 | 调用形状 0 候选 → E-04，位置在 `@` 调用 span，Hint 列同动词已定义形状，错误串不含名字 | 负例 `.err.json` 字段断言 |
| E-7 | 多候选 → E-05，列出全部候选与定义行（防御宿主注入/合并绕过同块检查） | 负例 `.err.json` 含候选行号数组 |
| E-8 | 参数位个数按形状绑定；仅尾部可选位可省略；中间跳过或个数不符 → `arity`；默认值按位生效 | 正例 3 条、负例 3 条全绿 |
| E-9 | 状语按名称集合匹配，顺序无关、重复不计、值不比较；多/少一个状语名 → E-04 | 正例 2 条、负例 2 条全绿 |
| E-10 | 介词按名称与顺序精确匹配；`[into]/[ok]/[error]/[results]` 不是介宾、不进签名 | 正例 2 条、负例 2 条全绿 |
| E-11 | 同一参数位在模板多处出现时，调用每个位都要写值且相等；不等 → E-06；无空位语法 | 正例 2 条、负例 1 条全绿 |
| E-12 | 直接 `<verb>` 工具调用行为不变；函数调用仍必须带 `@` | 原有 run fixture 全绿；`<send>` 与 `@ <send>` 分表断言 |
| E-13 | 旧 `@ "name"` 不得回退到名字查找；一律解析期 E-07 | 负例 3 条（定义/调用/混合）全绿 |
| E-14 | Python parse golden：5 正例 `.sexpr`、4 负例 `.err.json` | `test_fn_shape_parse.py -q` 退出 0 |
| E-15 | Python loader 正负例：同形冲突、未声明、二义、arity、默认值、状语、介词各至少 1 条 | `test_fn_shape_load.py -q` 退出 0 |
| E-16 | Python eval：重复参数绑定、默认值、尾随块、返回值各至少 1 条 | `test_fn_shape_eval.py -q` 退出 0 |
| E-17 | CT 与 Python 的 fn AST 对拍 0 差异 | `tools/diff/diff.py --layer ast --filter fn` 退出 0 |
| E-18 | CT 与 Python 的 fn 错误对拍 0 差异 | `tools/diff/diff.py --layer error --filter fn` 退出 0 |
| E-19 | CT 与 Python 的 fn 求值对拍 0 差异 | `tools/diff/diff.py --layer eval --filter fn` 退出 0 |
| E-20 | `examples/`、`testdata/0.1.0/`、`tests/` 中不再有 `@ "` 旧形态（历史决策文档除外） | `bash -c '! grep -Rq "@ \"" examples testdata/0.1.0 tests'` 退出 0 |
| E-21 | `examples/tour/09-fn.ri` 可运行；`09-fn.md` 输出与 `expected.out` 一致；`examples/phase22/` 样例纳入真实门禁 | `bash tools/check-0.1.0.sh --all` 退出 0 |
| E-22 | fn 相关 golden 变更全部登记 `golden-change:`，不得静默改 golden | `docs/reviews/diff/registry.md` 有对应条目；`git diff` 可追溯 |
| E-23 | 编辑器语法匹配 `@ <verb>`，不再匹配 `@ "name"`；JSON 合法 | `test_editor_grammar.py -q` 退出 0 |
| E-24 | `tools/check.sh all`、`tools/check-0.1.0.sh --all`、`tools/diff/diff.py --all` 全绿；0 未解释差异 | 三条命令退出 0；收口对照表贴原始输出 |
| E-25 | 任务清单每项可独立验收（T-6）；收口对照表逐项贴 verify 输出 | `docs/reviews/closeout-22.md` 逐行对应 T1…T8 |
| E-26 | P-025 未裁定前，签名键不含 `类型:值` 前缀；类型前缀不得改变形状匹配 | 负例：仅类型前缀不同的两个定义仍同形 → E-03 |
| E-27 | P-026 未裁定前，本卡不做兼容层；旧脚本一律 E-07 并给迁移提示 | 负例 `.err.json` 含迁移 Hint；无 `@ "name"` 回退路径 |
| E-28 | 收口记录破坏性变更；`version-minor=22`；实际 bump 按 §9 裁定在收口提交内完成 | `CHANGELOG.md` 与 `closeout-22.md` 同条目；`git show` 版本落点一致 |

## 5. 样例计划

| 样例 | 内容 | 门禁 |
| --- | --- | --- |
| `examples/phase22/shape-fn.ri` | 两个不同形状的函数 + 一个同形冲突负例（负例放 `tests/phase22/negative/`） | `tests/phase22/run.sh` 调用 `ct/bin/rill run` 与 `python3 -m rill run`，比对 `expected.out` |
| `examples/tour/09-fn.ri` | 迁移后的三处定义/调用 | `bash tools/check-0.1.0.sh --all` |
| `testdata/0.1.0/expected/ast/fn-shape/` | 5 份 `.sexpr` | `tools/diff/diff.py --layer ast --filter fn` |
| `testdata/0.1.0/negative/fn-shape/` | 4 份 `.err.json` | `tools/diff/diff.py --layer error --filter fn` |

golden 格式沿用 10 卷/现有 `testdata/0.1.0`：AST 为稳定 `sexpr`，错误为
`{"error_kind","line","col","message","hint"}`；新增字段先写进 `tests/phase22/README.md`，
不另造格式。

## 6. 红证与提交节奏

- 每个实现任务先提交 `test(fn): PH-22-T<n> 红`（只含夹具、golden 与红证），再提交
  `feat(fn): PH-22-T<n> ...`；红证正文含 `baseline: <sha>`、命令、原始输出、退出码。
- T1/T8 为纯文档/收口任务，写 `no-test: 纯文档或收口记录，无可执行行为`，由 VERIFY 签字。
- 每项任务一次提交、一个路径集合、可单独 `git revert`；不得把 Python、CT、语料混在一个提交。
- 首个实现提交后 §3/§4 冻结；要改只能关闭 PH-22 另开。

## 7. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | D-022 的签名构成表（§判决 1）；Python 0.12.0 的 parser/loader/eval；CT 的 parser/loader/eval；`tools/diff/diff.py`；`testdata/0.1.0`。 |
| 风险 1 | 形状键混入参数名/默认值/状语值：早期探针 `@ <send> $a` 与 `@ <send> $b` 必须同形 E-03；`@ <send> 'ok'` 与 `@ <send> "ok"` 必须同形。 |
| 风险 2 | 旧语料残留：早期探针 `@ "announce" 'RILL'` 必须 E-07；`grep -R '@ "'` 在 T6 前先清零 `examples/`/`tests/`。 |
| 风险 3 | CT 三处漂移：T5 前先用 `tools/diff/diff.py --layer ast --filter fn` 建红，再逐层转绿；不得只改 Python。 |
| 风险 4 | P-025/P-026 被顺手裁定：P-025 只做“不进签名”的负例，P-026 只做“旧形态 E-07”，对外迁移与版本口径另开。 |

## 8. 退出条件与 Phase 23 前提

- **收口状态**：E-1…E-28 全绿；T1…T8 每项有 verify 原始输出；`tools/check.sh all` 与
  `tools/check-0.1.0.sh --all` 退出 0；`docs/reviews/closeout-22.md` 完成。
- **判定人**：VERIFY 逐条认定；REVIEW 复核；用户签收口记录与 §9 的版本偏离选择。
- **Phase 23 前提**：PH-22 收口 + 版本偏离方式已选定并写入 `AGENTS.md` 0.3；P-025/P-026
  的后续项另开卡，不并入 PH-22。

## 9. 版本偏离（待用户三选一，本卡不自行收敛）

当前 `version-minor=22`，产品版本 `0.12.0`，落差 `d = 22 - 12 = 10`。按 6.7/AGENTS.md
0.3 登记；以下三选一，选定后写入 `AGENTS.md` 并由用户签字：

```
deviation: PH-22-version
  日期: 2026-11-15
  条款: 6.7 V-1 / G1 g1-version
  现状: PH-22，产品 0.12.0，d=10
  理由: PH-13…PH-21 的 CT 重写阶段未按 V-1 逐 phase 移动产品版本，形成存量落差
  收敛: 待用户从 A/B/C 三选一
  签字: 待用户
```

| 方式 | 写法 | 后果 |
| --- | --- | --- |
| A 一次性补号 | PH-22 收口时把 MINOR 一次补到 22（`0.22.0`），在同一条 deviation 里显式豁免“不许多跳” | 一次跳 10 个 MINOR；CHANGELOG 出现空段；tag `v0.22.0`；这是唯一能让 PH-22 收口真正体现 minor bump 的方式 |
| B 永久偏移 | `偏移: 10`，PH-22 收口 `MINOR = 22 - 10 = 12`（`0.12.0`） | 机械可查，但本次收口没有可见 minor bump；以后每个 phase 都按偏移换算 |
| C 将来重编号 | 保持 `0.12.x`，到 `PH-<m>` 时按重新编号处理（一次跳号） | PH-22 收口仍是 `0.12.0`；届时仍要一次跳号与 CHANGELOG 空段 |

## 10. 卡内裁定与未决

| 编号 | 事项 | 裁定/去向 |
| --- | --- | --- |
| C-1 | 旧 `@ "name"` 的处理 | 本卡实现一律解析期 E-07，不做兼容层；对外迁移策略归 P-026 |
| C-2 | `类型:值` 前缀是否进签名 | P-025 未裁定；本卡只断言“不进签名”，不实现类型匹配 |
| C-3 | 错误码 E-03…E-07 | 采用 D-022 的建议码；若 T1 规范正文改成别的码，以正文为准并同步 golden |
| C-4 | CT 对等范围 | 以 PH-21 的 fn fixture 为基线；PH-21 未收口时 T5 可先建红，但 E-17…E-19 不判绿 |
| U-1 | P-026 的发布版本（0.1.2/0.2.0） | 不阻塞本卡；由用户另裁，§9 只处理产品 `MAJOR.MINOR.PATCH` |
