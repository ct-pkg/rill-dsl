# PH-14 收口对照表

> 基线 `bc2c8cc`（AST 差异报告提交）；本相收口改动见 §4。只本地提交，不 push、不打 tag。
> 规范 1.9.0；CT 轨道产品版本 `0.14.0`（卡片 §6 目标）。Python 参考实现版本落点
> `src/rill/__init__.py#__version__` 仍为 `0.12.0`：边界禁止改 `src/rill/`，`g8-version`
> 因此仍显示 0.12.0（不是遗漏）。`docs/RILL-0.1.0.md` 未改。
> 差异报告见 `docs/reviews/diff/PH-14.md`；登记表 `docs/reviews/diff/registry.md` 保持空表。

## 1. 判定

**GO（单文件 `ctc` 路线）。** parser/AST 已端到端可用：23 个 AST golden 全过；10 个
parse 负例的 `stage/code/line/col` 与 Python 一致；AST 层 82 源对拍 **0 差异**；成功/诊断
退出码 0/2 与信封同形。`ct build` 多单元化按用户决定**不在本相做**，四条阻塞单列在 §6，
不影响本相判据。

## 2. 退出判据

| ID | 条件 | 原始证据 | 结果 |
| --- | --- | --- | --- |
| E-1 | 23 个 AST golden 全部由 CT SUT 通过 | `compliance: 23 passed, 0 failed ... VERDICT: PASS (exit 0)` | PASS |
| E-2 | 10 个 parse 负例 `stage=parse` 与错误码/行列一致 | 10/10 逐条相等，退出码均为 2（见差异报告 §3） | PASS |
| E-3 | AST 对拍 23/23，忽略 `span` 0 差异或全部登记 | 23/23 golden；`sources=82 ok=60 diagnostics=22 diffs=0`；`RESULT: PASS` | PASS |
| E-4 | 成功 0、parse 失败 2；错误 JSON 同形 | 成功顶层键 `ast` / rc 0；诊断顶层键 `error` / rc 2 | PASS |
| E-5 | 每个语句形态至少 1 个 AST golden | 11 类形态逐项有 golden（差异报告 §5）；产生式映射 31 条见 `ct/README.md` | PASS |
| E-6 | 任务清单每项可独立验收（T-6） | §3 四条 verify 均有命令与原始输出；T3 原文命令含 7 条范围外 load，已单列 | PASS（附 T3 范围注） |

E-6 不是靠“全绿”凑出来的：T3 的字面 verify 退出 1，原因全部是 `negative/load/**`（PH-15）；
本相只把 `negative/parse/**` 10 条记为通过，范围外 7 条在 §5 如实列红。

## 3. 任务 verify

| 任务 | verify（仓库根执行） | 原始输出 | 退出码 |
| --- | --- | --- | --- |
| PH-14-T1 | `bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --kind ast --bucket positive` | `compliance: 23 passed, 0 failed`；`VERDICT: PASS` | 0 |
| PH-14-T2 | `python3 tools/diff/diff.py --layer ast` | `sources=82 ok=60 diagnostics=22 diffs=0`；`total diffs: 0` | 0 |
| PH-14-T3 | 卡片原文：`bash tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --bucket negative --kind error` | `compliance: 19 passed, 7 failed`（7 条全是 `negative/load/**`） | 1 |
| PH-14-T3（范围内） | 同上 + 10 个 `--case negative/parse/...` | `compliance: 10 passed, 0 failed` | 0 |
| PH-14-T4 | `test -s ct/README.md` | 文件非空；新增 31 条产生式 → 代码位置映射 | 0 |

T1 说明：接管时 AST 序列化已与 golden 同形，**补差 0 处**，没有为提交而改代码。T2 的
报告提交为 `bc2c8cc`。T3 的 10 条清单在 `docs/reviews/diff/PH-14.md` §3。

## 4. 允许变化 / 不允许变化

### 4.1 本相允许且实际发生的变化

| 路径 | 变化 | 理由 |
| --- | --- | --- |
| `docs/reviews/diff/PH-14.md` | 新增 | 卡片 T2：AST 差异报告 |
| `ct/README.md` | 新增“31 条产生式 → 代码位置”映射 | 卡片 T4 / E-6 |
| `docs/reviews/closeout-14.md` | 新增本文件 | 卡片 §6 |

代码零改动：`ct/rill_ct.ct` 的 parser/AST 段在接管时已满足全部判据。

### 4.2 本相不允许且未发生的变化

| 路径 / 行为 | 判定证据 |
| --- | --- |
| `src/rill/**`（Python 参考实现） | 未改 |
| `testdata/0.1.0/**`（fixture、golden、`sut.json`） | 未改 |
| `docs/RILL-0.1.0.md`（0.1.1 规范正文） | 未改 |
| `ct/rill_ct.ct` 的语义 | 未改；无“为过门禁”的改写 |
| golden 修订 / 判据放宽 | 0 处；没有 `golden-change:` 提交 |
| `ct build` 多单元化 | 未做；见 §6、§7，不写成通过 |
| push / tag | 未执行 |

### 4.3 差异策略

| 允许 | 不允许 |
| --- | --- |
| 规范允许的宿主差异，登记为 `host-specific` | 无登记的实现差异 |
| 规范歧义先提 CR，定稿后两边同步 | 只改一边不记账 |
| golden 本身有错，经用户签字后修订并登记 | 改 golden 迁就实现（本相 0 处） |

## 5. 本层范围外与未跑通项

| 项 | 数量 | 实测 | 归属 |
| --- | --- | --- | --- |
| `negative/load/**` | 7 | `stage` 实际 `cli`，期望 `load` | PH-15 |
| `W-01` 裸词警告 | 1 | 未实现 | PH-15 |
| run / 求值 / 管道求值 | 10 | 未实现 | PH-16 |
| 控制流求值 / parallel 执行 / `//fn` 调用 | 9 | 未实现 | PH-17 |
| round-trip | 71 | 未实现 | PH-18 |
| Shell host fixture | 12 | 未实现 | PH-19 |
| Agent host fixture | 14 | 未实现 | PH-20 |
| 全链路 CLI 与全层对拍 | — | 未实现 | PH-21 |

7 条 load 的失败形态与 PH-13 收口一致：

```text
FAIL negative/load/fn-arity-too-few    stage 不符：期望 'load'，实际 'cli'
FAIL negative/load/fn-arity-too-many   stage 不符：期望 'load'，实际 'cli'
FAIL negative/load/fn-default-not-tail stage 不符：期望 'load'，实际 'cli'
FAIL negative/load/fn-name-case        stage 不符：期望 'load'，实际 'cli'
FAIL negative/load/map-duplicate-short stage 不符：期望 'load'，实际 'cli'
FAIL negative/load/unknown-function    stage 不符：期望 'load'，实际 'cli'
FAIL negative/load/unknown-verb        stage 不符：期望 'load'，实际 'cli'
```

## 6. `ct build` 四条阻塞（单列）

结论先说：**PH-14 的验收不依赖多单元，本相判定不受这四条阻塞影响。** 本相仍用
`ctc v0.44.1` 单文件构建；以下只是把“为什么现在不能切 `ct build`”钉死，供后续立卡时复现。

### 阻塞 1：前向 `typedef` 不被接受

```c
// b1.ct
typedef struct JVal JVal;
struct JVal { int x; };
int main(void){ return 0; }
```

```console
$ ~/.local/bin/ct build b1.ct -o b1
b1.ct:1:21: error: unexpected token
$ echo $?
1
```

对应本文件 L115 `typedef struct JVal JVal;`。需要 CT 支持不带定义体的前向 typedef，或
在规范里明确“必须写成 `typedef struct X { … } X;`”。

### 阻塞 2：`impl` 块尾 `;` 不被接受

```c
// b2.ct
trait T { void f(); }
struct S { int x; } use T;
impl T for S { void f() { self->x = 1; } };
int main(void){ S s; s.f(); return 0; }
```

```console
$ ~/.local/bin/ct build b2.ct -o b2
b2.ct:3:43: error: expected a type (tok 4 ';')
$ echo $?
1
```

对应本文件 L277 `impl Emitter for StdoutEmitter { ... };`。需要 CT 接受 `};` 或给出
“impl 末尾不要分号”的明确诊断。

### 阻塞 3：反斜杠续行的 `#define` 不被支持

```c
// b3.ct
#define f(x) \
    ((x) + 1)
int main(void){ return f(1); }
```

```console
$ ~/.local/bin/ct build b3.ct -o b3
b3.ct:2:6: error: expected a type (tok 4 '(')
$ echo $?
1
```

本文件有 64 处宏续行。需要 CT 支持多行宏，或明确报“宏必须单行”。

### 阻塞 4：超长宏被静默截断（根因在前端词法层，不是发射端）

最小复现一（截断后语法不完整，错误到 `cc` 才出现）：

```c
// b4.ct：505 字符的单行宏
#define is_kw(x) (strcmp(x, "k0") == 0 || … || strcmp(x, "k19") == 0)
int main(void){ return is_kw("k1"); }
```

```console
$ ~/.local/bin/ct build b4.ct -o b4
'cc' -std=c99 -I '.ctbuild' '.ctbuild/b4.c' '-o' 'b4'
b4.ct:5:23: error: expected ')'
$ echo $?
1
$ grep 'define is_kw' .ctbuild/b4.c | wc -c
159
```

最小复现二（截断点落在合法边界，整条链路 rc=0，行为被静默改掉）：

```c
// s.ct：源码宏 181 字符；前 159 字符已是完整表达式，后面的 "+ 99" 被丢掉
#define S (1+2+3) <此处 141 个空格> + 99
int main(void){ printf("%d\n", S); return 0; }
```

```console
$ ~/.local/bin/ct build s.ct -o s
$ echo $?
0
$ ./s
6
$ echo $?
0
```

`S` 本应为 105（1+2+3+99），实际输出 6；`ct`、`cc`、运行全部 rc=0，没有任何诊断。

根因（ct-lang v0.44.1 源码）：

- `frontend/lex/Lexer.h.ct:18` `#define MAX_TEXT 160`；T_PP 分支（约 92–96 行）按
  `if (n + 1 < MAX_TEXT)` 拷字符，最多 159 字符，**且不置 `toktrunc`**；同文件 T_ID
  分支（108–110 行）在同样截断时会置位。
- `frontend/parse/Parser.h.ct:1313` 用 `snprintf(…, MAX_TEXT, …)` 把 token 文本拷进
  `Arena::Node.text`（`runtime/arena/Arena.h.ct:35` `char text[160]`），形成第二道上限。
- 发射端只把 `Node.text` 原样写出，输入到它手里时已经是 159 字符。

**定性更正**：原来说“发射端定长缓冲”不成立。实际是**前端词法层先截断且不报错，解析层
再截一次，发射端不是元凶**。`ct build` 本身不报宏被截断；截断落在合法边界时生成 C 与
源码不一致但 rc=0，行为被静默改掉。本文件有 11 个宏超过 159 字符（`is_keyword`、
`ast_*`、`p_is_*`、`p_reject_results` 等）。

四项之外，PH-13 已记录的两条 CT 缺陷仍会影响多单元组织：导出头里 `pub struct` 内嵌
`Map<K, 用户 struct>` 生成不完整类型；指针变量上的 `.` 方法调用发射 `S_f(&p)`（传 `S**`）。

## 7. 多单元化登记（后续项，待立卡）

| 字段 | 内容 |
| --- | --- |
| 要动什么 | ① 11 个超过 159 字符的宏改短或改函数；② 64 处宏续行合并；③ 修掉阻塞 1/2/3 的源码形态；④ 按 `.h.ct` / `.m.ct` 拆成多单元，构建改用 `ct build -I`；⑤ 复核 `pub struct` 内嵌 `Map` 与指针接收者两条缺陷 |
| 为什么现在不做 | 本相卡片交付物是单文件 `ct/rill_ct.ct`，判据已全绿；①–③ 会把已验证的词法/JSON 构造代码重做一遍，风险大于收益；多单元化不是本相判据 |
| 现有卡位 | 无。PH-13 §5 风险 2 只裁定“头/实现拆分未复核前保持单文件”，未承诺拆分；PH-14…PH-21 没有承载多单元化的任务 |
| 登记位置 | **待立卡**（不占相号，不自行加 PH-22） |
| 触发条件 | 再次撞上单文件 64 函数上限；或某个相要求 `.h.ct` 导出；或构建时间/模块化成为门禁问题 |
| 建议时点 | 在任何“必须多单元”的相之前立卡；立卡前不把 `ct build` 写进门禁 |

## 8. lessons

- `gate:` **事实更正**：PH-13 是单文件 `ctc` 构建，**没有“已验证的多单元拆分方式”**可供
  延续；此前“延续词法层的拆分方式”这个前提不成立。后续排活不要按这个前提估算工作量。
- `gate:` `ct build` 当前不接受前向 typedef、`impl` 尾 `;`、续行宏，并会把超过 159 字符的
  宏静默截断；最后一条根因在前端词法层（`Lexer.h.ct` T_PP 分支，`MAX_TEXT=160`，且不置
  `toktrunc`），解析层再 `snprintf` 一次，不是发射端。触发信号：`ct build` 报
  `unexpected token` / `expected a type`，或 `cc` 在宏调用处报括号不匹配；截断落在合法
  边界时则整条链路 rc=0、行为被静默改掉。
- `gate:` 断言根因前先确认证据落在哪一层：同一现象要能指到具体阶段（词法 / 解析 / 发射）
  的代码位置与边界值，不能凭“输出看起来像”下结论。本条的更正就是反例。
- `gate:` `--bucket negative --kind error` 会跨相选中 `negative/load/**`；按卡验收要用
  `--case` 过滤到本层，或显式把范围外红单列，不能混进通过。
- `spec:` 单文件 + ctc 64 函数上限意味着新增解析函数要走宏或合并；多单元化待立卡，
  不在本相用“顺手重构”消化。
- `rejected:` 不为迁就 `ct build` 改写已验证代码；不把 PARTIAL 包装成 PASS；不改 golden、
  不放宽判据。

## 9. 全量计数与复跑

```text
AST golden        23/23 PASS
parse 负例        10/10 PASS（stage/code/line/col 逐条相等）
AST 对拍          82 源：60 成功 + 22 诊断，0 差异（exit 0）
token 回归        82 源：73 成功 + 9 诊断，0 差异（exit 0）
ct/test.sh        12 + 23 + 19 全 PASS
negative/load     7 条 FAIL（PH-15，范围外）
产生式映射        31/31（27 条 EBNF 命名 + 4 条内联形态）
Python/golden     未改
```

复跑：

```console
$ bash ct/build.sh
built /Users/samxx/trae-ws/rill-dsl/ct/bin/rill_ct
$ ./ct/test.sh
...
ct/test.sh: PASS
$ python3 tools/diff/diff.py --layer ast
== layer=ast
   sources=82 ok=60 diagnostics=22 diffs=0
   RESULT: PASS
== total diffs: 0
```
