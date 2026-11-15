# RILL 解析期缺陷登记：`$"..."` 与「引号串在前」的相邻拼接

> 状态：open。2026-11-15 由 `examples/tour/` 样例集发现，单独记账，**尚未修复**。
> 复现基线：`ct/bin/rill_ct`（当日主干构建）与 `PYTHONPATH=src python3 -m rill`。
> 样例侧处理：`examples/README.md` §4 已说明样例一律不使用这两种写法。
> 本文件不动 `ct/src`、不改 golden、不改判据。

## 0. 两条的性质不同

| 编号 | 写法 | 两侧行为 | 性质 |
| --- | --- | --- | --- |
| PD-1 | `$"-x"`（`$` 紧跟字符串） | CT 解析失败；Python 解析通过并正常运行 | **实现缺陷**（CT 与参考实现分歧） |
| PD-2 | `"n="$v`（引号串在前的相邻拼接） | 两侧都在解析期失败，行列一致 | **共同缺陷**（设计层面，方向待裁定） |

两条都只影响「相邻」判定，不涉及 `$var` / `` `map` `` / `.field` 的正常用法。

## 1. PD-1：`$"..."`，CT 与参考实现分歧

### 1.1 最小复现（两行）

```console
$ cat pd1.rill
<read> /etc/hosts |> <send> $"-x" [to] user
<send> 'after' [to] user
```

```console
$ ct/bin/rill_ct run pd1.rill
{"error":{"stage":"parse","code":"E-PARSE-UNEXPECTED","line":1,"col":30,"message":"语句后出现意外 token -x"}}
$ echo $?
2
```

```console
$ PYTHONPATH=src python3 -m rill run pd1.rill
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

修 CT，让它对齐 Python：`p_raw_len` 的 `TK_DOLLAR` 分支返回 1，与 `f_raw_width` 一致。
配套要求：

- 新增 positive fixture：`$` 紧跟 STRING，且 `$` 在管道/块内是非空字符串（顶层 `$`
  是 `null`，会走到 `E-RUN-CONCAT`，测不到解析差异）；
- eval 层补 1 例两侧对拍，AST 断言按 §4.17 归一化比较；
- 不因此放宽任何既有判据。

### 1.4 时机与影响面

- 等 **PH-21 收口之后**再改 `ct/src`；本文件只做记录。
- 影响面：仅 `$` 与紧邻词元的拼接判定；不影响 `$var"-x"`（两侧都正常）。

## 2. PD-2：`"n="$v`，两侧一致的共同缺陷

### 2.1 最小复现（两行）

```console
$ cat pd2.rill
<env> PATH -> $v
<send> "n="$v [to] user
```

```console
$ ct/bin/rill_ct run pd2.rill
{"error":{"stage":"parse","code":"E-PARSE-UNEXPECTED","line":2,"col":12,"message":"语句后出现意外 token v"}}
$ echo $?
2

$ PYTHONPATH=src python3 -m rill run pd2.rill
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

### 2.3 待裁定：修实现还是修文档（不擅自定方向）

| 方向 | 做什么 | 代价 |
| --- | --- | --- |
| A 修实现 | 宽度函数返回源码原始宽度（STRING 含引号；双引号内的 `\"` `\\` 按源码宽度），两侧同步；补 fixture 与 §4.16 示例的 golden | 两个 parser 都要改；单/双引号/转义的相邻边界各留 1 例；两侧 formatter 与 parser 的测宽口径要对齐，避免出现第三种算法 |
| B 修文档 | 承认当前只支持「变量 / 映射引用在前」的拼接，把 §4.16 的示例改成可实现形态，并写明限制 | 规范正文要动（需走 CR）；「相邻即拼接」的表述要一起收窄；已发布样例无需改，但语法参考的可信度要靠下一版补回 |

在方向定下之前，样例与文档**不宣称**引号串在前的相邻拼接可用；PD-2 不记入任何
「已支持」清单。

## 3. 记账口径

- PD-1 是实现缺陷；PD-2 是设计与规范一致性问题。两条都不是「语义选择」。
- 修任何一条都要带 fixture + 对拍证据，未修完不得写成通过。
- 发现位置：`examples/tour/` 01–16 编写过程（提交 `c1b3e43`、`c744c79`、`c812a92`）。
