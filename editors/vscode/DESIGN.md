# RILL VS Code 插件：选型与实现说明

## 1. 结论

- 采用 **`DefinitionProvider` + `ReferenceProvider`**，不实现 Language Server。
- 函数符号解析用插件内的 **JavaScript 扫描器**，覆盖 `src/rill/lexer.py` 中与
  `@ "name"` 相关的词法规则；再用仓库的 Python lexer/parser 做逐文件对拍。
- 跨文件解析是**工作区索引**：扫描工作区内全部 `*.ri`，按函数名字符串精确匹配。
- 打包不依赖 node/npm/vsce，`tools/package_vsix.py` 直接生成 `.vsix`。

## 2. 为什么不用 LSP

| 因素 | 判断 |
| --- | --- |
| 功能面 | 目前只有“跳定义 + 查调用点”两个静态功能，没有跨文件类型检查、补全、诊断需求 |
| 依赖 | LSP 需要独立进程、JSON-RPC 生命周期与额外打包；DefinitionProvider 在扩展进程内即可完成 |
| 语法来源 | RILL 的函数名是 `@` 后的字符串字面量（规范 §4.18），不需要求值或类型推导 |
| 失败面 | 解析失败时直接返回 `null`，VS Code 不会跳转；LSP 还要额外保证 server 崩溃不影响编辑器 |
| 后续扩展 | 若将来需要诊断/补全，可在同一 `lib/scanner.js` 上再加 Provider，或整体迁移到 LSP，不影响语法文件 |

代价：每次跳转会在扩展进程内做一次工作区索引（带 mtime 缓存），文件极多时首次会慢；
LSP 的常驻索引会更省。当前仓库规模（对拍覆盖 128 个 `.ri`）下不构成问题。

## 3. 语法支持的来源

不凭印象定义语法，逐项对应仓库实现：

| 语法点 | 依据 | 插件落地 |
| --- | --- | --- |
| 关键字 `if/else/else-if/each/parallel/break` | `src/rill/tokens.py:KEYWORDS`、规范 §三 | `syntaxes/rill.tmLanguage.json#keywords` |
| 动词 `<name>` | 规范 §4.2、`lexer.py:_lex_verb` | `#verbs` |
| 介词 `[to]/[with]/[from]/[in]/[on]/[into]/[ok]/[error]` | 规范 §4.5、`parser.py:_PREPS` | `#prepositions` |
| `[results]` | 规范 §4.14（仅 `parallel` 块级） | `#prepositions`（仅着色，不做语义校验） |
| 单/双引号与转义 | 规范 §4.16、`lexer.py:_lex_string` | `#strings` |
| 反引号映射引用 | 规范 §4.17、`lexer.py:_lex_map_ref` | `#map-reference` |
| `//map{}` 行模式 | 规范 §3.1/§3.2、`lexer.py:_lex_map_line` | `#map-block` 区域 |
| `//fn{}` 区块 | 规范 §4.18、`lexer.py:_lex_comment_or_header` | `#fn-block` 区域 |
| 函数定义/调用 `@ "name"` | 规范 §4.18、`parser.py:_parse_fn_def/_parse_call_stmt` | `#fn-definition`、`#function-call` |
| 变量 `$x` / self `$` / 字段 `.x` | 规范 §4.7/§4.8、`lexer.py:_lex_dollar/_lex_field` | `#variables`、`#fields` |
| `|>` / `->` / `?` | 规范 §二/§4.6/§4.15 | `#operators` |

展示态格式化（`src/rill/formatter.py`）只影响空白与引号形态，不引入新 token；
插件的引号正则按 formatter 的“单引号优先、双引号仅 `\"`/`\\`”口径写。

## 4. 符号解析规则

`lib/scanner.js` 复刻 lexer 的状态机，只记录函数名：

1. `//fn{}` 顶层（`fnDepth === 1`）的 `@ STRING` 登记为**定义**；
2. 正文（`fnDepth === 0`）的 `@ STRING` 登记为**调用点**；
3. `fnDepth >= 2`（函数体内部）的 `@` 在 RILL 中非法，不登记；
4. `//map{}` 行、注释、字符串、反引号引用里的 `@` 不会被当成函数；
5. `@` 与名字之间只允许空格/制表符；跨行不构成函数名；
6. 双引号名字按 lexer 规则解码 `\"`/`\\`，单引号名字原样保留；
7. 未闭合字符串/动词/反引号、非法双引号转义时停止扫描，不猜后续名字。

跳转规则（`lib/symbols.js`）：

- 光标必须在函数名的字符串**内容**上（不含引号）；
- 调用点按名字精确匹配；同文件定义优先，其次按 uri 排序返回全部同名定义；
- 目标为 0 个时返回 `null`，不跳到“看起来像”的其他符号；
- 引用/调用点（Shift+F12）列出工作区所有同名 `@ "name"`。

## 5. 已知局限

1. **RILL 0.1.x 没有 import/模块机制**。同一个程序内的函数定义才参与加载期校验；
   跨文件跳转是编辑器导航能力，跨文件目标对当前文件的 `check/run` 不一定可见。
   `examples/vscode/cross-file/` 已按这个事实写注释。
2. **同名函数多文件定义时返回全部候选**，由 VS Code 候选列表选择；不替用户猜“最近的那个”。
   语言加载期对同一程序内重名取首个定义（`loader.py:_collect_functions`），插件不改写这个语义。
3. **语法高亮是启发式**：`//fn{}` 区域结束标记取列首 `}`（仓库 formatter 的输出形态）。
   若手工把 `//fn{}` 整体缩进、且函数体结束括号也顶格，区域可能提前结束。
4. **不做语义校验**：未知动词、未知介词、实参数量不匹配由 `check`/`load` 负责，插件不重复实现。
5. **不处理超长文件/超大工作区**：默认最多索引 5000 个 `.ri`，并跳过 `.git/node_modules/dist/out/build/.ctbuild/.venv`。
6. **位置列宽**按 UTF-16 码元计数（VS Code 口径）；Python 侧对拍数据已换算成同一口径。

## 6. 验证方式与结果

`test/run-tests.js` 做三件事：

1. 调 `test/oracle.py`，用仓库 `src/rill/lexer.py` 产出全部 `.ri` 的函数定义/调用点，
   同时用 `parser.py` 的 AST 交叉核对名字集合；
2. 与 `lib/scanner.js` 逐文件比对 `name/line/character/length`；
3. 跑同文件、跨文件、注释/字符串/map/函数体嵌套/转义名/未闭合输入等边界用例，
   并校验 `package.json`、语法 JSON、include 引用和正则可编译。

实测（2026-11-15，仓库根目录）：

```text
oracle: 128 个文件对拍通过，10 个 lex 错误文件跳过
checks: 544, failed: 0
PASS
```

`python3 tools/package_vsix.py` 生成并自检 `.vsix`，输出包含条目数与解压后字节数。
