# PH-18 收口：CT 格式化与 round-trip（P6）

> 卡面 `docs/phases/PH-18/card.md`；差异报告 `docs/reviews/diff/PH-18.md`；
> 单文件冻结结论见迁移卡 M-5（`docs/phases/pending/ct-multiunit.md`）。
> 只本地提交，未 push、未打 tag。

## 1. 结论

GO。`fmt --compress` / `fmt --display` 在 71 个 round-trip 输入上与 Python 参考实现
逐字节一致，round-trip（压缩→展示→压缩）的文本与 AST 全绿；token/ast/error/eval 四层
回归 0 差异；`ct/test.sh` 与 `tools/check.sh all` 通过。

沿用多单元架构，新增 `ct/src/formatter/formatter.h.ct` 一个单元（32 个函数定义，
单元上限 256）。函数槽不再是约束，本相没有再为省槽做宏化或合并：`f_raw_width`、
`f_merges`、`f_display_space`、`f_value_replacement`、`f_expand_ref` 各自独立成函数，
与 Python 的 `formatter.py` 同名函数一一对应。

**E-5（`Bytes`/`Opaque`）仍未通过**，本相不具备触发条件，判据原样挂着。

## 2. 退出判据（E）

| ID | 条件 | 结果 | 证据 |
| --- | --- | --- | --- |
| E-1 | 71 个 round-trip 输入通过（压缩→展示→压缩 AST 等价） | 通过 | `--mode roundtrip`：`corpus=71 diffs=0`；三段文本与两侧 AST 全等 |
| E-2 | 压缩/展示逐字节与 Python 一致 | 语料范围内通过 | `--mode compress` / `display` 各 `corpus=71 diffs=0`；口径外差异见差异报告 §7 |
| E-3 | 含空格/双引号/单引号长词各一例 | 通过 | `directed=3 direct_diffs=0`；输出见差异报告 §4 |
| E-4 | `//map {` 与 `//map{` 容忍 | 通过 | `headers=2 header_diffs=0`（两种写法输出相同） |
| E-5 | `Bytes`/`Opaque` 不透传成文本、不报假成功 | **未通过（缺能力）** | `fmt` 只吃源码文本/token/AST，没有 Value 入口；见 §5 |
| E-6 | 任务清单逐项可独立验收 | 通过 | §3 逐项贴原始输出 |

## 3. 任务逐项 verify（原始输出）

| 任务 | verify | 原始输出 |
| --- | --- | --- |
| T1 压缩 | `python3 tools/diff/diff.py --layer fmt --mode compress` | `corpus=71 diffs=0` / `directed=3 direct_diffs=0 headers=2 header_diffs=0` / `RESULT: PASS` |
| T2 展示 | `python3 tools/diff/diff.py --layer fmt --mode display` | `corpus=71 diffs=0` / `directed=3 direct_diffs=0 headers=2 header_diffs=0` / `RESULT: PASS` |
| T3 可逆性 | `python3 tools/diff/diff.py --layer fmt --mode roundtrip` | `corpus=71 diffs=0` / `directed=3 direct_diffs=0 headers=2 header_diffs=0` / `RESULT: PASS` |
| T4 报告 | `test -s docs/reviews/diff/PH-18.md` | `test -s rc=0` |

四层回归与门禁（同一构建产物 `ct/bin/rill_ct`）：

```
token : sources=82 ok=73 diagnostics=9 diffs=0   RESULT: PASS
ast   : sources=82 ok=60 diagnostics=22 diffs=0  RESULT: PASS
error : sources=26 ok=0  diagnostics=26 diffs=0  RESULT: PASS
eval  : sources=19 ok=19 diagnostics=0 diffs=0   RESULT: PASS
ct/test.sh: PASS
== overall: PASS ==
```

## 4. 与卡面偏差

| # | 卡面 | 实际 | 影响 |
| --- | --- | --- | --- |
| 1 | 交付 `ct/src/formatter.h.ct`、`ct/src/formatter.m.ct` | 只产出 `ct/src/formatter/formatter.h.ct`；`.m.ct` 是映射单元、不能定义函数（PH-17 已实测），目录形式也与现有 `src/<unit>/<unit>.h.ct` 一致 | 判据不变；§2 的接口/实现同文件 |
| 2 | T1/T2/T3 各一次实现提交 | 三件共享同一单元，合并为一次实现提交（先例：PH-16-T1/T2/T3/T4） | 三条 verify 仍逐条独立可跑；按 hunk 拆会产生不可编译的中间态 |
| 3 | `tools/diff` 扩 fmt 层 | 新增独立的 71 例发现规则（kind 过滤 + 双宿主脚本），不复用 positive/negative 发现 | 语料与 `tests/phase12/support.py` 的选择规则对齐 |
| 4 | 逐字节对拍 | 只对 71 例语料与定向用例比字节；错误路径比 JSON 字段（两侧 `json.dumps` 空格不同，PH-13 起的既有契约） | 语料全为可词法正例，错误路径不进入本层 |
| 5 | E-5 透传或 `cannot_format` | 未实现：`fmt` 无 Value 入口，凭空加 `cannot_format` 是假实现 | E-5 记未通过，不挪判据 |

## 5. E-5 的诚实结论

`Bytes` / `Opaque` 只在运行期值里出现（`src/rill/value.py`），`fmt` 的输入是源文件文本，
中间产物是 token 流与 AST，没有任何路径能把一个 `Value` 交给格式化器。所以本相无法
构造 E-5 的触发条件；它继续以「缺能力」挂着，不记通过。

结构性旁证（非通过证据）：`formatter.h.ct` 只 `import common` / `import lexer`，不含
eval 或 value 依赖，卡 §5 风险 4 的触发信号未出现。

## 6. 单元与函数

| 单元 | 函数定义数 | 上限 |
| --- | --- | --- |
| `common.h.ct` | 29 | 256 |
| `lexer.h.ct` | 13 | 256 |
| `parser.h.ct` | 37 | 256 |
| `loader.h.ct` | 2 | 256 |
| `eval.h.ct` | 28 | 256 |
| `cli.h.ct` | 5 | 256 |
| `formatter.h.ct`（本相新增） | 32 | 256 |
| `main.ct` | 1（`main`） | 256 |

## 7. 允许与不允许的改动

允许且已做：`ct/src/formatter/**` 新增；`ct/src/cli/cli.h.ct` 加 `fmt`；`ct/src/main.ct`
分派；`tools/diff/diff.py` 的 fmt 层；本相文档；迁移卡 M-5 与冻结结论。

不允许且未做：改 `testdata/` golden；改 `src/rill/` 参考实现；改 harness 协议；
放宽既有判据；把 `Bytes`/`Opaque` 记成通过。

## 8. 口径外差异与缺陷登记

本相没有新增 CT 工具链或语料缺陷；`case_opts` 的目录拼接修复沿用 PH-17，eval 层 19 例
仍全绿。新增一条**参考实现候选缺陷**：

- 位置：`src/rill/formatter.py` 的 `_merges` 与 `_value_replacement` 用 `str.isalnum()`
  作词边界，而 Python/CT 两套词法器的裸词规则把所有非 ASCII 字节都当作词内容。
- 现象：非 ASCII 标点（`—`、`，`、emoji…）落在词边界时，Python 会去掉本应保留的
  空格/提前做长词替换，CT 不会。两个探针与完整说明见差异报告 §7。
- 为什么此前是假绿：71 例语料与 `tests/phase12/test_roundtrip.py` 都不含这类输入，
  所以任何「格式化与 Python 一致」的结论在没覆盖这一类时依然全绿；它既不会让既有门禁
  变红，也不会被既有门禁发现。
- 为什么不修：卡 §1 禁止改 Python 参考实现；要精确对齐需要给 CT 引入 Unicode 字母
  数字表，且用「非 ASCII 一律非字母数字」近似会在中文词边界反向出错。按卡登记，留给
  PH-5 的格式化完整化处理。

## 9. 提交与门禁

- `docs(reviews): 单文件 rill_ct.ct 冻结为参考实现`（M-5 结案）
- `feat(ct): PH-18-T1/T2/T3 格式化与 round-trip`
- `docs(diff): PH-18-T4 格式化差异报告`
- `docs(review): PH-18 收口`

门禁末行：

```
== overall: PASS ==
```
