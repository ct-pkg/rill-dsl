# PH-13 收口对照表

> 基线 `1006030`（本轮改动前的 HEAD）；本卡改动见 §4。只本地提交，不 push、不打 tag。
> 差异报告见 `docs/reviews/diff/PH-13.md`，登记表见 `docs/reviews/diff/registry.md`。
> 规范版本 1.9.0；CT 轨道产品版本 `0.13.0`（卡片 §6 目标）。Python 参考实现的版本落点
> `src/rill/__init__.py#__version__` 仍为 `0.12.0`：本卡边界禁止改 `src/rill/`，版本落点
> 迁移不在本卡范围，`g8-version` 因此仍显示 0.12.0（不是遗漏）。`docs/RILL-0.1.0.md` 未改。

## 1. 判定

**GO。** CT 版 `tokenize` 可重复构建；12 个 token golden 全过；9 个词法负例的
`stage/code/line/col` 与 Python 一致；token 层 82 个源对拍 **0 差异**；成功/诊断退出码
0/2 与信封同形。`negative/load/**` 等范围外用例未通过，逐条列在 §5，不计入本卡。

## 2. 退出判据

| ID | 条件 | 原始证据 | 结果 |
| --- | --- | --- | --- |
| E-1 | 干净检出上 `bash ct/build.sh` 退出 0，产物存在 | `built /Users/samxx/trae-ws/rill-dsl/ct/bin/rill_ct`；`test -x ct/bin/rill_ct` → 0 | PASS |
| E-2 | 12 个 token golden 全部由 CT SUT 通过 | `compliance: 12 passed, 0 failed ... VERDICT: PASS (exit 0)` | PASS |
| E-3 | 9 个词法负例的 `stage/code/line/col` 与 Python 一致 | 9 行 `PASS ... tokenize <code>@<line>:<col>`；逐条 JSON 见差异报告 §3 | PASS |
| E-4 | token 对拍 12/12，差异 0 或全部登记 | `sources=82 ok=73 diagnostics=9 diffs=0`；`RESULT: PASS`；`total diffs: 0` | PASS |
| E-5 | 成功退出 0、词法失败退出 2，stdout 信封同形 | `ok_rc=0` / 顶层键 `['tokens']`；`err_rc=2` / 顶层键 `{"error":...}` | PASS |
| E-6 | 任务清单每项可独立验收（T-6） | §3 六条 verify 与原始输出 | PASS（T5 见注） |

注：T5 的 verify 已按用户裁定改为 9 个 `--case` 的精确过滤（见卡片 §3 原文），原
`--bucket negative --kind error` 会连带选中 7 条 `negative/load/**`（PH-15），整体退出 1。
判据 E-3 的实质不变；词法 9 条单跑 9/9 PASS，load 7 条仍在 §5 列红，不计入通过。

## 3. 任务 verify

| 任务 | verify（仓库根执行） | 原始输出 | 退出码 |
| --- | --- | --- | --- |
| PH-13-T1 | `bash ct/build.sh && test -x ct/bin/rill_ct` | `built .../ct/bin/rill_ct` | 0 |
| PH-13-T2 | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --kind tokens` | `compliance: 12 passed, 0 failed`；`VERDICT: PASS` | 0 |
| PH-13-T3 | `python3 tools/diff/diff.py --layer token` | `sources=82 ok=73 diagnostics=9 diffs=0`；`total diffs: 0` | 0 |
| PH-13-T4 | `test -s docs/reviews/diff/PH-13.md` | 文件存在且非空；`registry.md` 同批落盘 | 0 |
| PH-13-T5 | 卡片原文：`bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --bucket negative --kind error` | `compliance: 19 passed, 7 failed`（7 条全是 `negative/load/**`） | 1 |
| PH-13-T5（范围内） | 同上 + 9 个 `--case negative/tokenize/...` | `compliance: 9 passed, 0 failed`；`VERDICT: PASS` | 0 |

`ct/test.sh` 全量切片（token + AST + error）同样 PASS：

```text
== ... --bucket positive --kind tokens   → 12 passed, 0 failed
== ... --bucket positive --kind ast      → 23 passed, 0 failed
== ... --bucket negative --kind error ...→ 19 passed, 0 failed
ct/test.sh: PASS
```

## 4. 允许变化 / 不允许变化

### 4.1 本卡允许且实际发生的变化

| 路径 | 变化 | 理由 |
| --- | --- | --- |
| `ct/build.sh` | 产物名 `ct/bin/rill-ct` → `ct/bin/rill_ct` | 对齐卡片 §2 与 E-1 的 `test -x ct/bin/rill_ct` |
| `ct/test.sh` | 默认二进制路径同步 | 同上 |
| `ct/README.md` | 构建/入口说明、CT 限制复现、验证记录；修正“本机只有 ctc”的旧结论 | §6 工具链结论落盘 |
| `tools/diff/diff.py` | 新增对拍入口 | 卡片 T3 |
| `tools/diff/sut.ct.json` | 新增 CT SUT 清单 | 卡片 T2 |
| `docs/reviews/diff/PH-13.md` | 新增本阶段差异报告 | 卡片 T4 |
| `docs/reviews/diff/registry.md` | 新建空登记表 | 卡片 T4 |
| `docs/reviews/closeout-13.md` | 新增本文件 | 卡片 §6 |

以上只改构建产物名、协议清单与文档；`tokenize` 的语义未动。

### 4.2 本卡不允许且未发生的变化

| 路径 / 行为 | 判定证据 |
| --- | --- |
| `src/rill/**`（Python 参考实现） | `git diff --quiet -- src/rill` → 0 |
| `testdata/0.1.0/**`（fixture、golden、`sut.json`） | `git diff --quiet -- testdata` → 0 |
| `docs/RILL-0.1.0.md`（0.1.1 规范正文） | `git diff --quiet -- docs/RILL-0.1.0.md` → 0 |
| `ct/rill_ct.ct`（在途文件，另一会话所有） | 未修改、未重写 |
| golden 修订 | 0 处；无 `golden-change:` 提交 |
| push / tag | 未执行 |
| 为凑 T5 原文 verify 去实现 `check` 或改卡片 | 均未做；7 条 load 如实列红 |

### 4.3 差异策略（对拍口径）

| 允许 | 不允许 |
| --- | --- |
| 规范明文允许的宿主差异，登记为 `host-specific` | 无登记的实现差异（0 条也不能“默认通过”） |
| 规范歧义先提 CR，定稿后两边同步 | 只改 Python 或只改 CT 后不记账 |
| golden 本身有错，经用户签字后修订并登记旧/新值 | 改 golden 迁就实现（本卡 0 处） |

## 5. 本层范围外与未跑通项

| 项 | 数量 | 实测 | 归属 |
| --- | --- | --- | --- |
| `negative/load/**` | 7 | `stage` 实际 `cli`，期望 `load`；CT 无 `check` 子命令 | PH-15 |
| `W-01` 裸词警告 | 1 | 未实现 | PH-15 |
| `negative/parse/**` | 10 | 已通过，但属 AST 层判据 | PH-14 |
| `positive/**` AST golden | 23 | 已通过，但属 AST 层判据 | PH-14 |
| run / 求值 / 管道 | 10 | 未实现 | PH-16 |
| 控制流 / parallel / `//fn` | 9 | 未实现 | PH-17 |
| round-trip | 71 | 未实现 | PH-18 |
| Shell host fixture | 12 | 未实现 | PH-19 |
| Agent host fixture | 14 | 未实现 | PH-20 |
| 全链路 CLI 与全层对拍 | — | 未实现 | PH-21 |

7 条 load 的实际失败行：

```text
FAIL negative/load/fn-arity-too-few    stage 不符：期望 'load'，实际 'cli'
FAIL negative/load/fn-arity-too-many   stage 不符：期望 'load'，实际 'cli'
FAIL negative/load/fn-default-not-tail stage 不符：期望 'load'，实际 'cli'
FAIL negative/load/fn-name-case        stage 不符：期望 'load'，实际 'cli'
FAIL negative/load/map-duplicate-short stage 不符：期望 'load'，实际 'cli'
FAIL negative/load/unknown-function    stage 不符：期望 'load'，实际 'cli'
FAIL negative/load/unknown-verb        stage 不符：期望 'load'，实际 'cli'
```

## 6. 工具链矛盾：`ctc` / `ct build` / `ct-ast build`

**结论：本机可用的多单元入口是 `~/.local/bin/ct`（`ct v0.44.1`，即 ct-ast），它不在
当前 shell 的 PATH 上；`ct build` 与 `ct-ast build` 是同一件事；“只有 ctc、没有
ct build”是入口查找不完整造成的误判。**

证据：

1. **两个 `ctc` 不是同一个编译器。**
   - 仓库根 `../ct-lang/ctc`（104 KB，`sha256 c3f6e28…`）是 L0 种子（`selfhost/l0/ctc.c`），
     `-v` 也报 `ctc v0.44.1`，但 `build` 被显式拒绝：
     `ctc: 'build' (multi-file) is not supported by this compiler`，rc=1。
   - `~/.local/bin/ct`（1.29 MB，`sha256 92ec5fa…`）是 ct-ast 主线，`ct v0.44.1`，
     `--help` 列出 `ct build <input.ct>... [-I] [--emit-c] [--outdir] ...`。
   - `~/.local/bin/ctc` 只是 `ct` 的符号链接（`ctc -> ct`）。所以“PATH 里只有 ctc”在
     安装目录里恰恰意味着 `ct` 已经可用，只是没进 PATH。
2. **`ct build` 与 `ct-ast build` 同源。** `docs/glossary.md`（ct-lang）定义安装形态为
   二进制命名为 `ct`、10.7 起由 ct-ast 提供，没有独立的 `ct-ast` 可执行文件；仓库里
   `selfhost/ct-ast/` 是源码目录，不是命令。所谓 `ct-ast build` 就是 `ct build`。
3. **`Map<char *, 用户 struct>` 在该入口下的行为（最小复现，均在 `/tmp`）：**
   - 单文件单元、非导出结构：
     ```c
     struct Item { int x; };
     struct Holder { Map<char *, struct Item> items; };
     ```
     `ct build --emit-c mapstruct.ct --outdir <existing>` → rc=0；生成
     `struct Map_char_p_Item { struct ct_buf * h; };` 与
     `struct Holder { struct Map_char_p_Item items; };`，类型完整。
   - 导出结构（`types/types.h.ct` 里 `pub struct Holder { pub Map<char *, Item> items; }`）：
     `ct build` → **rc=1**，`types.h` 发射为
     `pub struct Map_char_p_Item items;`（字段前多出字面 `pub`），且
     `Map_char_p_Item` 只有前置声明；`cc` 报
     `error: unknown type name 'pub'`，以及 `Vec.h` 里
     `error: field has incomplete type 'struct Item'`（值类型只有 `struct Item;` 前置声明）。
   - 另一条线用 `ct-ast build --emit-c` 复现的“整包问题”**属实**；根因是导出头对
     `pub struct` 字段的发射缺陷（字面 `pub` + 不完整类型），不是两个入口的差异。
4. **指针变量上的 `.` 方法调用**（`S *p = &s; p.set(7);`）在 `ct build` 下发射
   `p.__setter_vptr->set(&p, 7);`：clang 直接报
   `error: member reference type 'struct S *' is a pointer; did you mean to use '->'?`，
   `ct build` rc=1；即使编译器只告警，`&p` 传给 `void *self` 的是 `S**`，非空时结果已错。
   因此 PH-15/16 的门禁口径应写死：**禁用指针变量上的 `.` 方法调用，只用值接收者或
   自由函数**；`Value`、宿主能力表不要放进 `pub struct` 内嵌 `Map`。

对后续卡的影响：PH-14 仍可维持单文件（不受导出头缺陷影响）；PH-15/16 若拆多单元，
构建命令用 `ct build -I <srcroot>`，不要再用“本机没有 ct”作为保持单文件的理由；
门禁脚本应显式解析 `$CT` 或 `~/.local/bin/ct`，不得把“PATH 里没有”当成“工具链缺失”。

## 7. 全量计数与复跑

```text
token golden       12/12 PASS
词法负例            9/9 PASS（stage/code/line/col 逐条相等）
token 对拍          82 源：73 成功 + 9 诊断，0 差异（exit 0）
ct/test.sh          12 + 23 + 19 全 PASS
negative/load       7 条 FAIL（PH-15，范围外）
AST 对拍（参考）    82 源：60 成功 + 22 诊断，0 差异（不计入本卡；
                    22 = 19 个 parse/tokenize 负例 + 3 个 token-only 正例）
Python/golden       未改（git diff 均 0）
```

复跑：

```console
$ bash ct/build.sh
built /Users/samxx/trae-ws/rill-dsl/ct/bin/rill_ct
$ ./ct/test.sh
...
ct/test.sh: PASS
$ python3 tools/diff/diff.py --layer token
== layer=token
   sources=82 ok=73 diagnostics=9 diffs=0
   RESULT: PASS
== total diffs: 0
```

## 8. lessons

- `gate:` 解析 CT 入口必须同时看 PATH、`$CT` 与 `~/.local/bin/ct`；仓库根 `ctc` 是 L0
  种子，不能用它判断多单元能力。触发条件：`ctc build` 报
  `multi-file is not supported`。
- `gate:` 负例门禁不要用 `--bucket negative --kind error` 跨 phase 一把抓；要么按
  `--case` 过滤到本层，要么显式接受后续层的红并单列归属。本卡 T5 的字面 verify 就是
  这个坑。
- `spec:` v0.44.1 的导出头不能承载 `pub struct` 里的 `Map<K, 用户 struct>`；PH-15/16
  的类型与宿主表用自由函数 + 值接收者，避免内嵌 Map 与指针 `.` 调用。
- `rejected:` 不用“已经跑过”替代卡片要求的逐条证据；不为过 T5 原文 verify 去实现
  `check`、改卡片或改 golden。
