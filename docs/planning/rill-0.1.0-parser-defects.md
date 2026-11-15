# RILL 解析期缺陷登记：`$"..."` 与「引号串在前」的相邻拼接

> 状态：open（PD-2 已裁定 A／修实现，尚未动代码）。2026-11-15 由 `examples/tour/` 样例集发现并单独记账。
> 复现基线：`ct/bin/rill`（当日主干构建）与 `PYTHONPATH=src python3 -m rill`。
> 样例侧处理：`examples/README.md` §4 已说明样例一律不使用这两种写法。
> 本文件不动 `ct/src`、不改 golden、不改判据。

## 0. 两条的性质不同

| 编号 | 写法 | 两侧行为 | 性质 |
| --- | --- | --- | --- |
| PD-1 | `$"-x"`（`$` 紧跟字符串） | CT 解析失败；Python 解析通过并正常运行 | **实现缺陷**（CT 与参考实现分歧） |
| PD-2 | `"n="$v`（引号串在前的相邻拼接） | 两侧都在解析期失败，行列一致 | **共同缺陷**（已裁定：A／修实现，见 §2.3） |

两条都只影响「相邻」判定，不涉及 `$var` / `` `map` `` / `.field` 的正常用法。
PD-1 与 PD-2 的修复合并进行：口径统一由同一个宽度来源给出，不各自改常量（见 §2.4）。

## 1. PD-1：`$"..."`，CT 与参考实现分歧

### 1.1 最小复现（两行）

```console
$ cat pd1.ri
<read> /etc/hosts |> <send> $"-x" [to] user
<send> 'after' [to] user
```

```console
$ ct/bin/rill run pd1.ri
{"error":{"stage":"parse","code":"E-PARSE-UNEXPECTED","line":1,"col":30,"message":"语句后出现意外 token -x"}}
$ echo $?
2
```

```console
$ PYTHONPATH=src python3 -m rill run pd1.ri
# stderr 前半是 /etc/hosts 原文，最后一行是 -x
{"ok": true, "value": "after", "error": null, "host_meta": {"stdio": {"channel": "stderr", "text": "after"}}, "host": {"profile": "shell", "principal": {"kind": "os-user", "name": "samxx"}}}
$ echo $?
0
```

同一份脚本：Python 把 `$"-x"` 解析成 `Self + String` 拼接并跑完；CT 在第 1 行第 30 列
（`-x` 的起始列）报解析错误，退出码 2。

### 1.2 根因

- CT：[parser.h.ct](file:///Users/samxx/trae-ws/rill-dsl/ct/src/parser/parser.h.ct#L605-L611)
  的 `p_raw_len` 对 `TK_DOLLAR` 返回 `cp_len(t->text) + 1`。`$` 的文本就是 `"$"`，
  于是宽度算成 2 列，而它在源码里只占 1 列，下一个 token 的 `col` 对不上
  `p_adjacent` 的期望，被判成"不相邻" → `$` 之后即语句结束 → `E-PARSE-UNEXPECTED`。
- Python：[parser.py](file:///Users/samxx/trae-ws/rill-dsl/src/rill/parser.py#L34-L43)
  的 `_raw_len` 对 `DOLLAR` 返回 1，所以相邻成立。
- CT 自己的 formatter 也取 1：`f_raw_width` 里 `TK_DOLLAR` 分支
  （[formatter.h.ct](file:///Users/samxx/trae-ws/rill-dsl/ct/src/formatter/formatter.h.ct#L152-L186)）。
  也就是说 CT 内部 parser 与 formatter 两套口径，parser 是错的一侧。

### 1.3 修复方向（已定）

修 CT，让它对齐 Python：`$` 的相邻宽度必须是 1。**不单独改 `p_raw_len` 里的
`TK_DOLLAR` 常量**——按 §2.4 的统一口径改造，让 `parser` 与 `formatter` 从同一个
宽度来源取值，PD-1 与 PD-2 在同一个提交里一起转绿。

配套要求：

- 新增 positive fixture：`$` 紧跟 STRING，且 `$` 在管道/块内是非空字符串（顶层 `$`
  是 `null`，会走到 `E-RUN-CONCAT`，测不到解析差异）；
- eval 层补 1 例两侧对拍；这一例 Python 侧本来就是正常路径，不属于预期差异；
- 不因此放宽任何既有判据。

### 1.4 时机与影响面

- 等 **PH-21 收口之后**再改 `ct/src`；本文件只做记录。
- 影响面：仅 `$` 与紧邻词元的拼接判定；不影响 `$var"-x"`（两侧都正常）。

## 2. PD-2：`"n="$v`，两侧一致的共同缺陷

### 2.1 最小复现（两行）

```console
$ cat pd2.ri
<env> PATH -> $v
<send> "n="$v [to] user
```

```console
$ ct/bin/rill run pd2.ri
{"error":{"stage":"parse","code":"E-PARSE-UNEXPECTED","line":2,"col":12,"message":"语句后出现意外 token v"}}
$ echo $?
2

$ PYTHONPATH=src python3 -m rill run pd2.ri
{"error": {"stage": "parse", "code": "E-PARSE-UNEXPECTED", "line": 2, "col": 12, "message": "语句后出现意外 token 'v'"}}
$ echo $?
2
```

两侧同错、同行同列（唯一区别是 Python 的 message 带引号）。

### 2.2 根因：相邻宽度按 token 文本长度算，不含引号

两个实现里的宽度函数注释都写「token 在源码里的原始宽度」，但 `STRING` 分支落到默认的
`len(text)`：不含两端引号，比真实宽度少 2 列。同一个函数里 `MAP_REF` 却加了 2 列
（反引号），说明「原始宽度」的口径本身没有贯彻到底。

- CT：[parser.h.ct](file:///Users/samxx/trae-ws/rill-dsl/ct/src/parser/parser.h.ct#L605-L611)
- Python：[parser.py](file:///Users/samxx/trae-ws/rill-dsl/src/rill/parser.py#L34-L43)
- 两侧 formatter 的测宽函数（CT `f_raw_width`）会回到源码行里扫引号，是另一套口径。

后果是规范 §4.16 表格里的拼接示例 `"查询到 "$count" 条"` 在当前两侧实现里都到不了
解析成功：[RILL-0.1.0.md](file:///Users/samxx/trae-ws/rill-dsl/docs/RILL-0.1.0.md#L409)
（§4.16「拼接」行）。这是规范与实现不一致，不是 CT 分歧。

### 2.3 已裁定：A／修实现（不改规范）

2026-11-15 裁定走 A：**修实现，规范 §4.16 不动**。依据一句话：§4.16 的
`"查询到 "$count" 条"` 是给用户看的契约，改弱规范等于把实现与规范的不一致藏起来。

因此：

- 不修改 `docs/RILL-0.1.0.md`，不改写 §4.16 的示例与「相邻即拼接」表述；
- 修复目标是让 CT 按 §4.16 把 `"n="$v` 解析成 `Concat(String, Variable)`；
- 修复前样例与文档仍**不宣称**该写法可用，PD-2 不记入任何「已支持」清单。

### 2.4 统一口径：一个宽度来源，不许各改各的

PD-1 的根因就是 `p_raw_len`（parser）与 `f_raw_width`（formatter）对同一个 token 算出
不同宽度。这次修复不再往两个函数里各加常量，而是**先在词法期算出唯一宽度**：

- `Token` 增加一个 `raw_len` 字段，由 lexer 在产词时按源码实际占位写入：
  STRING 含两端引号（双引号内的 `\"` `\\` 按源码宽度计），MAP_REF / VERB 含反引号或
  尖括号，VARIABLE / FIELD 含 `$` 或 `.`，DOLLAR 为 1，裸词/数字为文本宽度；
- `p_adjacent` 只读 `prev->raw_len`，`f_raw_width` 改为直接返回 `t->raw_len`，
  删掉 formatter 里回扫源码行的那段宽度逻辑；
- 结论只有一个：同一个 token 在 parser 与 formatter 里的宽度恒等，PD-1 / PD-2 由同一次
  改造一起解决，不出现第三种算法。

### 2.5 验收：fixture + 对拍，且把新增分歧登记为「预期差异」

修完必须同时具备：

| 项 | 要求 |
| --- | --- |
| positive fixture | §4.16 的形态各 1 例：`"n="$v`、`"a "$v" b"`、单引号同类、双引号内含 `\"`/`\\`；另加 PD-1 的 `$"..."`（在管道或块内，`$` 为非空字符串） |
| harness | 上述用例按 `ast` / `run` 的 kind 落盘，golden 重新生成，`tools/check-0.1.0.sh --all` 转绿 |
| 对拍 | `python3 tools/diff/diff.py --layer parse` 与 `--layer eval` 都要跑；PD-1 用例两侧一致，不算差异 |
| 预期差异 | PD-2 用例在 Python 侧仍是 `E-PARSE-UNEXPECTED`，CT 侧解析成功。这是**有意的两侧分歧**：Python 参考实现不跟着改，也不许为了对拍去改它 |
| 登记方式 | 在 `case.json` 增加可选字段 `expected_diff`（`layers` + `side` + `reason` + `anchor`），`diff.py` 命中时把差异计入单列的 `expected`、不计入 `diffs`；匹配必须精确到「用例 + 层 + 两侧摘要」，不做通配豁免，未登记或摘要不符一律按失败处理 |

`expected_diff` 是本次修复要新增的对拍机制（当前 `diff.py` 没有这个字段）；它只用于
登记「裁定过的有意分歧」，不能拿来放过普通回归。

### 2.6 时机与边界

- 等 **PH-21 收口之后**再动 `ct/src`、`testdata/`、`tools/diff/`；本文件只是记录。
- 本次（样例与缺陷记账）不改 Python 参考实现、不改 golden、不改判据。

## 3. 记账口径

- PD-1 是实现缺陷；PD-2 已裁定走 A（修实现、不改规范），不再是"待裁定"项。
- 两条共用一次宽度口径改造，修的时候不得只改其中一侧或其中一种 token。
- 修完要带 fixture + 对拍证据（PD-2 的新增分歧按 `expected_diff` 登记）；未修完不得写成通过。
- 发现位置：`examples/tour/` 01–16 编写过程（提交 `c1b3e43`、`c744c79`、`c812a92`）。
