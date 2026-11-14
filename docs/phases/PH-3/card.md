# PH-3 立项卡：语法与 AST（Parser 轨）

> 状态：正常开卡（判据在开工前写死，首个实现提交后冻结）。体系见 `docs/phases/README.md`。
> 对齐：`docs/planning/rill-0.1.0-phase-plan.md` phase 3；roadmap phase 3「完整 §三 产生式与 AST」。
> 规范版本快照：`1.9.0`。语言规范：`docs/RILL-0.1.0.md`（0.1.1，只读）。

## 0. 开卡必填

| 字段 | 值 |
| --- | --- |
| 编号 | `PH-3`，目录 `docs/phases/PH-3/` |
| 目标 | 按 §三 产生式把 token 流归约为完整 AST，只解析，不校验注册表、不执行。 |
| 范围 | 做什么：`program`/`header`/全部 `statement`、`verb_call` 可选主语、`arg := value`、`prep_block_stmt`、`prep_phrase*`、`parallel`/`[results]`、尾随块数量、AST 序列化与解析错误。不做什么：加载期校验、执行、格式化、宿主判断。 |
| 交付物清单 | 见 §2，每项一个路径。 |
| 任务清单 | 见 §3，每项一个交付物、一条 verify、一次实现提交、可单独回滚。 |
| 退出判据 | 见 §4，每条带命令或 golden 锚点。 |
| 依赖 | PH-2 的 token 流与关键字；token 信封 `rill-tokens-golden/0`；harness `--kind ast` 通道。 |
| 规范版本 | `1.9.0`。 |
| version-minor | `3`（收口目标产品版本 `0.3.0`）。 |
| 已知风险 | `verb_call` 可选主语、`[into]` 的 `]` 归约三分、裸词 value、`->$x` 顺序；见 §5。 |

## 1. 范围

| 做什么 | 不做什么 |
| --- | --- |
| `program := header* statement*`；`header := map_block \| fn_block` | 不建 map/fn 表、不查重（PH-4） |
| `statement` 全部分支：simple/prep_block/if/each/parallel/break/call | 不求值、不做段输出（PH-7/PH-8） |
| `verb_call := [subject] <动词> 宾语 [(状语)] prep_phrase*` | 不把角色/工具/权限写进 AST 语义 |
| `call_stmt` 的 `arg := value`；裸词在 value 位按 STRING 归约 | 不校验实参个数与默认值（PH-4） |
| 重复 `[ok]`/`[error]` 解析期拒绝；`[results]` 只允许 parallel 块级 | 不实现表面格式化（PH-5） |
| 宾语/介宾宾语接受 `$变量`（规范示例用法，见 §8 缺口 3） | 不判定 `$变量` 指向谁（PH-4/PH-7） |
| 状语与介宾按书写顺序保留（规范示例与 §三 冲突，见 §8 缺口 2） | 不解释状语并列语义 |

## 2. 交付物清单

| 路径 | 用途 |
| --- | --- |
| `src/rill/ast.py` | AST 节点词汇、字段顺序、`span` 语义、`--dump-ast` 序列化 |
| `src/rill/parser.py` | §三 产生式、尾随块归约、解析期错误 |
| `src/rill/cli.py` | `parse --dump-ast` 子命令 |
| `tests/phase3/test_ast_json.py` | AST 序列化与字段顺序的独立断言（T1 验收） |
| `testdata/0.1.0/positive/` | 每条语句形态至少 1 个正例（含 `value/five-branches`） |
| `testdata/0.1.0/negative/parse/` | 解析期负例与稳定错误码 |
| `testdata/0.1.0/expected/ast/` | AST golden（信封见 `expected/README.md`） |
| `docs/reviews/phase3-red.md` | 逐任务红证（baseline、命令、原始输出、退出码） |

## 3. 任务清单

每行“提交”含两个相邻提交：`test(...) 红`（只含夹具/断言/红证）是 `feat(...)` 的父提交（T-7）。
verify 命令必须能在本任务完成时单独跑绿，不借用整个 phase 门禁。

| ID | 交付物 | 提交 | 回滚 | verify | effort | 覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| PH-3-T1 | `src/rill/ast.py` | `test(parser): PH-3-T1 红` → `feat(parser): PH-3-T1 AST 节点与序列化` | `git revert <feat-sha> <test-sha>` | `python3 tests/phase3/test_ast_json.py` | S | E-1 |
| PH-3-T2 | `src/rill/parser.py`（program/header/block、verb_call 核心、map 展开）+ `cli.py` 的 parse | `test(parser): PH-3-T2 红` → `feat(parser): PH-3-T2 program 与基本语句` | `git revert <feat-sha> <test-sha>` | `PYTHONPATH=src python3 -m rill parse --dump-ast testdata/0.1.0/positive/map/space-header/source.rill --profile shell` | M | E-2 |
| PH-3-T3 | `src/rill/parser.py`（状语/介宾/赋值/管道/call_stmt/fn 模板） | `test(parser): PH-3-T3 红` → `feat(parser): PH-3-T3 调用、介宾与模板` | `git revert <feat-sha> <test-sha>` | `PYTHONPATH=src python3 -m rill parse --dump-ast testdata/0.1.0/positive/call/basic/source.rill --profile shell` | M | E-3 |
| PH-3-T4 | `src/rill/parser.py`（if/each/parallel/break/尾随块/prep_block_stmt） | `test(parser): PH-3-T4 红` → `feat(parser): PH-3-T4 控制流与尾随块` | `git revert <feat-sha> <test-sha>` | `PYTHONPATH=src python3 -m rill parse --dump-ast testdata/0.1.0/positive/parallel/results/source.rill --profile shell` | M | E-4 |
| PH-3-T5 | `src/rill/parser.py` 解析期错误码与位置 | `test(parser): PH-3-T5 红` → `feat(parser): PH-3-T5 解析错误码` | `git revert <feat-sha> <test-sha>` | `bash tools/check-0.1.0.sh --phase p2 --bucket negative --kind error` | S | E-5 |

## 4. 退出判据（exit-criteria）

首个实现提交后本节与 §3 冻结；变更只能关闭当前 phase 另开（§6.2）。

| ID | 条件 | 判定 |
| --- | --- | --- |
| E-1 | AST 节点词汇、字段顺序与 `span` 归一化可独立断言 | `python3 tests/phase3/test_ast_json.py` 退出 0 |
| E-2 | map 头与映射展开可归约：`//map{...}`、`` `cfg`.yml ``、`<r>` → `read` | `positive/map/space-header`、`positive/map/header`、`positive/map/verb-marker` 三条 AST 断言通过 |
| E-3 | 调用与介宾可归约：`<replace> localhost [with] prod (global) [in] $file`、`@ "f" "a"`、`//fn` 模板含 `\|>`、`->$x` 与 `\|>` 顺序 | `positive/simple/prep-phrases`、`positive/call/basic`、`positive/simple/assign` 三条 AST 断言通过 |
| E-4 | 控制流与尾随块可归约：`if $cfg <contains> debug=true`、`each $f [in] xs`、`break done`（含 `value` 五分支）、`[into] $cfg {}`、`parallel {…} [results]{} \|> …` | `positive/if/else-if`、`positive/each/bareword-value`、`positive/break/bareword-value`、`positive/value/five-branches`、`positive/block/into-independent`、`positive/parallel/results` 六条 AST 断言通过 |
| E-5 | `[results]` 出现在非 parallel、`@` 定义出现在正文、重复 `[ok]`/`[error]`、缺 block、`break` 后接动词全部有稳定解析错误 | `bash tools/check-0.1.0.sh --phase p2 --bucket negative --kind error` 退出 0，逐条断言 `code/line/col` |
| E-6 | 全部正例 AST golden 通过 | `bash tools/check-0.1.0.sh --kind ast --bucket positive` 退出 0 |
| E-7 | 每个语句形态至少 1 个 AST golden | `bash tools/check-0.1.0.sh --list --kind ast --bucket positive` 可枚举 |
| E-8 | 任务清单每项可独立验收（T-6） | 收口对照表逐项贴 `verify` 原始输出 |

## 5. 依赖与风险

| 类型 | 内容 |
| --- | --- |
| 依赖 | PH-2 的 token 流；`src/rill/cli.py` 的 SUT 退出码协议（0/2/3）；harness 的 `kind: ast` 与 golden 信封。 |
| 风险 1 | `verb_call` 可选主语：写成必选会让 `if $cfg <contains> debug=true` 不可归约。触发信号：E-4 第一条解析失败。 |
| 风险 2 | `[into]` 的 `]` 三分：尾随形式 / 普通介词 / 独立 `prep_block_stmt`。触发信号：`[into] $cfg {}` 被当普通介词。 |
| 风险 3 | 裸词 value：词法给 `BARE`，AST 必须在 value 位生成 STRING 节点。触发信号：AST 保留 `Bare` 节点。 |
| 风险 4 | `->$x` 与尾随块顺序：AST 必须保留书写顺序，不得解析期重排。触发信号：golden 子节点顺序与源码相反。 |
| 风险 5 | 规范 §三 与 §四 示例存在 10 处不一致（§8）；实现按示例与 §4.5 位置规则落地，不自行改规范。触发信号：§8 条目被实现悄悄“修正”。 |

## 6. 收口与 tag

- 收口时产品版本 `0.3.0`；annotated tag `v0.3.0`，message 含 `PH-3` 与收口提交 sha 前 7 位。
- 只推 tag，不推分支、不对外发布；分支推送与发布须用户显式指令。
- 收口对照表：`docs/reviews/closeout-3.md`（模板已建）。

## 7. 解析期错误码（PH-3 自定，实现契约）

规范 §4.20 只冻结 `E-01` / `E-02`（词法层），未给解析期错误码表（§8 缺口 5）。
本卡冻结 PH-3 的解析期错误码；PH-4 起只能新增，不得改号或改位置语义。

| 编号 | 触发 | 位置 |
| --- | --- | --- |
| `E-PARSE-MISSING-BLOCK` | `if`/`each`/`parallel`/尾随块/`prep_block_stmt` 缺 `{` | 期望 `{` 处的 token |
| `E-PARSE-RESULTS-CONTEXT` | `[results]` 出现在非 `parallel` 块级（含分支内） | `[results]` 的 `[` |
| `E-PARSE-FN-DEF-BODY` | 正文出现 `@ STRING <动词> … { … }` 定义形状 | `@` |
| `E-PARSE-DUP-OK` | 同一语句/循环出现第二个 `[ok]` | 第二个 `[ok]` 的 `[` |
| `E-PARSE-DUP-ERROR` | 同一语句/循环出现第二个 `[error]` | 第二个 `[error]` 的 `[` |
| `E-PARSE-BREAK-VALUE` | `break` 后接动词调用 | 动词的 `<` |
| `E-PARSE-UNKNOWN-PREP` | 方括号内不是介词表成员（§4.5 常用集） | 介词首字符 |
| `E-PARSE-HEADER-ORDER` | `header` 出现在 `statement` 之后 | 区块头 `//` |
| `E-PARSE-UNEXPECTED` | 其余语法错误（兜底） | 当前 token |

## 8. 规范缺口清单（只报告，不改正文）

| # | 位置 | 缺口 | PH-3 落地方式 |
| --- | --- | --- | --- |
| 1 | §三 `simple_stmt` | 产生式没有 `->$x`，但 §4.7、§4.15 与正例 `simple/assign` 都使用；`->` 与尾随块的书写顺序也无产生式 | 在 `simple_stmt` 尾部接受 `-> $变量`，与尾随块同放有序 `tail`，保留书写顺序 |
| 2 | §三 `verb_call` vs §4.13 示例 | 产生式是 `宾语 [状语] prep_phrase*`，示例 `<replace> localhost [with] prod (global) [in] $file` 把状语放在介宾之后 | 接受状语与介宾交错，按书写顺序存入同一 `post` 列表 |
| 3 | §4.3 | 宾语只写裸词/引号，但 §4.13、§4.18 示例用 `<send> $msg`、`<read> $path` | 宾语与介宾宾语接受 `$变量` 与 `.字段`；不判定指向 |
| 4 | §4.16 拼接 vs §4.17 示例 | 拼接只定义“引号段与变量相邻”，但示例 `` `cfg`.yml `` 是映射引用与裸词相邻 | 相邻的映射引用/裸词/数字按位置折叠为单个 STRING；引号段相邻因 token 不含原文长度暂不支持（列入遗留） |
| 5 | §4.20 | 只冻结 `E-01`/`E-02`，解析期无错误码表 | §7 自定 `E-PARSE-*` 并冻结 |
| 6 | §三 `prep_phrase` / §4.5 | `prep_phrase` 未限定 `]` 后不得跟 `{`，块头与介词靠 §4.5 位置表区分 | 在 `]` 后看 `{`：是则按尾随块归约，否则按介词短语 |
| 7 | §三 `program` vs §4.17 | `header*` 只允许在 program 起始，§4.17 又说 map 可“顶层或块内” | 只支持顶层 `header`；块内 map 留 CR |
| 8 | §三 `expr` / `pipe` vs `simple_stmt` | `expr` 的 `pipe` 不允许尾随块，`simple_stmt` 的 `|>` 每段可带尾随块；两处 `|>` 语义不同 | 分别用 `Pipe` 节点（条件/循环头）与 `SimpleStmt.pipe`（语句链） |
| 9 | §4.13 / §4.20 `W-01` | `each $f [in] xs` 裸词归约为 STRING 后，AST 无法再判定“来源是裸词”，PH-4 的 `W-01` 失去依据 | PH-3 不保留来源标记；建议 CR 决定是否加 `source` 字段或让 PH-4 回读 span |
| 10 | §三 `value` / §4.8 | `$`（self）未出现在 `value` 产生式，`break $` 是否合法无定义 | 接受 `DOLLAR` 为 `Self` 节点，不宣称规范支持 |
