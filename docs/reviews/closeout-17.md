# PH-17 收口：CT 控制流与函数（P5）

> 卡面 `docs/phases/PH-17/card.md`；差异报告 `docs/reviews/diff/PH-17.md`；
> 多单元迁移卡 `docs/phases/pending/ct-multiunit.md`。只本地提交，未 push、未打 tag。

## 1. 结论

GO。9 个 control/parallel run 用例与函数用例全部通过，eval 层 19/19、0 未解释差异；
token 82 / ast 82 / error 26 三层回归仍为 0 差异；`ct/test.sh` 与 `tools/check.sh all` 通过。

本相第一件事按用户要求做了路线裁决：**乙（`ct build` 多单元）**，立卡并迁移完成，
再在 `ct/src/eval/eval.h.ct` 内实现控制流/并行/函数。理由与实测见迁移卡 §0。

## 2. 退出判据（E）

| ID | 条件 | 结果 | 证据 |
| --- | --- | --- | --- |
| E-1 | `positive/run/{control,parallel}` 9 例通过 | 通过 | `check-0.1.0.sh` 逐例 rc=0；eval 层 19/19 |
| E-2 | `if` 用 truthy，`[ok]` 用 `ok` | 通过 | `control/if-subject` → `"on"`；`segment/success-ok` 空串成功仍触发 |
| E-3 | each 空数组/null 0 次、非数组 1 次；某轮失败后继续 | 通过 | 见 §3：三态逐条对拍 Python，另加 3 个探针 |
| E-4 | break 只中断当前场域；带值可捕捉 | 通过 | `control/break-pipe` → `"halt"`；`pipe-segment-error` 顶层 break → `{"format":"yaml"}` |
| E-5 | parallel 分支三态与 `[results]` 顺序正确 | 通过 | `three-state` → `["A",null,null,"E_D"]` / `B_FAIL`；`results-array` → `["A","B"]` |
| E-6 | 参数去重、默认值仅尾部、返回最后一条语句 | 通过 | `call/defaults`、`call/return-last` |
| E-7 | eval 层 19/19，0 未解释差异 | 通过 | `--layer eval`：`sources=19 ok=19 diffs=0` |
| E-8 | 每项可独立验收（T-6） | 通过 | §4 逐项贴原始输出 |

PH-16 遗留的 **E-5（`Bytes`/`Opaque` 单测）仍未通过**，本相不记通过、不挪判据。

## 3. E-3 的三态证据

fixture 只覆盖数组形态，另用探针补齐 null / 空数组 / 非数组（Python 与 CT 逐字段一致）：

| 源 | CT 输出 | Python 输出 |
| --- | --- | --- |
| `<read>` default `null` | `{"ok":false,"value":null,"error":"RILL DSL ERROR",...}` rc=1 | 同左 rc=1 |
| `<search>` default `[]` | `{"ok":true,"value":[],...}` rc=0 | 同左 rc=0 |
| `<read>` default `"only"` | `{"ok":true,"value":[null],...}` rc=0 | 同左 rc=0 |

「某轮失败后继续」：`each-level-error` 三轮回合里前两轮失败、`[error]` 收到首个失败串并接回
结果；但两轮失败串相同，输出上无法用哨兵区分是哪一轮继续的。可验证的是「没有在首轮失败处
就把 each 收口」与「与 Python 逐字段一致」，不是逐轮轨迹。**这条观测局限记在这里，不当作
已单独验证**。

## 4. 任务逐项 verify（原始输出）

| 任务 | verify | 结果 |
| --- | --- | --- |
| T1 if | `... --show positive/run/control/if-subject` | `PASS`（rc=0）；CT `{"ok":true,"value":"on",...}` |
| T2 each | `... --show positive/run/control/each-round-failure` | `PASS`（rc=0）；CT `exit : 1` + `{"ok":false,"error":"RILL DSL ERROR"}` |
| T3 break | `... --show positive/run/control/break-pipe` | `PASS`；CT `{"ok":true,"value":"halt"}` |
| T4 parallel | `... --show positive/run/parallel/three-state` | `PASS`；CT `{"ok":false,"value":["A",null,null,"E_D"],"error":"B_FAIL"}` |
| T5 fn | `... --show positive/run/call/return-last` | `PASS`；CT `{"ok":true,"value":null}` |
| T6 diff | `python3 tools/diff/diff.py --layer eval` | `sources=19 ok=19 diffs=0`，`== total diffs: 0` |

## 5. 与卡面偏差

| # | 卡面 | 实际 | 影响 |
| --- | --- | --- | --- |
| 1 | 直接在单文件扩控制流 | 先按路线乙迁移多单元（独立提交 `feat(ct): 多单元化迁移`） | 判据不变；见迁移卡 |
| 2 | 交付 `eval_control.m.ct` 等 | `.m.ct` 是映射单元，不能定义函数；改为 `ct/src/eval/eval.h.ct` 三个分区 | 已在冻结点前修订卡面 §2/§3 |
| 3 | T1–T5 各自一次实现提交 | 求值单元一次重写，T1–T5 合并为一次实现提交 | 按功能切 hunk 会产生不可编译的中间态；六条 verify 仍逐条独立可跑 |
| 4 | （未写）`run` 的 value 输出 | 改为不依赖 `ok` 直接输出 `value` | Python 在 `ok=false` 时仍带值（`three-state` 的数组）；PH-16 语料没暴露 |
| 5 | （未写）break 实现方式 | `EOut.is_break` + `break_target` 逐层早退；program 层用 `eval_set_var` 写目标变量 | C 无异常，等价于 Python 的 `BreakSignal` |
| 6 | 通用 break 值 | 只支持字符串作为错误串 | 语料内 break 值都是字符串；非字符串记为本层局限 |
| 7 | eval 层 PH-16 口径 10 例 | 扩到 19 例，并修 `case_opts` 目录拼接 | 原实现读不到 `case.json`，PH-16 的 10 例恰好都用默认 fakes 才没暴露 |

## 6. 函数与单元

| 单元 | 函数数（含 static） | 上限 |
| --- | --- | --- |
| `common.h.ct` | 29 | 256 |
| `lexer.h.ct` | 13 | 256 |
| `parser.h.ct` | 32 | 256 |
| `loader.h.ct` | 2 | 256 |
| `eval.h.ct` | 22 | 256 |
| `cli.h.ct` | 4 | 256 |
| `main.ct` | 1 | 256 |

合计 103 个定义，最忙的 parser 32/256。单文件 `ctc` 时代的 61/64 不再是约束。

## 7. 允许与不允许的改动

允许：`ct/src/**` 新增/修改；`ct/build.sh` 换 `ct build`；`ct/README.md` 口径；
`tools/diff/diff.py` 的 eval 语料与 case 选项；本相新增文档；删除单文件实现（独立提交）。

不允许且未做：改 `testdata/` golden；改 `src/rill/` Python 参考实现；改 harness 协议；
放宽任何既有判据；把 `Bytes`/`Opaque` 或无 fixture 的能力记成通过。

## 8. 提交与门禁

- `feat(ct): 多单元化迁移，构建切到 ct build`
- `feat(ct): PH-17 控制流与函数求值`
- `docs(diff): PH-17 差异报告`
- `docs(review): PH-17 收口`

单文件 `ct/rill_ct.ct` **保留**（PH-18 决定）：冻结为参考实现，不参与构建，
`ct/build.sh` 只走 `ct/src/main.ct`。迁移卡 M-5 已按此结论更新。

门禁末行：

```
== overall: PASS ==
```
