# PH-16 收口对照表

> 基线 `e0e9505`；本相实现提交 `8737124`（T1–T4）、`3bb6ab8`（T5 代码）、
> `a9be167`（T5 报告）。只本地提交，不 push、不打 tag。
> 规范 1.9.0；CT 轨道产品版本 `0.16.0`（卡片 §6 目标）。Python 参考实现版本落点
> `src/rill/__init__.py#__version__` 仍为 `0.12.0`：边界禁止改 `src/rill/`，`g8-version`
> 因此仍显示 0.12.0（不是遗漏）。`docs/RILL-0.1.0.md` 未改。
> 差异报告见 `docs/reviews/diff/PH-16.md`；登记表 `docs/reviews/diff/registry.md` 保持空表。
> 施工路线：用户裁定沿用 **A（单文件 `ctc` + 直接消费 JSON AST）**。

## 1. 判定

**GO（A 路线），E-5 不计通过。** `positive/run/{segment,into,pipe,call}` **10/10 PASS**；
eval 层对拍 10/10、0 差异；token / AST / error 三层回归仍 0 差异。`ct/src/*.h.ct` /
`*.m.ct` 八件交付物、`Value` tagged union 与 arena、`Bytes`/`Opaque` 单测受单文件路线与
无注入通道限制未产出，逐条写在 §4、§6，**不冒充通过**。

## 2. 退出判据

| ID | 条件 | 原始证据 | 结果 |
| --- | --- | --- | --- |
| E-1 | 10 个 run 用例通过 | `compliance: 10 passed, 0 failed`；§3 T1–T4 | PASS |
| E-2 | `[ok]` 只看 `ok`，空串成功仍触发 | 实现只读 `EOut.ok`，无 truthy 分支；`success-ok`/`success-plain` PASS | PASS（见 §6 边界） |
| E-3 | `$` 指代可观察；`host_meta` 不进入 `$` | `into/order` value 精确相等；`call/defaults` 的 `$name` 绑定不报错 | PASS（见 §6 边界） |
| E-4 | 管道下游只收 value；上游失败不回溯 | `pipe/downstream`、`pipe/failure-stops` PASS | PASS |
| E-5 | `Bytes`/`Opaque` 可透传，不被 truthy 误判 | 无 tagged union、无 fake 注入通道、无 value 单测 | **不计通过**（§6） |
| E-6 | eval 层对拍 10/10，0 差异 | `sources=10 ok=10 diffs=0` | PASS |
| E-7 | 每个任务可独立验收（T-6） | §3 五条 verify 均有命令与原始输出 | PASS |

## 3. 任务 verify

| 任务 | verify（仓库根执行） | 原始输出 | 退出码 |
| --- | --- | --- | --- |
| PH-16-T1 | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --show positive/run/segment/success-plain` | `exit: 0`；`ok=true`；`value="host: a\n"` | 0 |
| PH-16-T2 | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --show positive/run/into/order` | `exit: 0`；`value="host: a\n"`；`host_meta={}` | 0 |
| PH-16-T3 | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --show positive/run/pipe/downstream` | `exit: 0`；`ok=true`；`value=null` | 0 |
| PH-16-T4 | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --show positive/run/call/defaults` | `exit: 0`；`ok=true`；`value=null` | 0 |
| PH-16-T5 | `python3 tools/diff/diff.py --layer eval` | `sources=10 ok=10 diagnostics=0 diffs=0` | 0 |

T1 原始信封：

```json
{"ok":true,"value":"host: a\n","error":null,"host_meta":{},
 "host":{"profile":"fakes","principal":{"kind":"test-transport","name":"--fakes"}}}
```

T1–T4 合并为一次实现提交 `8737124`：求值器、fake 派发与最小 `//fn` 绑定共用一个
`run` 入口，拆开会得到不可独立编译的中间态；五条 verify 仍可分别执行。

## 4. 与卡面偏差

| # | 卡面要求 | 实际做法 | 为什么不按卡面 | 影响哪些判据 |
| --- | --- | --- | --- | --- |
| 1 | §2 产出 `ct/src/value.h.ct`、`value.m.ct`、`eval.h.ct`、`eval.m.ct`、`pipe.h.ct`、`pipe.m.ct`、`verbs.h.ct`、`verbs.m.ct` 八件 | 八件均不产出；求值器作为 `ct/rill_ct.ct` 内的 evaluator 分区 | 用户裁定 A：保持单文件 `ctc`；多单元前置未立卡（PH-14 §7），`ct build` 四条阻塞未解（PH-14 §6） | T1–T4 交付物路径、E-5；不影响 E-1/E-2/E-4/E-6 |
| 2 | §1 把 `//fn` 划给 PH-17 | 实现最小 `//fn`：按位置绑定、尾部默认值、返回最后一条段输出 | §3 T4 与 E-1/E-3 把 `call/defaults`、`call/return-last` 列为本相用例；不做就无法满足 10 例。只做调用所需子集，不含控制流与递归扩展 | E-1、E-3、T4 |
| 3 | §2 `Value` tagged union + arena + retain/release | 直接消费解析期 JSON 树（`JVal`），进程即退，不回收 | A 路线没有跨单元 `Value` 头；JSON 树已含 string/number/array/object/null/bool，再建 tagged union 会复制一套所有权。没有释放就没有 use-after-free | E-5、风险 1；不影响 10 例结果 |
| 4 | §2 `verbs.m.ct` “10 个固有动词实现” | 只做 fake 表派发：按动词名取 `queue`/`default`，不实现真实进程/文件/网络 | §1 明写“固有动词用 fake 表”；真实宿主是 PH-19/PH-20 | E-1（fake 下通过）、E-5 |
| 5 | §3 每项一次实现提交、可单独回滚 | T1–T4 合并为 `8737124`；T5 代码与报告分开 | 同 PH-15：单文件路线下四件交付物是同一 `run` 入口的分区，无法拆出可编译中间态 | 回滚粒度；五条 verify 仍独立 |
| 6 | 以 `ct build` 多单元施工 | 仍用 `bash ct/build.sh`（`ctc` 单文件 + `cc`） | 沿用 PH-14 收口 §6 四条阻塞：前向 typedef、`impl` 尾 `;`、续行宏、>159 字符宏静默截断 | E-5 与多单元；其余判据不受影响 |
| 7 | `Bytes`/`Opaque` 的 value 单测 + run 用例 | 未实现、未测试 | `JVal` 无对应 tag，fake JSON 也无法表达 `Bytes`/`Opaque`；没有观测面就不伪造单测 | **E-5 不计通过** |

**多单元化前置**指回 `docs/reviews/closeout-14.md` §7 的待立卡。它阻塞的是“按卡面原文施工”
（§2 八件交付物、`Value`/arena、E-5 的完整 `Value` 语义），**不是本相 10 例功能**：
10/10 与 eval 层 0 差异均已在 A 路线下交付。

## 5. 允许变化 / 不允许变化

### 5.1 本相允许且实际发生的变化

| 路径 | 变化 | 理由 |
| --- | --- | --- |
| `ct/rill_ct.ct` | 新增 `run` 子命令、JSON 读取、求值器；宏化/合并腾函数槽 | 卡片 T1–T4 |
| `tools/diff/diff.py` | 新增 `--layer eval` | 卡片 T5 |
| `ct/README.md` | CLI 补 `run` 与退出码 1；删掉过时的“run 没做” | 实现已改变可观察面 |
| `docs/reviews/diff/PH-16.md` | 新增 | 卡片 T5 |
| `docs/reviews/closeout-16.md` | 新增本文件 | 卡片 §6 |

### 5.2 本相不允许且未发生的变化

| 路径 / 行为 | 判定证据 |
| --- | --- |
| `src/rill/**`（Python 参考实现） | `git diff --stat e0e9505..HEAD -- src/rill` 为空 |
| `testdata/0.1.0/**`（fixture、golden） | `git diff --stat` 为空 |
| `docs/RILL-0.1.0.md` | `git diff --stat` 为空 |
| `tools/checks/**`（门禁脚本） | `git diff --stat` 为空；g8 白名单未改 |
| PH-13/14/15 已验证的 golden 与判据 | 未改；token 82、AST 82、error 26 仍 0 差异 |
| 警告降级 / 用 warning 凑绿 | 未做；`W-01` 行为未变 |
| push / tag | 未执行；`git tag --points-at HEAD` 为空 |

## 6. 未满足项（不计通过）

| ID | 条件 | 实测 | 原因 | 归属 |
| --- | --- | --- | --- | --- |
| E-5 | `Bytes`/`Opaque` 可透传，不被 truthy 误判；value 单测 + run 用例 | 无 tagged union、无注入通道、无单测 | 单文件路线的 `JVal` 只有 JSON 六类；fake JSON 无法表达 `Bytes`/`Opaque` | 多单元化后的 `value` 卡，或宿主卡 |

边界说明（不改判据，只标证据面）：

- **E-2**：`[ok]` 只读 `EOut.ok`，全文件没有 truthy 判断；但 10 例里没有“空串成功”的
  独立 fixture，空串子情形靠构造保证。
- **E-3**：`into/order` 的 `$` 与 `call/defaults` 的 `$name` 绑定有观测；`.field` 与
  `host_meta` 隔离没有可观测 fixture（fake 不回声参数），属于 PH-19/PH-20 的观测面。

## 7. 函数槽预算与宏化代价

`ctc` 上限 64（含 `main` 与 `impl` 方法）。本相开始前 62 个定义 + 8 个前向声明 + 1 个
`impl`；收口后 **58 个定义 + 7 个前向声明 + 1 个 `impl`**。用空函数实测：当前再加 3 个
仍可编译，加 4 个报 `too many functions (max 64)`，即 **61/64，余 3 槽**。

新增求值函数 7 个：`json_parse`、`var_lookup`、`eval_value`、`apply_tail`、`run_block`、
`eval_stmt`、`cmd_run`。

为腾位置做的改动：

| 改动 | 腾出 | 牺牲 |
| --- | --- | --- |
| `jpush`、`jget_str`、`lx_map_unclosed`、`p_take` 改宏 | 4 | 无独立栈帧与参数类型检查；`jget_str` 重复查键（最多 3 次）；`p_take` 重复求值 `p`（调用点都是局部 `Parser*`，无副作用） |
| `lx_dollar`、`lx_field` 并入 `lx_normal`；`load_verb_known` 并入 `load_scan`；`maps_find` 并入 3 个调用点；`p_parse_break` 并入 `p_parse_statement` | 6 | 函数边界消失，单函数变长；行为由 token/AST/error 三层对拍兜底 |
| `var_get` + `var_set` 合并为 `var_lookup`；`p_parse_adverb` + `p_parse_prep_phrase` 并入 `p_parse_verb_call` | 3 | `var_lookup` 用 `set` 分支；`p_parse_verb_call` 从 ~40 行涨到 ~90 行 |
| `eval_stmt` 内联 fake 派发与参数绑定 | 2 | `eval_stmt` 约 150 行，是“为省槽合并”的单点；已在代码注释与本表说明，没有把校验逻辑压进巨型函数 |

## 8. 全量计数与复跑

```text
run 目标 10 例      10/10 PASS（segment 4 + into 2 + pipe 2 + call 2）
eval 层对拍         10 源、0 差异（exit 0）
token 层回归        82 源：73 成功 + 9 诊断，0 差异
AST 层回归          82 源：60 成功 + 22 诊断，0 差异
error 层回归        26 源：26 诊断，0 差异
load 负例           7/7 PASS；W-01 1/1 PASS；positive check 1/1 PASS
ct/test.sh          12 + 23 + 19 全 PASS
函数定义            62 → 58（含 main）；ctc 计数 61/64，余 3 槽
Python / golden     未改；registry 空表
```

复跑：

```console
$ bash ct/build.sh
built /Users/samxx/trae-ws/rill-dsl/ct/bin/rill_ct
$ python3 tools/diff/diff.py --layer eval
   sources=10 ok=10 diagnostics=0 diffs=0
   RESULT: PASS
== total diffs: 0
```

## 9. 门禁

```console
$ bash tools/check.sh all
...
== overall: PASS ==
```

末行 `== overall: PASS ==`。上一相遗留的 `g8-phase-freeze` 红仍由
`tools/checks/phase-freeze-errata.json` 的单条白名单处理；本相未改门禁脚本、未开通用豁免。
