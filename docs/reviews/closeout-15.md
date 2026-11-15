# PH-15 收口对照表

> 基线 `4a7cd7a`；本相实现提交 `9df0f4b`（T1/T2/T3）、`636b938`（T5 代码）、
> `57f3654`（T4）、`cc23108`（T5 报告）。只本地提交，不 push、不打 tag。
> 规范 1.9.0；CT 轨道产品版本 `0.15.0`（卡片 §6 目标）。Python 参考实现版本落点
> `src/rill/__init__.py#__version__` 仍为 `0.12.0`：边界禁止改 `src/rill/`，`g8-version`
> 因此仍显示 0.12.0（不是遗漏）。`docs/RILL-0.1.0.md` 未改。
> 差异报告见 `docs/reviews/diff/PH-15.md`；登记表 `docs/reviews/diff/registry.md` 保持空表。
> 施工路线：用户裁定 **A（单文件 `ctc` + token 流加载期校验）**。

## 1. 判定

**GO（A 路线），但 E-3 不计通过。** 加载期已端到端可用：7 个 `negative/load/**` 的
`stage/code/line/col` 与 Python 一致；`W-01` 提示且不阻断；error 层对拍 26/26、0 差异；
token / AST 两层回归仍为 0 差异。`ct/src/*.h.ct` / `*.m.ct` 四件交付物与四表只读接口
（E-3）受单文件路线限制未产出，逐条写在 §4、§6，**不冒充通过**。

## 2. 退出判据

| ID | 条件 | 原始证据 | 结果 |
| --- | --- | --- | --- |
| E-1 | 7 个 load 负例的错误码/行列与 Python 一致 | 7/7 PASS，逐条 `stage=load`；见 §3 T1 | PASS |
| E-2 | `W-01` 在 `each $f [in] xs` 触发且不阻断（退出 0） | `W-01` 已提示，`check` 退出 0；见 §3 T3 | PASS |
| E-3 | 四张表以只读接口暴露给 PH-16，复制/改写为硬错 | 未产出接口；单文件 `load_scan` 内部表 | **不计通过**（§6） |
| E-4 | error 层对拍 7/7，0 未解释差异 | `sources=26 diagnostics=26 diffs=0`；load 7 条在内 | PASS |
| E-5 | PH-46 绕法有实测命令、通过证据与代价 | workarounds 文档三节齐全；`bad` rc=1、指针/`void *` rc=0 | PASS |
| E-6 | CT 二进制不链接 Python | `test -z "$(otool -L ct/bin/rill_ct \| grep -i python)"` → rc=0 | PASS |
| E-7 | 任务清单每项可独立验收（T-6） | §3 五条 verify 均有命令与原始输出 | PASS |

E-6 写法沿用 PH-13/PH-14 的口径：只认命令退出码，不贴推断。`otool -L` 仅列
`/usr/lib/libSystem.B.dylib`。

## 3. 任务 verify

| 任务 | verify（仓库根执行） | 原始输出 | 退出码 |
| --- | --- | --- | --- |
| PH-15-T1 | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --kind error --bucket negative` | `compliance: 26 passed, 0 failed`；`VERDICT: PASS` | 0 |
| PH-15-T2 | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --show negative/load/unknown-function` | `exit : 2`；`load E-LOAD-FN-UNDECLARED@1:1` | 0 |
| PH-15-T3 | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --kind warning` | `1 passed, 0 failed`；`W-01 已提示，check 退出 0` | 0 |
| PH-15-T4 | `test -s docs/planning/rill-0.1.0-ct-defect-workarounds.md` | `rc=0`；命中点 / 实测 / 代价三节齐全 | 0 |
| PH-15-T5 | `python3 tools/diff/diff.py --layer error` | `sources=26 ok=0 diagnostics=26 diffs=0`；`total diffs: 0` | 0 |

T1 说明：卡片命令现在**不再连带红**——`--bucket negative --kind error` 的 26 条
（load 7 + parse 10 + tokenize 9）全部通过；其中 load 7 条的逐条 PASS 行见
`docs/reviews/diff/PH-15.md` §3。

T2 原始 JSON：

```json
{"error":{"code":"E-LOAD-FN-UNDECLARED","col":1,"line":1,
"message":"未声明的函数 'nope'；只能调用 //fn{} 内定义的名字","stage":"load"}}
```

T3 原始 JSON（退出 0）：

```json
{"warnings":[{"code":"W-01","col":14,"line":1,
"message":"裸词 `xs` 按字符串处理，若意图是变量请写 `$xs`"}]}
```

## 4. 与卡面偏差

| # | 卡面要求 | 实际做法 | 为什么不按卡面 | 影响哪些判据 |
| --- | --- | --- | --- | --- |
| 1 | §2 产出 `ct/src/tables.h.ct`、`tables.m.ct`、`loader.h.ct`、`loader.m.ct` | 四件均不产出；表与校验作为 `ct/rill_ct.ct` 内的 `LoadMap` / `LoadFn` / `load_scan` 分区 | 用户裁定 A：保持单文件 `ctc`；多单元前置未立卡（PH-14 §7） | T1/T2 交付物路径、E-3；不影响 E-1/E-2/E-4 |
| 2 | 加载期校验消费 PH-14 的 AST（并带 span） | 在 token 流上做三遍扫描，复用 lexer 的 `Token`；`parse` 只用于保持词法/语法阶段，加载期不改 AST | 用户裁定 A：token 自带 `line/col`，不为校验给 AST 加 `span`；也避免把表查询塞进 parser（卡片 §5 风险 4） | E-1 的实现方式、E-3；不影响判据结果 |
| 3 | E-1 的行列来自 AST span | 错误位置取 token：调用点取 `@`，动词调用取 VerbCall 起点（主语起点），map 重复取重复短词 token | 同 #2；token 的 `line/col` 与 AST span 在现有语法下同源同值（7/7 与 error 层 0 差异可证） | E-1 的位置来源说明；不影响 E-1 结果 |
| 4 | §2/§3 以 `ct build` 参与验收 | 仍用 `bash ct/build.sh`（`ctc` 单文件 + `cc`）；`ct build` 不参与本相验收 | 沿用 PH-14 收口 §6 的四条阻塞：前向 typedef、`impl` 尾 `;`、续行宏、>159 字符宏静默截断 | E-3 与多单元；E-1/E-2/E-4/E-5/E-6 不受影响 |
| 5 | §3 每项一次实现提交、可单独回滚 | T1/T2/T3 合并在 `9df0f4b` 一次提交；T4、T5 分开 | 三张表与调用绑定共用一个 `load_scan` 与一个 `check` 入口，拆开会得到不可独立编译的中间态 | 回滚粒度；五条 verify 仍可独立执行 |
| 6 | E-3 四表只读接口暴露给 PH-16 | 未产出接口 | 单文件无“单元间接口”可导出；需先完成多单元化 | **E-3 不计通过**；不影响其余判据 |

**多单元化前置**指回 `docs/reviews/closeout-14.md` §7 的**待立卡**（不占相号）。它现在
阻塞的是“按卡面原文施工”（§2 四件交付物、E-3 的导出接口），**不是本相功能**：加载期
校验、7 条负例、`W-01` 与 error 层对拍都已按 A 路线交付并通过。

## 5. 允许变化 / 不允许变化

### 5.1 本相允许且实际发生的变化

| 路径 | 变化 | 理由 |
| --- | --- | --- |
| `ct/rill_ct.ct` | 新增 `check` 子命令与 token 流加载期校验 | 卡片 T1/T2/T3 |
| `tools/diff/diff.py` | 新增 `--layer error` | 卡片 T5 |
| `ct/README.md` | CLI 形状补 `check`；删掉过时的“check 没做” | 实现已改变可观察面 |
| `docs/planning/rill-0.1.0-ct-defect-workarounds.md` | 新增 | 卡片 T4 |
| `docs/reviews/diff/PH-15.md` | 新增 | 卡片 T5 |
| `docs/reviews/closeout-15.md` | 新增本文件 | 卡片 §6 |

### 5.2 本相不允许且未发生的变化

| 路径 / 行为 | 判定证据 |
| --- | --- |
| `src/rill/**`（Python 参考实现） | `git diff --stat 4a7cd7a..HEAD -- src/rill` 为空 |
| `testdata/0.1.0/**`（fixture、golden、`sut.json`） | `git diff --stat` 为空 |
| `docs/RILL-0.1.0.md`（0.1.1 规范正文） | `git diff --stat` 为空 |
| `tools/checks/**`（门禁脚本） | `git diff --stat` 为空；g8 白名单未改 |
| PH-13/PH-14 已验证的 golden / 判据 | 未改；token 82 源、AST 82 源仍 0 差异 |
| 警告降级 / 用 warning 凑绿 | 未做；`W-01` 只新增提示，不改退出码 |
| push / tag | 未执行；`git tag --points-at HEAD` 为空 |

## 6. 未满足项（不计通过）

| ID | 条件 | 实测 | 原因 | 归属 |
| --- | --- | --- | --- | --- |
| E-3 | 四张表以只读接口暴露给 PH-16，复制/改写为硬错；接口测试 + 断言 | 无导出接口；`load_scan` 内表仅本进程可读 | A 路线单文件，无 `.h.ct` 可导出；接口语义还要求跨单元只读约束 | 多单元化待立卡（`closeout-14.md` §7） |

除 E-3 外，§2 其余判据均按原始输出通过。没有把 E-3 改写成“内部表也算接口”。

## 7. 函数计数与改动面

| 项 | 改动前 | 改动后 | 上限 |
| --- | --- | --- | --- |
| `ct/rill_ct.ct` 函数定义 | 59 | 62 | `ctc` 64 |
| 计入 `impl` 方法 | 60 | 63 | 64 |

新增三个函数：`load_verb_known`、`load_scan`、`cmd_check`。没有为腾位置做合并或新增长宏；
只复用了既有 `p_is_word_kind` / `p_adjacent` / `xrealloc` / `jobj`。`ct build` 仍不适用的
四条阻塞不变。

## 8. 全量计数与复跑

```text
load 负例        7/7 PASS（stage=load；code/line/col 逐条相等）
W-01             1/1 PASS（退出 0，col=14）
positive check   1/1 PASS（host-profiles：shell / agent 均通过，warnings 一致）
negative 全量    26/26 PASS（load 7 + parse 10 + tokenize 9）
error 层对拍     26 源、26 诊断、0 差异（exit 0）
token 层回归     82 源：73 成功 + 9 诊断，0 差异
AST 层回归       82 源：60 成功 + 22 诊断，0 差异
ct/test.sh       12 + 23 + 19 全 PASS
函数定义         59 → 62（含 impl 60 → 63）
Python / golden  未改；registry 空表
```

复跑：

```console
$ bash ct/build.sh
built /Users/samxx/trae-ws/rill-dsl/ct/bin/rill_ct
$ python3 tools/diff/diff.py --layer error
   sources=26 ok=0 diagnostics=26 diffs=0
   RESULT: PASS
== total diffs: 0
```

## 9. 门禁

```console
$ bash tools/check.sh all
...
== overall: PASS ==
```

末行 `== overall: PASS ==`。上一相遗留的 `g8-phase-freeze` 红已由
`tools/checks/phase-freeze-errata.json` 的单条白名单处理；本相未改门禁脚本、未开通用豁免。
