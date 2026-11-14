# RILL 0.1.x 词法约定（phase 2）

> 实现：`src/rill/lexer.py`；CLI：`rill tokenize <file>`；用例：`testdata/0.1.0/{positive,negative}/…`
> 规范依据：[RILL 0.1.1 正文](../RILL-0.1.0.md) §3.1、§3.2、§4.8、§4.16、§4.17、§4.19、§4.20。
> 本文冻结 phase 2 的 token 词汇与序列化，供 phase 3 直接消费；不修改规范正文。

## 1. 实现选型

实现语言为 **Python 3（仅标准库）**。理由：仓库现有工具链（`tools/rill_harness/`、`tools/checks/`、`tools/rill_stub/`）全部是 Python 3；仓库没有构建系统、没有依赖清单；harness 的 SUT 契约就是“子进程 + 退出码 + stdout JSON”，Python 包无需安装即可用 `PYTHONPATH=src python3 -m rill` 运行。后续 phase 3/4 可在同一包内继续，不引入第二套工具链。

`testdata/0.1.0/sut.json` 已从占位实现切换到：

```json
{"command": ["python3", "-m", "rill"], "env": {"PYTHONPATH": "src"}}
```

## 2. Token 序列化

```json
{"kind": "VERB", "text": "read", "line": 1, "col": 1}
```

- `line` / `col` 为 1 基，`col` 按 Unicode 码点计数；换行统一为 LF。
- 顺序固定为 `kind, text, line, col`；golden 信封为
  `{"schema": "rill-tokens-golden/0", "case": "<用例相对路径>", "tokens": [...]}`。
- 文件末尾固定追加一个 `EOF`（`text` 为空）；每条物理换行产生一个 `NEWLINE`。

## 3. Token 清单

| kind | text | 产生位置 |
| --- | --- | --- |
| `VERB` | 尖括号内原文 | `<read>` → `read`；位置在 `<` |
| `KEYWORD` | 关键字原文 | `if` / `else` / `else-if` / `each` / `parallel` / `break` |
| `BARE` | 裸词原文（保留 `\` 转义序列） | 主语、宾语、状语项、裸词 value |
| `NUMBER` | 数字原文 | 整数，见 §4.4 |
| `STRING` | 解码后的值 | 单引号或双引号字符串 |
| `VARIABLE` | 变量名，不含 `$` | `$cfg` → `cfg` |
| `DOLLAR` | `$` | `$` 后不跟标识符（self） |
| `FIELD` | 字段名，不含 `.` | `.host` → `host` |
| `MAP_REF` | 反引号内原文 | `` `cfg` `` → `cfg` |
| `MAP_HEADER` | `//map` | `//map{`、`//map {`、`// map {`；`{` 已被该 token 吞掉 |
| `FN_HEADER` | `//fn` | `//fn {` 等；`{` 已被该 token 吞掉 |
| `MAP_SHORT` | 短词原文 | `//map{}` 行模式，`[A-Za-z0-9_-]+` |
| `MAP_MARK` | 一个字符：`'` / `` ` `` / `<` | `//map{}` 行模式；块外 `<` 永远是 `VERB` |
| `MAP_LONG` | 标记符后到行尾的全部原文 | 不转义、不解析、不认引号 |
| `LBRACE` / `RBRACE` | `{` / `}` | 普通块；`//map{}` 的 `{` 在 header 里，闭合仍是 `RBRACE` |
| `LPAREN` / `RPAREN` | `(` / `)` | 状语 |
| `LBRACKET` / `RBRACKET` | `[` / `]` | 介词 |
| `ARROW` | `->` | 赋值 |
| `PIPE` | `\|>` | 管道 |
| `AT` | `@` | 函数调用 |
| `QUESTION` | `?` | 默认值 |
| `COMMA` | `,` | 状语并列项 |
| `NEWLINE` | `\n` | 语句边界 |
| `EOF` | 空串 | 文件末尾 |

说明：

- `<>` 不拆成两个 token：`VERB` 的 text 已包含动词名，位置指向 `<`。这样 phase 3 不必再拼 `<` + 名字 + `>`。
- `//` 后无 `{`（或 `map`/`fn` 后不是 `{`）整行按行注释处理，**不产生 token**，换行仍产生 `NEWLINE`。
- `,` 是 token；`:` 与 `=` **不是** token。因此 `backup:daily`、`timeout:30`、`debug=true`、`file:/etc/passwd` 各自是一个 `BARE`，符合 §4.1「`类型:值` 是裸词的一种形式，语法层不拆分」。

## 4. 切分规则

### 4.1 普通模式

- 空格与制表符只作分隔，不产生 token；换行产生 `NEWLINE`。
- 符号即边界：`< > ( ) [ ] { } | @ ? , $ ' " \`` 终止裸词。
- `->` 优先于裸词中的 `-`：`a.yml->$c` 切为 `a.yml` / `->` / `$c`。
- `|>` 同理；孤立的 `|` 报 `E-LEX-PIPE`。
- `//` 仅在 token 起始位置识别为注释/区块头；裸词内部的 `/`（含 `https://`）按字面保留。

### 4.2 `//` 头（§3.1）

读入 `//` 后跳过零个或多个空格/制表符；若读到 `map` 或 `fn`，再跳过零个或多个空格/制表符；下一个字符是 `{` 则产生 `MAP_HEADER` / `FN_HEADER`，否则整行按注释。因此 `//map{`、`//map {`、`// map {`、`//fn {` 都是头，`//map` 单独一行是注释。

### 4.3 `//map{}` 行模式（B1 裁定）

进入 map 块后，每行按 `短词 + 第一个非短词字符（标记符）+ 行尾（长词）` 切分：

- 行首空白视为缩进，先跳过；空行只产生 `NEWLINE`。
- 短词 `[A-Za-z0-9_-]+` 后**不再跳过空白**；第一个非短词字符必须是 `'` / `` ` `` / `<`，否则报 `E-01`。所以 `cfg `configuration` 在空格处报错。
- 标记符只占一个字符；其后到行尾全部是 `MAP_LONG`，包括 `"`、`'`、`//`、`}` 和尾随空格。
- 行首（跳过缩进后）第一个字符是 `}` 时产生 `RBRACE` 并退出行模式；`}` 出现在长词中间不闭合区块。
- 块内不启动动词扫描：`r<read` 是 `MAP_SHORT r` + `MAP_MARK <` + `MAP_LONG read`；块外 `<r>` 是 `VERB r`。
- 到 EOF 仍未遇到行首 `}` 报 `E-LEX-MAP-UNCLOSED`。

### 4.4 字符串、裸词与数字

- 单引号：纯字面，不转义，内部字符原样（`'a [b]'` → `a [b]`）；不能跨行。
- 双引号：仅 `\"` 与 `\\` 两个转义；其他 `\x` 报 `E-LEX-ESCAPE`；不能跨行。
- 裸词：`\` 后只允许 `[ ] ( ) < > { } $ \`；其他报 `E-LEX-BARE-ESCAPE`。转义序列原样保留在 `text` 中（`caf\[e\]` 不还原成 `caf[e]`）。
- 数字：`-?[0-9]+`，且后面不能紧邻词字符（字母、数字、`_`、`-`、`.`、`:`、`\`）。因此 `42` 是 `NUMBER`，`42abc`、`1.5`、`prod-db:5432` 是 `BARE`。
- `$` 后跟 `[A-Za-z0-9_]+` 是 `VARIABLE`，否则 `DOLLAR`。
- `.` 只有在 token 起始位置、后跟标识符、且前一字符不是词字符时才是 `FIELD`；否则并入裸词。这样 `` `cfg`.yml `` 切为 `MAP_REF(cfg)` + `BARE(.yml)`，而 `.host` 是 `FIELD(host)`。

## 5. 词法错误码

| code | 触发 | 规范来源 |
| --- | --- | --- |
| `E-01` | map 行短词后第一个非短词字符不是 `'` / `` ` `` / `<` | §4.20 |
| `E-02` | 正文 `<` 到行尾仍未遇到 `>`；文案含“映射定义必须在 `//map{}` 块内” | §4.20 |
| `E-LEX-QUOTE` | 单/双引号到行尾或 EOF 未闭合 | 实现补充 |
| `E-LEX-ESCAPE` | 双引号内出现 `\"` `\\` 以外的转义 | §4.16 + 实现 |
| `E-LEX-BARE-ESCAPE` | 裸词内出现 §4.16 列表以外的转义 | §4.16 + 实现 |
| `E-LEX-MAP-ENTRY` | map 行缺少短词 | 实现补充 |
| `E-LEX-MAP-UNCLOSED` | `//map` 到 EOF 未闭合 | 实现补充 |
| `E-LEX-MAP-REF` | 反引号引用未闭合 | 实现补充 |
| `E-LEX-VERB` | `<>` 为空 | 实现补充 |
| `E-LEX-PIPE` | 孤立的 `\|` | 实现补充 |
| `E-LEX-GT` | 孤立的 `>` | 实现补充 |

诊断形状固定为 `{"error": {"stage": "tokenize", "code", "line", "col", "message"}}`，退出码 2。

## 6. 规范未定死、phase 2 暂定的事项

以下不是 phase 2 自行改规范，而是词法层必须选一个切分才能产出 token；均已用用例固化，等规范补条后可直接替换：

1. **`NUMBER` 没有词法定义**。正文只有产生式名。phase 2 取 `-?[0-9]+` 且不紧邻词字符；小数 `1.5` 暂按裸词。
2. **`.字段` 与含 `.` 的裸词**没有消歧规则（评审 R-23 已知）。phase 2 用“token 起点 + 前字符非词字符”判 `FIELD`；因此对象位 `.env` 也会成 `FIELD`，留给 phase 4 按语法位置处理。
3. **反引号引用与相邻字面后缀**（`` `cfg`.yml ``）没有切分规则。phase 2 产出 `MAP_REF` + 相邻 `BARE`，拼接语义留给 phase 3/5。
4. **`//map{}` 单行形式**与“长词到行尾”冲突（决策材料 B.2 已指出）。phase 2 规定 `}` 只有作为行首（跳过缩进）第一个字符才闭合；`//map{cfg`x}` 的长词是 `x}`，区块不闭合。
5. **map 行缩进与空行**正文未写。phase 2 允许行首空格/制表符与空行。
6. **`//` 头里的“空格”**是否含制表符未写。phase 2 接受空格与制表符。
7. **裸词转义集合之外**（`\|` `\@` `\?` `\'` `\ `` `\ `）是字面还是错误未写。phase 2 报 `E-LEX-BARE-ESCAPE`。
8. **空动词 `<>`、空长词、空反引号引用**未写。phase 2 对空动词报错，空长词/空引用暂允许，留给加载期。
9. **逗号**不在 §二 符号总表，但 §4.4 把它当并列分隔符。phase 2 产出 `COMMA`；`:` 与 `=` 保持裸词内字面。
10. **关键字识别位置**：正文说“语句起始位置优先”。phase 2 在任何位置对精确匹配产出 `KEYWORD`；与“关键字作普通名词/主语时必须加引号”一致。
11. **变量名、字段名与动词名的字符集**未写。phase 2 取 `VARIABLE = $[A-Za-z0-9_]+`、`FIELD = .[A-Za-z_][A-Za-z0-9_]*`、`VERB` 为 `<` 与 `>` 之间除换行外的原文（内部空格原样保留，交给 phase 4 校验）。
12. **BOM** 未写。phase 2 不剥离；带 BOM 的文件首字符会进入裸词。

## 7. A2 / B1 落实与仍存在的文档差异

- A2（裸词在 `value` 位合法、按 `STRING` 处理）：正文 §三、§4.13、§4.15、§4.18、§4.20 已更新；词法层把裸词统一产出 `BARE`，phase 3 负责在 `value` 位生成 `STRING` 节点。
- B1（`//map{}` 行模式、块内 `<` 是标记符）：正文 §3.1、§3.2、§4.17、§4.20 已更新，phase 2 已按行模式实现并有正例 `positive/tokens/map-verb-marker`。
- 仍不一致、phase 2 不改的地方：
  - `testdata/0.1.0/pending/` 下仍有 4 个 A/B 阻塞用例（phase 3/4/5/8 所有），B1/A2 已裁定后应各自转为正常用例，但不在 phase 2 切片内。
