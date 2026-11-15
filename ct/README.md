# RILL 0.1.0 — CT 侧实现（token / parse / check / run）

独立的 CT 实现，不碰 `src/rill/` 的 Python 对照实现，也不改 `testdata/` 的既有 golden。
范围：读 `.rill` → 词法 → 语法 → 加载期校验 → 伪宿主求值；不含真实宿主与格式化。

```
ct/
├── src/main.ct          入口（CLI 分派）
├── src/common/          Diag/longjmp、JVal/JSON、内存与字符类（pub 全局量）
├── src/lexer/           词法
├── src/parser/          AST 与语法（31 条产生式）
├── src/loader/          加载期校验（三遍）与源码读入
├── src/eval/            求值：核心 / 控制流 / 并行 / 函数（文件内分区）
├── src/cli/             tokenize/parse/check/run 四个子命令
├── rill_ct.ct           单文件旧实现（冻结为参考实现，不参与构建，可作两条路的对照）
├── build.sh             从零构建出 ct/bin/rill_ct（ct build 多单元）
├── test.sh              跑本层覆盖的门禁用例
└── README.md            本文件（构建、规则映射、CT 限制、验证记录）
```

## 构建与运行

依赖：`ct`（ct-ast 主线多单元编译器，v0.44.1+）+ `cc`。切分理由与对拍口径见
`docs/phases/pending/ct-multiunit.md`。

```bash
cd /Users/samxx/trae-ws/rill-dsl
./ct/build.sh                       # 依次找 $CT、PATH 上的 ct、~/.local/bin/ct
./ct/test.sh                        # 对 12 tokens + 23 ast + 19 error 跑 harness

# ct 不在默认位置时
CT=/path/to/ct ./ct/build.sh
```

`build.sh` 展开后就是一条 `ct build`：

```bash
cd ct && ct build src/main.ct -I src --outdir <tmp> \
  --cflags '-Wall -Wextra -O2' -o ct/bin/rill_ct
```

单文件 `ctc` 上限 64 个函数，PH-17 起已触顶；多单元后上限是 256/单元。
`ct build` 不读 `CT_STD_DIR` 也能编（本实现不用 `Vec`/`Map` 泛型），四个已知阻塞的绕法
见“撞到的 CT 限制”第 1 条。

CLI 形状与 Python 版对齐：

```bash
ct/bin/rill_ct tokenize testdata/0.1.0/positive/tokens/compact/source.rill
ct/bin/rill_ct parse --dump-ast testdata/0.1.0/positive/simple/read-write/source.rill --profile shell
ct/bin/rill_ct check testdata/0.1.0/positive/check/each-bareword-w01/source.rill
ct/bin/rill_ct run testdata/0.1.0/positive/run/segment/success-plain/source.rill \
  --profile shell --fakes testdata/0.1.0/fakes/tools.json
```

退出码：`0` 成功（stdout 为 `{"tokens":[...]}`、`{"ast":...}`、`{"warnings":[...]}` 或
`{"ok":true,...}`）；`1` 运行结果失败（`{"ok":false,"error":...}`，仍属运行结果）；
`2` 诊断（stdout 为 `{"error":{"stage","code","line","col","message"}}`）。`stage` 取
`tokenize` / `parse` / `load` / `run`；CLI 用法错误取 `cli` / `E_USAGE`，与 Python 版一致。
`--profile` 接受 `shell|agent`，但 AST 与 profile 无关，两个值输出相同；`check` 的动词集
在 0.1.0 两个 profile 下相同（harness 的 `host-ast-equal` 也依赖这一点）。`run` 只实现伪宿主，
必须给 `--fakes`。

`tokenize` 输出覆盖 `positive/**` 与 `negative/tokenize/**`；`parse` 输出覆盖
`positive/**` 与 `negative/parse/**`；`check` 覆盖 `positive/check/**` 与
`negative/load/**`；`run` 覆盖 `positive/run/{segment,into,pipe,call,control,parallel}/**`（19 例）。

对拍入口（PH-13 起的回归门禁）：

```bash
python3 tools/diff/diff.py --layer token    # PH-13：82 源，0 差异
python3 tools/diff/diff.py --layer ast      # PH-14 预演（忽略 span）
python3 tools/diff/diff.py --layer error    # PH-15：negative/** 26 源，0 差异
python3 tools/diff/diff.py --layer eval     # PH-17：run 19 例，0 差异
```

## 规则到 CT 写法的映射

| 规范 | 落点 | 一句话写法 |
| --- | --- | --- |
| §3.1 注释与区块头 | `lx_comment_or_header` | 先看 `//` 后是否紧跟 `map`/`fn` 与 `{`；命中发 `MAP_HEADER`/`FN_HEADER`，否则吃到行尾；`//fn` 内用 `fn_depth` 让 `//` 退回普通注释 |
| §3.2 map 行模式 | `lx_map_line` | 独立状态机：行首短词 → 单字符标记（``'``/`` ` ``/`<`）→ 行尾长词；未闭合回到 `map_line/map_col` 报错 |
| §4.4 状语并列 | `p_parse_verb_call` | `(` 后循环读单词，逗号分隔，`)` 收口，产出 `Adverb.items` |
| §4.5 介宾短语 | `p_parse_verb_call` | `[名称]` 后读一个单词；名称先查冻结介词表，表外直接 `E-PARSE-UNKNOWN-PREP` |
| §4.10 尾随块 | `p_parse_trailing_block` | 语句尾巴循环识别 `[ok]/[error]/[into]{`，每条语句用 `ok_count/err_count` 做重复判定 |
| §4.14 `[results]` | `p_reject_results` / `p_parse_parallel` | 只有 `parallel` 的块尾允许；其余方括号入口先调用同一拒绝函数 |
| §4.16 token 位置 | `lx_advance` + `Token` | 1 基行列；换行重置 col；UTF-8 连续字节不增 col，等价于按码点计数 |
| §4.17 AST 等价 | `ast_*` 函数/宏 | 只写 `kind` 与字段，不写 `span`；golden 与 harness 的 canonical 都不含 span |
| §4.12 控制流 | `eval_if_stmt` / `truthy` | `if` 用 truthy；`[ok]` 只看 `ok`，两条通道不混 |
| §4.13 each 三态 | `eval_each_stmt` | null 0 轮；数组逐项；非数组 1 次；失败轮占 null 并继续 |
| §4.15 break 场域 | `eval_break_stmt` + `EOut.is_break` | 管道/块/program 各自截住；无异常机制，用返回值逐层早退 |
| §4.14 parallel | `eval_parallel_stmt` | 分支按源序串行模拟；`$` 是进入值；`[results]` 的 `$` 是结果数组 |
| §4.18 `//fn` | `eval_fn_call` | 首次出现去重；默认值只在缺实参时于调用方求值；返回最后一条语句段输出 |
| §4.18 `//fn` 默认值 | `template_mode` + `Default` | 只在 fn 模板内把 `$x?` 识别为 `Default`，出模板即关闭 |
| §4.19 词类判定 | `lx_bare` / `match_number` / `lx_field` | 裸词按停止符与 `\` 转义推进；数字要求前后不粘连词字符；`.` 后接标识符且前一字符非词字符时出 `FIELD` |
| §4.20 错误码 | `fail()` + `Diag` | 统一 `stage/code/line/col/message`，`longjmp` 回到 `main` 写诊断并退 2 |

AST 字段顺序按 Python 的 `FIELDS` 表；JSON 里键顺序不影响 harness（它按对象比对），
但保持顺序能让本实现自己的输出也可读。

### 语句产生式 → 代码位置（PH-14-T4，31 条）

规范 §三 EBNF 共 27 条命名产生式；另有 4 条在 EBNF 中内联、由 §3.1 / §3.2 / §4.4 /
§4.14 定义，合计 31 条。`L####` 是 PH-14 收口时单文件 `ct/rill_ct.ct` 的行号（已随 PH-17
迁移删除，仅作历史锚点）；现在这些函数都在 `ct/src/parser/parser.h.ct`，
`lx_map_line` 在 `ct/src/lexer/lexer.h.ct`。

| # | 产生式 | 代码位置 | 说明 |
| --- | --- | --- | --- |
| 1 | `program` | `p_parse_program` L1345 | 先 `header*`，再 `statement*`，到 EOF 收口 |
| 2 | `header` | `p_parse_program` L1345 | 按 `MAP_HEADER` / `FN_HEADER` 分派到两条块规则 |
| 3 | `map_block` | `p_parse_map_block` L1297 | `MAP_HEADER` 后逐条 `map_entry`，`RBRACE` 收口 |
| 4 | `fn_block` | `p_parse_fn_block` L1280 | `FN_HEADER` 后逐条 `fn_def`，`RBRACE` 收口 |
| 5 | `map_entry` | `p_parse_map_block` L1297 / `lx_map_line` L617 | 词法期已按“短词-标记-长词”切好，语法期只做结构装配 |
| 6 | `statement` | `p_parse_statement` L1321 | 按首 token 分派 7 种语句 |
| 7 | `simple_stmt` | `p_parse_simple_stmt` L1337 / `p_parse_statement_tail` L1040 | 动词调用 + 尾随块 + 可选 `|>` |
| 8 | `verb_call` | `p_parse_verb_call` L1533 | 主语可选；宾语、状语、介宾按序消费 |
| 9 | `subject` | `p_parse_verb_call` L1533 / `p_word_node` L1392 | 角色/裸词/引号/变量四态 |
| 10 | `prep_phrase` | `p_parse_prep_phrase` L1509 | 冻结介词表校验，表外 `E-PARSE-UNKNOWN-PREP` |
| 11 | `prep_block_stmt` | `p_parse_prep_block_stmt` L1073 | `[into]/[ok]/[error]` + 变量或动词调用 + 块 |
| 12 | `trailing_block` | `p_parse_trailing_block` L995 | `[ok]` 0..1、`[error]` 0..1、`[into]` 0..N |
| 13 | `block` | `p_parse_block` L1370 | `LBRACE` `statement*` `RBRACE`，缺块报 `E-PARSE-MISSING-BLOCK` |
| 14 | `if_clause` | `p_parse_if` L1105 | `if` / `else-if` / `else` 三分支链 |
| 15 | `condition` | `p_parse_expr` L1217 | 条件共用 `expr` |
| 16 | `each_clause` | `p_parse_each` L1129 | `each $var [in] expr` + `each_body` |
| 17 | `each_body` | `p_parse_each` L1129 / `p_parse_block` L1370 / `p_parse_trailing_block` L995 | 块 + 尾随块序列 |
| 18 | `parallel_clause` | `p_parse_parallel` L1154 | 分支列表 + 可选 `[results]` + 可选 `|>` |
| 19 | `branch` | `p_parse_parallel` L1154 / `p_parse_trailing_block` L995 | 分支限简单语句与 `[ok]/[error]/[into]` |
| 20 | `break_stmt` | `p_parse_break` L1189 | `break` + 可选值 + 可选 `-> $var` |
| 21 | `call_stmt` | `p_parse_call_stmt` L1235 | `@STRING arg*` + 尾随块 + 可选 `|>` |
| 22 | `arg` | `p_parse_call_stmt` L1235 / `p_parse_word` L1424 | 实参按 `value` 解析 |
| 23 | `expr` | `p_parse_expr` L1217 | `value` / `verb_call` / `pipe` 三选一 |
| 24 | `value` | `p_parse_word` L1424 / `p_word_node` L1392 | 引号/数字/裸词/变量/字段；裸词在 value 位归为字符串 |
| 25 | `pipe` | `p_parse_pipe` L1032 / `p_parse_statement_tail` L1040 | `|>` 串接，逐段独立尾随块 |
| 26 | `fn_def` | `p_parse_fn_def` L1256 | `@STRING` + 模板 + 块 |
| 27 | `fn_template` | `p_parse_fn_def` L1256 / `p_parse_pipe` L1032 | 模板内 `$x?` 出 `Default`，出模板即关闭 |
| 28 | `adverb`（§4.4 内联） | `p_parse_adverb` L1487 | `(` 单词列表 `)`，逗号分隔 |
| 29 | `[results]` 块（§4.14 内联） | `p_parse_parallel` L1154 / `p_reject_results` L981 | 只在 `parallel` 块尾允许，其余入口统一拒绝 |
| 30 | 映射标记符（§3.2 内联） | `lx_map_line` L617 | 单字符 ``'`` / `` ` `` / `<`，非法标记 `E-01` |
| 31 | 区块头判定（§3.1 内联） | `lx_comment_or_header` L559 | `//` 后接 `map`/`fn` 且有块才发头 token |

## 验证记录

2026-11-15，`ct build`（ct-ast 主线 v0.44.1）+ `cc -Wall -Wextra -O2`，macOS arm64：

- `positive/tokens`：12/12 PASS。
- `positive/ast`：23/23 PASS（harness 按 §4.17 忽略 span）。
- `negative/tokenize` + `negative/parse` + `negative/load`：PASS，断言到 `stage/code/line/col`。
- 全量差分（仓库资产）：`--layer token` 82 源（73 成功 + 9 诊断）0 差异；
  `--layer ast` 82 源 0 差异；`--layer error` 26 源 0 差异；
  `--layer eval` 19 例 0 差异（PH-17 起）。
- 边界：空文件、CRLF、无行尾换行三种输入的 token 序列与 Python 版相同。

复跑：

```bash
./ct/build.sh && ./ct/test.sh
```

## 撞到的 CT 限制与绕法

### 1. 单文件上限 64 个函数（PH-17 已用多单元解决）

最小复现：65 个 `static int fN(void)` + `main`。

```bash
ctc /tmp/ctprobe/many.ct -o /tmp/ctprobe/many.c
# /tmp/ctprobe/many.ct:1:1: error: too many functions (max 64)
# rc=1
```

第一版把词法器、JSON 构造器、AST 构造器、语法器都写成独立函数，直接超过上限。
PH-13..PH-16 的绕法：AST/JSON 单值构造器、字符分类与谓词改成宏。
代价：宏没有类型检查、`p_take`/`jget_str` 有重复求值/重复查键，且不能按模块拆。

PH-17 起改走 `ct build` 多单元（`docs/phases/pending/ct-multiunit.md`）：
单单元上限 256，`pub` 声明即跨单元可见；同时把这批省槽宏还原成函数。
四个已知阻塞的绕法：结构体按序定义、`impl` 不写尾分号、宏压单行、>159 字符宏改函数。

### 2. 单文件 `ctc` 不提供 `Vec` / `Map` 预解析层（绕开）

最小复现：

```c
struct Item { int x; };
struct Holder { Map<char *, struct Item> items; };
```

```bash
ctc /tmp/ctprobe/mapstruct.ct -o /tmp/ctprobe/mapstruct.c   # rc=0
cc -std=c99 /tmp/ctprobe/mapstruct.c -o /tmp/ctprobe/mapstruct   # rc=1
# error: unknown type name 'Map'
# error: expected member name or ';' after declaration specifiers
```

生成的 C 原样留下 `Map<...>`：容器层是 `ct build` 多单元时预解析的，`ctc` 单文件不注入。

多单元入口已复核：`~/.local/bin/ct`（`ct v0.44.1`，ct-ast 主线）可用，只是不在 PATH；
`ctc -> ct` 是兼容别名，`ct build` 与 `ct-ast build` 同源。仓库根 `../ct-lang/ctc` 是
L0 种子，`build` 会报 `ctc: 'build' (multi-file) is not supported by this compiler`（rc=1）。
用 `ct build` 复跑同一探针：

- 非导出结构（`struct Holder { Map<char *, struct Item> items; };`）：rc=0，生成完整的
  `struct Map_char_p_Item`，无 incomplete type。
- 导出结构（`.h.ct` 里 `pub struct Holder { pub Map<char *, Item> items; }`）：rc=1。
  `types.h` 把字段发射成 `pub struct Map_char_p_Item items;`（多出字面 `pub`，且
  `Map_char_p_Item` 只有前置声明），`cc` 报 `unknown type name 'pub'` 与
  `field has incomplete type 'struct Item'`。这就是「`Map<K, 用户 struct>` 放进导出结构
  生成不完整类型」的复现；根因在导出头，不在入口。

绕法：Token 数组、map 短词表都用自建 `malloc/realloc` 数组，插入序靠追加、查重靠线性扫描。
后续若拆多单元，不要往 `pub struct` 里放 `Map` 字段（见 `docs/reviews/closeout-13.md` §6）。
代价：手写内存增长与释放（本实现是一次性 CLI，未回收），没有 `Map` 的插入序与引用计数语义。

### 3. 指针变量上的 `.` 方法调用（绕开）

最小复现（`p` 是 `struct S *`，方法来自 trait）：

```c
p.set(7);
```

```bash
ctc /tmp/ctprobe/ptrrecv2.ct -o /tmp/ctprobe/ptrrecv2.c   # rc=0
cc -std=c99 /tmp/ctprobe/ptrrecv2.c -o /tmp/ctprobe/ptrrecv2   # rc=1
# error: member reference type 'struct S *' is a pointer; did you mean to use '->'?
# error: no member named 'set' in 'struct S'
```

生成的 C 原样保留 `p.set(7)`，没有展开成 `S_Setter_set(...)`。用 `ct build` 复核：

```c
p.__setter_vptr->set(&p, 7);
```

clang 直接报 `error: member reference type 'struct S *' is a pointer`，`ct build` rc=1；
即使编译器只告警，`&p` 传给 `void *self` 的是 `S**`，非空时结果已错。绕法：本实现不定义
方法，全部用自由函数与显式 `self` 参数，因此没有触发该路径。代价：没有 vtable/接口派发，
第一层也不需要。

## 明确没做

- 真实宿主：`run` 只认 `--fakes`；没有真实进程/文件/网络（PH-19/PH-20）。
- `fmt` 子命令（PH-18）；真实并发调度、取消、超时（本层按源序串行模拟）。
- `Bytes` / `Opaque` 的 truthy 与透传：没有 fake 注入通道，未建立单测
  （见 `closeout-16.md` §6、`diff/PH-17.md` §5）。
- `Value` 的 arena / retain / release：求值器直接消费 JSON 树，进程即退，未做回收。
- AST 的 `span`：golden 与 harness canonical 都不含 span，Python 版有 span 但比对时被剥离；
  运行时错误因此只有 `stage=run` 与 `line/col=0`。
- `break` 值不是字符串时：Python 会把该值当错误串，本层只支持字符串。
- 释放 AST/JSON 内存：进程即退，未做回收；若第二层要长驻，需要补生命周期管理。

## 后续相的准备

PH-15 加载期校验、PH-16 求值核心、PH-17 控制流与函数均已完成；剩余是格式化与真实宿主。

1. PH-18 直接往 `ct/src/` 加单元即可，单单元上限 256，不再需要宏化省槽。
2. PH-19/PH-20 的宿主能力按 `.h.ct` 接口落，复用 `Diag` 的 `stage/code/line/col` 信封。
3. 运行时定位若要精确到行列，需要把 `span` 带进 AST（当前被 golden 剥离）。
