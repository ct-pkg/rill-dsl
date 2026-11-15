# 待立卡：CT 多单元化（PH-14 §7 触发）

> 身份：不占相号。触发条件「再次撞上单文件 64 函数上限」在 PH-17 成立
> （`ctc` 实测 61/64，只剩 3 槽，而 PH-17 需新增约 10–14 个函数）。
> 本卡由 PH-17 首件事执行，产物是 `ct/src/**` 多单元树 + `ct build` 构建。
> 上游登记：`docs/reviews/closeout-14.md` §7；体系：`docs/phases/README.md`。

## 0. 决策：路线乙（`ct build` 多单元）

两席对辩的结论与实测证据（`ct v0.44.1`，2026-11-15，探针在 `/tmp/ph17probe*`）：

| 项 | 甲：继续单文件挤 | 乙：`ct build` 多单元 |
| --- | --- | --- |
| 函数上限 | 64/文件，现有 61，剩 3 | 256/单元（258 函数实测 `too many functions in unit 'main.ct' (limit 256)`） |
| PH-17 需要 | if/each 三态/break/parallel/results/fn ≈ 10–14 个函数 | 分摊到 7 个单元，单单元 ≤ 30 |
| 代价 | 只能继续把逻辑内联进 `eval_stmt`（已 150 行），收口为 400+ 行不可单点验证的巨型函数；9 个 ≥161 字符宏在 `ctc` 下无槽改函数 | 一次性搬迁 ~2,700 行；`typedef`/宏/可见性要重做 |
| 对 PH-18..21 | PH-18 71 个 round-trip、PH-19/20 12+14 个 host fixture 无处置放 | 可继续加单元 |
| 对拍能力 | 二进制不变，但对拍对象会变成不可验证的巨型函数 | 二进制不变，层口径与用例全集不变 |

判定基准是「后面几相还能可验证地往前走，且不丢 700+ 用例对拍」：甲在 PH-17 就触顶，
乙把上限从 64 抬到 256 并让每个功能有独立单元。选乙。

## 1. 单元切分

`ct/src/main.ct` 是唯一入口；其余单元均为 `.h.ct`（接口 + 实现同文件，产物 `<base>.c` + `<base>.h`）。
依赖是 DAG（`ct build` 拒绝环：实测 `circular import`）。

| # | 单元 | 内容 | import | 产物 |
| --- | --- | --- | --- | --- |
| 1 | `ct/src/common/common.h.ct` | `Diag`/`fail`/`failv`、`g_diag`/`g_fail_jmp`、内存与字符类、`JVal`/JSON 构造与写出、`Emitter` trait 与 `StdoutEmitter` | — | `common.c` `common.h` |
| 2 | `ct/src/lexer/lexer.h.ct` | `TokKind`/`Token`/`Lexer`、关键字表、`lexer_run` 与 `lx_*` | common | `lexer.c` `lexer.h` |
| 3 | `ct/src/parser/parser.h.ct` | AST 构造宏、`Parser`、动词/介词冻结表、`p_*`（31 条产生式） | common, lexer | `parser.c` `parser.h` |
| 4 | `ct/src/loader/loader.h.ct` | `load_scan`（三遍）、`read_source` | common, lexer | `loader.c` `loader.h` |
| 5 | `ct/src/eval/eval.h.ct` | `EOut`/`EVar`/`Eval`、`json_parse`、`eval_value`/`apply_tail`/`run_block`/`eval_stmt`；PH-17 的 if/each/break/parallel/`[results]`/`//fn` 作为文件内分区追加 | common, parser(仅 JVal 语义), loader | `eval.c` `eval.h` |
| 6 | `ct/src/cli/cli.h.ct` | `cmd_tokenize`/`cmd_parse`/`cmd_check`/`cmd_run` | 全部 | `cli.c` `cli.h` |
| 7 | `ct/src/main.ct` | `main` + 用法 | cli, common | `main.c` |

分区理由：`eval_stmt` ↔ `run_block` 互相递归，拆开会触发 import 环；故求值全域留一个单元，
文件内按「核心 / 控制流 / 并行 / 函数」分区，函数上限 256 对后续几相仍有余量。

## 2. 跨单元可见性

- 类型：跨单元一律 `pub struct` / `pub enum`（`ct build` 导出到 `.h`）；单元内部仍可用 `typedef`。
- `pub struct` 里不放 `Map<...>` 字段（PH-46 缺陷，见 `docs/reviews/closeout-13.md` §6）；本实现用自建数组。
- 函数：跨单元调用必须 `pub`（`.h` 里出声明）；单元内部助手保持 `static`。跨单元名全局唯一，沿用现有前缀（`lx_`/`p_`/`eval_`/`cmd_`）。
- 全局量：`pub Diag g_diag;`、`pub jmp_buf g_fail_jmp;` 定义在 `common.h.ct`，头里 `#include <setjmp.h>`；实测跨单元可见。
- `setjmp` **必须留在 `main` 的栈帧**：把 `setjmp` 包进 `ctx_guard()` 会因帧已销毁而漏捕（实测输出 `no`）；`longjmp` 可跨单元。
- 宏不跨单元：`#define` 只在自身 `.c` 生效，需要的单元各自定义一份（保持逐份 ≤159 字符、单行）。
- 每单元函数体直接写在 `.h.ct`，不建 `_impl.ct`（同名 `.h.ct` + `.ct` 会争同一个 `<base>.c`，实测 duplicate symbol）。

## 3. `ct build` 四阻塞与绕法（逐条实测）

| # | PH-14 记录 | 实测 | 本卡绕法 |
| --- | --- | --- | --- |
| 1 | 前向 `typedef struct X X;` 被拒 | 结构体按序定义即可 | 头文件按依赖拓扑排序；跨单元用 import 顺序 |
| 2 | `impl` 后尾随 `;` 被拒 | 去掉 `;` 后可编 | 统一去掉 |
| 3 | 反斜杠续行 `#define` 不支持 | `#define ADD(a,b) \` → `expected a type` | 所有宏压成单行 |
| 4 | >159 字符宏被前端静默截断 | 200 字符宏在调用点报 `expected ')'` | 超长宏改函数（`is_keyword`/`p_is_stop_kind`/`p_is_word_kind`/`p_is_trailing_block`/`p_raw_len`/`p_reject_results`/`ast_parallel_stmt`/`ast_call_stmt`/`ast_each_stmt`） |

## 4. 对拍怎么跑（`ct build` 下）

```bash
./ct/build.sh        # ct build src/main.ct -I src --outdir <tmp> --cflags '-Wall -Wextra -O2' -o ct/bin/rill_ct
./ct/test.sh         # tokens 12 + ast 23 + tokenize/parse 19
python3 tools/diff/diff.py --layer token    # 82 源
python3 tools/diff/diff.py --layer ast      # 82 源
python3 tools/diff/diff.py --layer error    # negative 26 源
python3 tools/diff/diff.py --layer eval     # PH-17 起 19 例
```

对拍入口只认 `ct/bin/rill_ct` 这个二进制，`tools/diff/sut.ct.json`、harness、golden 均不改；
构建换编译器不改变协议。`ct/build.sh` 的 `-Wall -Wextra -O2` 与单文件时代一致，警告纪律不降。

## 5. PH-17 卡面路径修订

PH-17 §2 列出的 `eval_control.m.ct` / `eval_parallel.m.ct` / `eval_fn.m.ct` 无法实现：
`.m.ct` 是**映射单元**，规范明说「不产任何产物、只能被 import」，实测
`a .m.ct unit cannot define a function`。修订为：
`ct/src/eval/eval.h.ct` 一个单元内的三个分区（控制流 / 并行 / 函数），T1–T5 的 verify 与判据 E-1..E-8 不变。
修订发生在 PH-17 首个实现提交（冻结点）之前。

## 6. 验收判据

| ID | 条件 | 判定 |
| --- | --- | --- |
| M-1 | 多单元树构建成功，产物是 `ct/bin/rill_ct` | `./ct/build.sh` 退出 0 |
| M-2 | token 层 82 源、ast 层 82 源、error 层 26 源全部 0 差异 | 三个 `--layer` 命令退出 0 |
| M-3 | eval 层 PH-16 的 10 例先回到 0 差异 | `--layer eval` 退出 0（PH-17 再扩到 19） |
| M-4 | `ct/test.sh` 与 `tools/check.sh all` 通过 | 末行 PASS |
| M-5 | 单文件 `ct/rill_ct.ct` 保留，冻结为参考实现，不参与构建 | 已完成：`ct/build.sh` 只走 `ct/src/main.ct`，仓库内无任何构建/门禁路径引用该文件 |
| M-6 | 无判据被降级：E-3/E-5 等「缺能力」项仍如实记为未通过 | 收口对照表 |

> M-5 结论（PH-18 起）：**保留，冻结为参考实现，不参与构建**。依据：删除收益为零——
> 构建与门禁都不读它；留着还能作为「单文件 `ctc`」与「多单元 `ct build`」两条路的对照，
> 后续若多单元工具链出问题可直接对照单文件行为。不删即不产生删除提交，回滚只需回退迁移提交。

## 7. 回滚

迁移是一次提交；`git revert 89dcc3d` 即回到「单文件 + `ctc`」构建。
`ctc` 路径在单文件冻结后仍可手动跑通，但不参与任何构建或门禁。

## 6. PH-20 追加：构建分两段（调用点预算 1024）

`ct` 前端还有一张不按单元重置的表：**每次 build 累计的已解析调用点上限 1024**
（`selfhost/ct-ast/frontend/parse/Expr.h.ct:55` 的 `MAX_CALLS`，由
`record_call()` 累加；前置声明也算解析，所以 static 包装省不了槽）。
PH-19 收口时已用掉 927，Agent 宿主再需要约 500，一次编译必然超表。

`ct/build.sh` 因此分两段：

| 段 | 单元 | 产物 |
| --- | --- | --- |
| 语言核心 | `common` `lexer` `parser` `loader` `formatter` | `ct/build/librill_core.a` + `ct/build/gen-lib/*.h` |
| 宿主与入口 | `eval` `json` `exec` `host` `shell` `agent*` `cli` `main` | `ct/bin/rill_ct` |

边界规则（与 §2 的跨单元规则并列）：

- 宿主层单元**不再 import** 语言核心，改 `#include "bridge.h"`；`bridge.h` 手写
  `typedef struct JVal JVal;` 等 14 个别名（生成头的拼写是 `struct JVal`）。
- `pub` 全局量在 `--lib` 下不可导出，`g_diag`/`g_fail_jmp` 收成 `static`，
  `main` 用 `pub jmp_buf *fail_jmp_slot(void)` 取地址。
- 跨层不要用 trait 方法（`out.emit()` 会落到未初始化的 `__emitter_vptr`，实测段错误）；
  用自由函数入口。
- 构建产物 `ct/build/` 已在 `ct/.gitignore` 里。

实测与探针：`docs/reviews/diff/PH-20.md` §3、
`docs/planning/rill-0.1.0-ct-defect-workarounds.md` §8。
