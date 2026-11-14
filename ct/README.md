# RILL 0.1.0 — CT 侧第一层（token / parse）

独立的 CT 实现，不碰 `src/rill/` 的 Python 对照实现，也不改 `testdata/` 的既有 golden。
范围只有：读 `.rill` → 词法 → 语法 → 可 diff 的 JSON；不求值、不碰宿主、不做双 profile。

```
ct/
├── rill_ct.ct     单文件 CT 实现（词法 + 语法 + CLI + JSON 写出）
├── build.sh       从零构建出 ct/bin/rill_ct
├── test.sh        跑本层覆盖的门禁用例
└── README.md      本文件（构建、规则映射、CT 限制、验证记录）
```

## 构建与运行

依赖：`ctc`（CT source-to-source 编译器，本机为 v0.44.1）+ `cc`。

```bash
cd /Users/samxx/trae-ws/rill-dsl
./ct/build.sh                       # ctc 依次找 $CTC、../ct-lang/ctc、PATH
./ct/test.sh                        # 对 12 tokens + 23 ast + 19 error 跑 harness

# ctc 不在默认位置时
CTC=/path/to/ctc ./ct/build.sh
```

`build.sh` 展开后就是两条命令：

```bash
ctc ct/rill_ct.ct -o /tmp/rill_ct.c
cc -std=c99 -Wall -Wextra -O2 /tmp/rill_ct.c -o ct/bin/rill_ct
```

`ctc` 有两种来源：仓库根 `../ct-lang/ctc` 是 L0 种子，只做单文件，`build` 会显式拒绝；
`~/.local/bin/ct` 是 ct-ast 主线（`ctc -> ct` 兼容别名），提供 `ct build` 多单元入口。
本层是单文件，用前者即可；多单元复核见“撞到的 CT 限制”第 2 条。

CLI 形状与 Python 版对齐：

```bash
ct/bin/rill_ct tokenize testdata/0.1.0/positive/tokens/compact/source.rill
ct/bin/rill_ct parse --dump-ast testdata/0.1.0/positive/simple/read-write/source.rill --profile shell
```

退出码：`0` 成功（stdout 为 `{"tokens":[...]}` 或 `{"ast":...}`）；`2` 诊断（stdout 为
`{"error":{"stage","code","line","col","message"}}`）。`stage` 取 `tokenize` / `parse`；
CLI 用法错误取 `cli` / `E_USAGE`，与 Python 版一致。`--profile` 接受 `shell|agent`，
但 AST 与 profile 无关，两个值输出相同（harness 的 `host-ast-equal` 也依赖这一点）。

`tokenize` 输出覆盖 `positive/**` 与 `negative/tokenize/**`；`parse` 输出覆盖
`positive/**` 与 `negative/parse/**`。

对拍入口（PH-13 起的回归门禁）：

```bash
python3 tools/diff/diff.py --layer token    # PH-13：82 源，0 差异
python3 tools/diff/diff.py --layer ast      # PH-14 预演（忽略 span）
```

## 规则到 CT 写法的映射

| 规范 | 落点 | 一句话写法 |
| --- | --- | --- |
| §3.1 注释与区块头 | `lx_comment_or_header` | 先看 `//` 后是否紧跟 `map`/`fn` 与 `{`；命中发 `MAP_HEADER`/`FN_HEADER`，否则吃到行尾；`//fn` 内用 `fn_depth` 让 `//` 退回普通注释 |
| §3.2 map 行模式 | `lx_map_line` | 独立状态机：行首短词 → 单字符标记（``'``/`` ` ``/`<`）→ 行尾长词；未闭合回到 `map_line/map_col` 报错 |
| §4.4 状语并列 | `p_parse_adverb` | `(` 后循环读单词，逗号分隔，`)` 收口，产出 `Adverb.items` |
| §4.5 介宾短语 | `p_parse_prep_phrase` | `[名称]` 后读一个单词；名称先查冻结介词表，表外直接 `E-PARSE-UNKNOWN-PREP` |
| §4.10 尾随块 | `p_parse_trailing_block` | 语句尾巴循环识别 `[ok]/[error]/[into]{`，每条语句用 `ok_count/err_count` 做重复判定 |
| §4.14 `[results]` | `p_reject_results` / `p_parse_parallel` | 只有 `parallel` 的块尾允许；其余方括号入口先调用同一拒绝函数 |
| §4.16 token 位置 | `lx_advance` + `Token` | 1 基行列；换行重置 col；UTF-8 连续字节不增 col，等价于按码点计数 |
| §4.17 AST 等价 | `ast_*` 宏 | 只写 `kind` 与字段，不写 `span`；golden 与 harness 的 canonical 都不含 span |
| §4.18 `//fn` 默认值 | `template_mode` + `Default` | 只在 fn 模板内把 `$x?` 识别为 `Default`，出模板即关闭 |
| §4.19 词类判定 | `lx_bare` / `match_number` / `lx_field` | 裸词按停止符与 `\` 转义推进；数字要求前后不粘连词字符；`.` 后接标识符且前一字符非词字符时出 `FIELD` |
| §4.20 错误码 | `fail()` + `Diag` | 统一 `stage/code/line/col/message`，`longjmp` 回到 `main` 写诊断并退 2 |

AST 字段顺序按 Python 的 `FIELDS` 表；JSON 里键顺序不影响 harness（它按对象比对），
但保持顺序能让本实现自己的输出也可读。

## 验证记录

2026-11-15，`ctc v0.44.1`，macOS arm64：

- `positive/tokens`：12/12 PASS。
- `positive/ast`：23/23 PASS（harness 按 §4.17 忽略 span）。
- `negative/tokenize` + `negative/parse`：19/19 PASS，断言到 `stage/code/line/col`。
- 全量差分（仓库资产）：`python3 tools/diff/diff.py --layer token` 对比 Python 版，
  `positive` + `negative` 共 82 个 `source.rill`：73 个成功 token 序列 + 9 个词法诊断，
  **0 差异**；`--layer ast` 亦为 0 差异（不计入 PH-13 判据）。
- 边界：空文件、CRLF、无行尾换行三种输入的 token 序列与 Python 版相同。

复跑：

```bash
./ct/build.sh && ./ct/test.sh
```

## 撞到的 CT 限制与绕法

### 1. 单文件上限 64 个函数（实际撞上）

最小复现：65 个 `static int fN(void)` + `main`。

```bash
ctc /tmp/ctprobe/many.ct -o /tmp/ctprobe/many.c
# /tmp/ctprobe/many.ct:1:1: error: too many functions (max 64)
# rc=1
```

第一版把词法器、JSON 构造器、AST 构造器、语法器都写成独立函数，直接超过上限。
绕法：把所有只做字段拼装的 AST 构造器、JSON 单值构造器、字符分类与谓词改成宏，
并把 `jnull/jbool/jint/jstr/jstrn/jarr/jobj` 收敛到一个 `jnew(kind, num, s, n)`。
代价：宏没有类型检查、调试时看不到独立栈帧；且必须继续单文件，不能按模块拆。
第二层若要用 `ct build` 多单元，应把词法、语法、CLI 拆成独立 `.ct` 单元，绕开该上限。

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

- 求值、宿主调用、`--fakes`、`shell/agent` 双 profile 行为（仅接受参数，不改变 AST）。
- `check` / `run` / `fmt` 子命令；`negative/load/**` 的加载期错误码。
- `each [in]` 的 `W-01` 裸词警告（`check` 才消费）。
- AST 的 `span`：golden 与 harness canonical 都不含 span，Python 版有 span 但比对时被剥离。
- 释放 AST/JSON 内存：进程即退，未做回收；若第二层要长驻，需要补生命周期管理。

## 第二层需要的准备

1. 用 `ct build` 多单元替代单文件 `ctc`，把词法、语法、CLI 拆开；同时获得 `lib/std` 的
   `Vec`/`Map`（或继续用自建数组，避免容器语义差异）。
2. AST 从「直接写 JSON」升级为可复用的节点结构（或让求值器直接消费同一棵 JSON 树），
   并补 `span` 以便运行时错误定位。
3. 加载期能力：`//map` / `//fn` 表的查重、函数名精确匹配与按位置绑定、未知动词/函数错误码
   （`negative/load/**`）。
4. 求值器与宿主动词注册表：沿用本层的 `stage/code/line/col` 诊断信封；`check` 的
   `W-01` 需要把 `each [in]` 右值的来源信息从解析期带出来。
5. 对拍入口已入库：`python3 tools/diff/diff.py --layer token`（PH-13 起作为回归门禁；
   PH-14 用 `--layer ast` 扩到 AST 层）。
