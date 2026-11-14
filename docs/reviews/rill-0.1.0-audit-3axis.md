# RILL 0.1.0 三轴独立评审

> 基线：`84d6e08`（产品 `0.12.0`，语言规范 `docs/RILL-0.1.0.md` 0.1.1）。
> 范围：只读仓库与全部文档；不改实现、规范正文与测试。所有结论来自本次实跑或本次读到的原文；
> 引用其他评审结论时标“引用”，并复核其当前是否仍成立。
>
> 复跑命令（本轮均 exit 0，除非单条另注）：
> `bash tools/check-0.1.0.sh --all`；`bash tools/check.sh all`；`bash tools/check-fmt.sh --roundtrip`；
> `for f in tests/phase*/test_*.py; do python3 "$f"; done`；两条 quickstart `run`。

## 0. 基线数字

| 观察 | 实际值 | 说明 |
| --- | --- | --- |
| fixture | 85 | positive 56 / negative 26 / host 1 / smoke 2；compliance 83 + smoke 2 通过，0 fail/block/draft |
| 测试文件 | 39 | `tests/phase*/test_*.py` 全 rc=0 |
| round-trip | 71 fixture | `check-fmt.sh --roundtrip` exit 0 |
| 文档门禁 | PASS | 0 FAIL；`WARN 豁免` 实际 10 行 |
| AST golden | 23 个文件 | 覆盖 26/31 种节点 |
| 实现错误码 | 55 个字符串 | 规范 §4.20 只登记 3 个 |
| phase 退出判据 | 79 条 | 12 张卡 §4 合计 |
| examples | 2 个脚本 | `examples/quickstart/{shell,agent}.rill` |

---

## 轴一：文档一致性

**结论数字：核对 22 项——一致 8 项、矛盾 7 项、说明不足 7 项。**

### 一致（8）

- **A-C1 版本口径**：`README.md#L4` 写产品 0.12.0、`src/rill/__init__.py` 实测 `"0.12.0"`；规范 `#L1` 写 0.1.1；`testdata/0.1.0/README.md#L3` 写 0.1.1 定稿。三套版本用途不同且各自说明，未混用。
- **A-C2 quickstart 命令**：README §2/§3 的两条 `run` 实跑逐字得到文档所示 payload，`rc=0`（principal 用户名除外）。
- **A-C3 门禁计数**：`README.md#L84` 的“85 个 fixture；83 compliance + 2 smoke”与实际 summary 一致。
- **A-C4 文档地图链接**：README §8 的 6 个链接全部可解析；`doc_links` 0 FAIL。
- **A-C5 卡片结构**：12 张卡均有 `## 4` 退出判据，合计 79 条。
- **A-C6 宿主差异**：acceptance §4 的 6 条 host-specific 与实测一致，例如 Shell 未处理失败 `rc=1`、Agent `rc=0`。
- **A-C7 DOC-S2 表**：登记表 7 份与门禁中 7 条“冻结正文/副本/档案”逐条对应；另 3 条 `docs/design/**` 由 `DOC-S2-waivers.md#L28-L29` 声明为自动 WARN。
- **A-C8 用例约定**：`testdata/README.md` 的桶/kind/统计口径与 harness 实跑一致（pending 0，retired 4 不计）。

### 矛盾（7）

- **A1 规范 §六 示例 1/5/9 违反 §三 产生式，无法解析**
  - 位置：`docs/RILL-0.1.0.md#L548-L556`（示例 1）、`#L600-L607`（示例 5）、`#L652-L655`（示例 9）；对照 `#L95` 的 `verb_call` 必带“宾语”。
  - 证据：把三例原样写入 `/tmp` 后 `rill parse --dump-ast`：
    - 示例 1 → `rc=2 {"code":"E-PARSE-UNEXPECTED","line":2,"col":5,"message":"期望 动词 <name>，实际 'database'"}`
    - 示例 5 → `rc=2 {"line":3,"col":25,"message":"动词 'replace' 缺宾语"}`
    - 示例 9 → `rc=2 {"line":4,"col":39,"message":"动词 'replace' 缺宾语"}`
  - 性质：确有问题（规范内部矛盾）。
  - 影响：用户照“推荐形态”写即失败。根因有两个：`.字段` 作语句头、`<replace> [with] prod` 缺宾语。前者已在 `docs/phases/PH-7/card.md#L99` 登记（“登记，不实现”）；后者没有任何卡片登记。
- **A2 规范把独立 `[ok]/[error]` 称为合法语句，运行期却拒绝**
  - 位置：`docs/RILL-0.1.0.md#L219-L221`（“`[ok] $x { ... }` 是独立形式语句”）、`#L98`（`prep_block_stmt` 含 ok/error）。
  - 证据：`[ok] $x { ... }` `parse` rc=0；`run --profile shell --fakes ...` → `rc=2 {"stage":"run","code":"E-RUN-UNSUPPORTED","message":"独立 [ok] 没有前置 {value, ok}…"}`；`[error]` 同。
  - 性质：确有问题（已登记：`PH-7/card.md` §8 #5、`known-limits.md#L76-L77`）。
  - 影响：正文与 README §7 的口径相反；按正文写脚本的用户会在运行期中断。
- **A3 §4.16 的拼接示例无法解析**
  - 位置：`docs/RILL-0.1.0.md#L409`（`"查询到 "$count" 条"`）。
  - 证据：原样 `parse` → `rc=2 {"line":1,"col":14,"code":"E-PARSE-UNEXPECTED","message":"语句后出现意外 token 'count'"}`；反向顺序 `$count" 条"` 则 rc=0。
  - 性质：确有问题（已登记：`PH-3/card.md#L116` #4“引号段相邻…暂不支持”）。
  - 影响：正文唯一一条拼接规则不可执行，且无任何用例守它。
- **A4 §4.17 允许“块内” `//map`，解析器只接受顶层**
  - 位置：`docs/RILL-0.1.0.md#L440`（“只允许出现在语句边界（顶层或块内…）”）。
  - 证据：`if ... { //map{ a`b } ... }` → `rc=2 {"line":2,"col":1,"message":"期望 动词 <name>，实际 '//map'"}`。
  - 性质：确有问题（已登记：`PH-3/card.md#L119` #7“只支持顶层 header；块内 map 留 CR”）。
  - 影响：正文与实现相反，错误信息也不提示 CR 限制。
- **A5 `E-01`/`E-02` 的报错阶段与正文相反**
  - 位置：`docs/RILL-0.1.0.md#L511-L512` 标“解析期错误”；`src/rill/errors.py#L17-L19` 的 `LexError.stage="tokenize"`。
  - 证据：`rill tokenize negative/tokenize/map-bad-marker/source.rill` → `{"stage":"tokenize","code":"E-01",...}`；`unclosed-verb` → `{"stage":"tokenize","code":"E-02",...}`；两条 fixture 也断言 `stage=tokenize`。
  - 性质：确有问题（`PH-3/card.md#L94` 自己写作“词法层”，与正文的“解析期”不一致）。
  - 影响：按 `stage` 分支的调用方会把正文冻结的两个码归错层。
- **A6 7 张卡声明的收口对照表不存在**
  - 位置：`PH-4/card.md#L81`、`PH-5#L75`、`PH-6#L91`、`PH-7#L85`、`PH-8#L79`、`PH-9#L85`、`PH-10#L88` 均写“`docs/reviews/closeout-N.md`（收口时新建）”。
  - 证据：`ls docs/reviews/` 只有 `closeout-2/3/11/12.md`；`closeout-4…10` 缺失。
  - 性质：确有问题。
  - 影响：PH-4…PH-10 的收口证据链断，读者只能回读卡片与 red 文件。
- **A7 评审档案仍写着 0.1.1 已推翻的结论**
  - 位置：`docs/review/v1.3-final-response-audit.md#L1`（“已闭合：裸词 value 位非法”）、`v1.3-final-response-audit-2.md#L2`（“value 无裸词维持非法”）、`v1.3-closure-audit.md#L9`（“`expr` 与 `condition` 仍无产生式”）。
  - 证据：规范 `#L745` 的 A2 明确“`each $f [in] xs`、`break done`、`@ "name" bare` 保留原样且合法”；`#L121-L122` 已有 `expr`/`value` 产生式。
  - 性质：确有问题（历史档案未标“已被 0.1.1 取代”）。
  - 影响：读者若按档案核对闭合状态，会得出与现状相反的结论。这三份未列入 DOC-S2 豁免表。

### 说明不足（7）

- **A8 正文只登记 3 个错误码，实现实际产生 55 个**
  - 位置：`docs/RILL-0.1.0.md#L506-L514`（仅 `W-01`/`E-01`/`E-02`）；实现侧 55 个（`E-LEX-*` 10、`E-PARSE-*` 10、`E-LOAD-*` 6、`E-RUN-*` 8、`E-HOST-*` 20、`E_USAGE`）。
  - 证据：对 `src/` 全量正则提取并按 `tests/`+`testdata/` 反查，得到 55 个码；`E-RUN-FN-ARITY` 等 16 个在测试里 0 引用。
  - 性质：说明不足（契约只落在 PH-3 §7、PH-4 §8 两张卡里）。
  - 影响：规范读者无法从正文知道诊断码全集；`E_USAGE`/`E-RUN-*`/`E-HOST-*` 连卡片都没有集中表。
- **A9 “fmt 语法诊断 2”与实际不符**
  - 位置：`docs/planning/rill-0.1.0-known-limits.md#L53`。
  - 证据：对语法非法输入 `<read>` 执行 `rill fmt --display` → 原样输出 `<read>`、`rc=0`（`cmd_fmt` 只捕 `LexError`，不 parse）。
  - 性质：说明不足。
  - 影响：调用方误以为 `fmt` 会拒绝坏脚本；CI 里用 `fmt` 当语法检查会漏。
- **A10 README 对 `run` 退出码的口径前后不一**
  - 位置：`README.md#L78` 写“`run` 的未处理失败退出 1”；`README.md#L93` 又写 Agent“未处理失败固定退出 0”。
  - 证据：同一缺文件脚本：Shell `rc=1`，Agent `rc=0`。
  - 性质：说明不足。
  - 影响：只看 §5 的调用方会对 Agent 误判。
- **A11 `testdata/README.md` 保留 P1 时代的状态描述**
  - 位置：`testdata/0.1.0/README.md#L151`（“parse/check/run/fmt 仍返回退出码 3”）、`#L183`（“真实 parse 落地后删除 smoke 桶”）、`#L19`（“pending/ 保留为空”）。
  - 证据：四个子命令均已实现；smoke 桶仍被 acceptance 正式保留；`pending/` 下有 4 个 retired 目录（`#L57` 有解释）。
  - 性质：说明不足。
  - 影响：新加入者会按过期说明写用例或误判实现阶段。
- **A12 豁免理由“会破坏稳定锚点”不成立**
  - 位置：`docs/DOC-S2-waivers.md#L18`。
  - 证据：`grep -rn "RILL-0.1.0.md#" docs` 无输出；对规范的引用全部是章节号（如 `§4.17`、`§4.20`），无一处行号或文件内片段锚点。
  - 性质：说明不足（“本版冻结不改”成立，“不能拆”不成立）。
  - 影响：把可还的文档债写成不可还，长期掩盖 760 行的单文件结构。
- **A13 “7 份豁免”与门禁 10 条 WARN 的计数口径**
  - 位置：`docs/DOC-S2-waivers.md#L14`（7 份）、`README.md#L90-L91`（7 份）；门禁实跑打印 10 条 `WARN 豁免`。
  - 证据：多出的 3 条是 `docs/design/README.md`、`dsl-discussion.md`、`dsl-spec-v0.1.md`，由 `DOC-S2-waivers.md#L28` 声明为自动豁免。
  - 性质：说明不足。
  - 影响：数字对不上会被误读成“登记表漏了 3 份”。
- **A14 同一概念多套写法**
  - 位置：`docs/RILL-0.1.0.md#L284`（“尾随区块”）与 `#L295`（“尾随块”）；`#L219`（“独立形式语句”）与解析器消息（“独立介宾块”，`src/rill/parser.py#L254`）；`testdata/0.1.0/negative/parse/break-verb-value/case.json#L4` 仍写“字面量”。
  - 证据：原文对照如上；0.1.1 A2 已把 §4.15 的“字面量”改为 `value`。
  - 性质：说明不足。
  - 影响：术语检索与教学口径不统一；fixture note 与冻结正文不一致。
- **A15 一处交叉引用指向不存在的章节**
  - 位置：`testdata/0.1.0/positive/check/each-bareword-w01/case.json#L4`（“0.1.1 §0.1.1 / §4.20”）。
  - 证据：规范中的“0.1.1”是变更摘要标题，不是章节号；`W-01` 的实际定义在 `#L510`。
  - 性质：说明不足。
  - 影响：小；会让按 note 回查的人多绕一步。

---

## 轴二：测试覆盖度

**结论数字：核对 12 项——有锚点/一致 4 项、覆盖缺口 8 项。**

### 一致（4）

- **T-C1 桶与计数**：positive 56 / negative 26 / host 1 / smoke 2；negative 内 tokenize 9、parse 10、load 7，与 acceptance 表逐项相符。
- **T-C2 单测**：39 个测试文件全 rc=0。
- **T-C3 未执行项**：pending 0；4 个 retired 目录 harness 不发现；fixture 无 `xfail`/`skip`，不存在静默剔除。
- **T-C4 判据锚点**：`rill-0.1.0-completion-audit.md` 为 79 条判据逐条给了锚点；抽查 PH-10 E-1 的“12 例”（实为 shell 12 个 fixture）与 PH-11 E-1 的 agent fixture 数量均对得上。

### 覆盖缺口（8）

- **T1 4 种 AST 节点没有任何 golden**
  - 位置：`src/rill/ast.py#L13-L49` 的 31 种节点；`testdata/0.1.0/expected/ast/**` 只出现 26 种。
  - 证据：全量扫描 23 个 golden，缺 `Concat`、`Default`、`Pipe`、`Self`。其中 `Pipe` 由 `parser.py#L416` 产生（`if <read> a |> <parse> yaml {}` 实测 rc=0 且 AST 为 `Pipe`），`Default` 只出现在 run 用例，`Self` 只作为 run 的实参出现。
  - 性质：确有问题（缺负例之外的正例）。
  - 影响：节点词汇表与解析器之间没有整树断言兜底；A3 的拼接缺陷正是缺 `Concat` golden 的直接后果。
- **T2 16 个实现错误码在测试/夹具中 0 引用**
  - 位置：`src/` 全量码表与 `tests/`+`testdata/` 反查。
  - 证据：无引用的码：`E-HOST-FS-TYPE`、`E-HOST-PROCESS-SPAWN`、`E-HOST-PROCESS-TIMEOUT`、`E-HOST-VERB-ARGS`、`E-LEX-CHAR`、`E-LEX-GT`、`E-LEX-PIPE`、`E-LEX-VERB`、`E-LOAD-PROFILE-UNKNOWN`、`E-PARSE-FN-DEFAULT`、`E-PARSE-HEADER-ORDER`、`E-PARSE-UNEXPECTED`、`E-RUN-CONCAT`、`E-RUN-FAKES`、`E-RUN-FN-ARITY`、`E-RUN-FN-UNDECLARED`。其中 4 个可手动触发：`<> a.yml`→`E-LEX-VERB`、`> a.yml`→`E-LEX-GT`、`| x`→`E-LEX-PIPE`、语句后写 `//map`→`E-PARSE-HEADER-ORDER`（均 rc=2）。
  - 性质：确有问题。
  - 影响：这些分支只靠本评审临时探针证明可达，回归时无人守。
- **T3 两个运行期错误码被加载期永久遮蔽**
  - 位置：`src/rill/eval_fn.py#L29`（`E-RUN-FN-UNDECLARED`）、`#L39/#L53`（`E-RUN-FN-ARITY`）。
  - 证据：`run negative/load/fn-arity-too-few` → `{"stage":"load","code":"E-LOAD-FN-ARITY"}`；`cli.cmd_run` 先 `loader.check_program` 再 `Interpreter`，故运行期重复码不可达。两者都是 0 测试引用。
  - 性质：确有问题（死分支）。
  - 影响：错误码表虚胖，读者会以为运行期还会报另一套码。
- **T4 4 个产生式分支没有夹具**
  - 位置：`docs/RILL-0.1.0.md#L96-L123`。
  - 证据：无夹具的分支：引号主语（`"a b" <read> x`，实测 rc=0 但无 golden）、`condition := value`（只有 verb_call 条件）、`expr := pipe` 在 `if`/`each` 头（实测 rc=0，无夹具）、独立 `[ok]/[error]` 形式（无法做正例，运行时拒绝）。
  - 性质：确有问题。
  - 影响：§三 的“每个产生式至少一条用例”实际不成立。
- **T5 26 条负例里 23 条断言的码不在正文**
  - 位置：`testdata/0.1.0/negative/**/case.json`。
  - 证据：只有 `E-01`（2 条）与 `E-02`（1 条）来自规范 §4.20；其余 23 条断言 `E-LEX-*`/`E-PARSE-*`/`E-LOAD-*`。
  - 性质：说明不足（与 A8 同源，测试侧视角）。
  - 影响：正文读者无法从 §4.20 推出失败用例的期望码。
- **T6 7 条替代锚点中 2 条已明确不成立**
  - 位置：`docs/reviews/rill-0.1.0-completion-audit.md#L157-L170`。
  - 证据：`#L164` PH-5 E-3“三类长词 golden 未交付”：`ls testdata/0.1.0/expected/` 只有 `ast/run/tokens`，无 `fmt/`；`#L165` PH-5 E-5“Bytes/Opaque 未交付”：`src/` 有 `Bytes`，但测试与夹具中无一处针对格式化的断言。另 `#L161` PH-1 E-4 锚点已过期（parse 已实现）。
  - 性质：确有问题（完成度口径）。
  - 影响：对外说“12 个 phase 已完成”时，PH-5 有 2 条判据不成立；只有读完 completion-audit 才会发现。
  - **2026-11-15 更新**：`E-3`/`E-5` 已由用户裁定移出 0.1.0，转入 0.1.1 backlog
    `BL-001`/`BL-002`。原“未满足”结论保留为当时事实；对外口径改为“已裁定移出，
    不计通过，0.1.0 不是 12 卡全绿”。
- **T7 宿主能力矩阵只有 4/16 格有真实用例**
  - 位置：`testdata/0.1.0/host/shell/**`（12 例）与 `host/agent/**`（14 例）。
  - 证据：真实宿主夹具只覆盖 `simple_stmt`、管道、角色主语、尾随 `[error]`；没有任何 `if`/`each`/`parallel`/`[into]`/`[ok]`/`//map`/`//fn` 的真实宿主用例。动词侧：Shell 真实实现 5/10（`read/write/run/env/send`），Agent canonical 工具 4/10（`read/write/run/send`）。
  - 性质：确有问题（缺一侧与全无并存）。
  - 影响：控制流只在 fake 传输上验证过，“真实宿主 + 控制流”这一组合无证据。
- **T8 负例集中在少数分支，8 类错误从未被夹具覆盖**
  - 位置：`testdata/0.1.0/negative/`。
  - 证据：无负例的分支包括：空动词 `<>`、孤立 `>`、孤立 `|`、非法字符、`header` 出现在语句后、`each` 缺 `[in]`、`each` 头用非 `[in]` 介词、`//fn{}` 未闭合；另有 §4.9“独立 `[into]` 重名禁令”无任何用例。
  - 性质：确有问题（happy path 之外的语法分支未测）。
  - 影响：上述分支的报错位置与码一旦漂移，门禁不会响。

---

## 轴三：样例覆盖度

**结论数字：核对 9 项——一致 2 项、缺例子 7 项（另 1 项与 A1 重复，不重复计数）。**

### 一致（2）

- **S-C1 两个样例都能跑**：`run shell.rill` 与 `run agent.rill` 均 `rc=0`，payload 与 README 一致；无需构建（`PYTHONPATH=src` 直跑）。
- **S-C2 quickstart 的目录前提被说清并可复现**：从仓库根目录跑通；从 `/tmp` 跑 Shell 例 → `rc=1 E-HOST-FS-READ`，与 README §2“请从仓库根目录运行”一致。

### 缺例子（7）

- **S1 样例只有 2 个，且是同一演示点**
  - 位置：`examples/quickstart/{shell,agent}.rill`。
  - 证据：两文件都是“读一个配置 → `send` 出去”；Agent 版多角色主语与 `file:` 类型槽。
  - 性质：只是缺例子。
  - 影响：读者看不到语言的其余形态。
- **S2 规范 20 个小节里只有约 6 节有可运行样例**
  - 位置：`docs/RILL-0.1.0.md` §4.1–§4.20。
  - 证据：样例覆盖 §4.1（主语）、§4.2/§4.6（动词与管道）、§4.3（宾语）、§4.5 的 `[to]`、§4.8 的 `$`；无样例覆盖 §4.4 状语、§4.7 变量、§4.9 `[into]`、§4.10/§4.11 `[ok]/[error]`、§4.12 `if`、§4.13 `each`、§4.14 `parallel`、§4.15 `break`、§4.16 转义、§4.17 `//map`、§4.18 `//fn`、§4.19 空格、§4.20 错误码。
  - 性质：只是缺例子。
  - 影响：新用户只能靠 fixture 学语法，而 fixture 不是面向使用者的样例。
- **S3 没有任何失败分支样例**
  - 位置：`examples/quickstart/`。
  - 证据：两个脚本都没有 `[error]`、`break`、非 0 退出路径。
  - 性质：只是缺例子。
  - 影响：用户不知道失败长什么样，也不知道 Shell/Agent 退出码不同（A10）。
- **S4 没有任何多点组合样例**
  - 位置：同上。
  - 证据：没有 `parallel` + 尾随块 + 管道、`each` + `[into]` + `[ok]`、`//fn` + `[error]` 这类组合。
  - 性质：只是缺例子。
  - 影响：规范把“管道 + 尾随块”称为重心，但重心没有可运行样例。
- **S5 两个样例的重复度高**
  - 位置：`examples/quickstart/shell.rill` 与 `agent.rill`。
  - 证据：差异只有主语（无 vs `engineer`）和类型槽（无 vs `file:`）；可以合并成“同一脚本、两个 profile”。
  - 性质：只是缺例子（重复）。
  - 影响：维护两份几乎相同的样例，新增样例时容易只改一边。
- **S6 文档地图没有交代 `docs/guides/` 与 `docs/examples/` 是旧 v0.1**
  - 位置：`README.md#L96-L105`；`docs/guides/dsl-tutorial/README.md#L1-L4`；`docs/examples/README.md#L1-L4`。
  - 证据：两份目录自述都写“v0.1 rev.1 / unverified”，但 README 的文档地图完全没列它们。
  - 性质：只是缺例子（可读性缺口）。
  - 影响：从 README 进入的新人会先读到 `let`/`|?`/`# allow:` 的旧语法，与 0.1.1 冲突。
- **S7 quickstart 依赖仓库相对路径，只有一半被文档化**
  - 位置：`examples/quickstart/profiles/tools.json`（`["python3","../../testdata/0.1.0/host/agent/tools/tool_server.py"]`）；`README.md#L52-L54` 只解释 `workspace` 相对 cwd。
  - 证据：从仓库根可跑；换目录即使改 `workspace`，`tools.json` 的 `../../testdata/...` 仍会失效。
  - 性质：只是缺例子（说明不足）。
  - 影响：把 quickstart 复制到别处的人会在工具创建阶段失败，且错误不在文档覆盖范围内。

> S5 之外的“规范 §六 示例 1/5/9 不可运行”与 A1 是同一事实，不重复计数。

---

## 优先级清单

### 必须在 0.1.1 修（会误导使用者或掩盖缺陷）

1. **A1**：§六 示例 1/5/9 与 §三 冲突；同时补登记示例 5/9 的“动词缺宾语”根因。
2. **A2**：独立 `[ok]/[error]`——正文说合法、运行期报 `E-RUN-UNSUPPORTED`，二者必须择一。
3. **A3**：§4.16 的拼接示例不可解析；要么实现引号段在前，要么改正文示例。
4. **A5**：`E-01/E-02` 的“解析期/词法层”口径统一。
5. **A4**：`//map` 块内位置——正文允许、实现拒绝，至少改成正文可推导的说法。
6. **A8**：55 个错误码在正文无入口，至少补一张“诊断码索引”或明确“见 phase 卡”。
7. **A9**：`fmt` 不产生语法诊断，删掉“语法诊断 2”的表述或补实现。
8. **A6**：补 `closeout-4…10` 或改掉 7 张卡的悬空引用。
9. **A7**：给 `docs/review/v1.3-*` 加“已被 0.1.1 取代”的抬头，避免旧结论被当现状。
10. **A10/A11**：README 的 `run` 退出码限定宿主；`testdata/README.md` 删掉 P1 时代的“返回 3/删除 smoke”。
11. **T3**：删除或标注 `E-RUN-FN-ARITY` / `E-RUN-FN-UNDECLARED` 这两个不可达码。
12. **T6**：在对外口径里明确 PH-5 有 2 条判据未满足，不能只说“12 个 phase 已完成”。（2026-11-15 已执行：两项裁定移出并登记 backlog；0.1.0 仍不得称 12 卡全绿）

### 可以放后面（缺例子、覆盖补强，不改变现有结论）

- **T1**：补 `Concat`/`Default`/`Pipe`/`Self` 四类 AST golden（`Concat` 与 A3 同批修）。
- **T2/T8**：为 16 个无引用码与 8 类未测分支补负例；优先 4 个已证明可触发的词法/解析码。
- **T4**：补引号主语、`condition := value`、`expr := pipe` 三条正例。
- **T7**：补“真实宿主 + `if/each/parallel/[into]`”用例，至少各 1 条。
- **S1–S7**：补分章样例、失败分支样例、组合样例；合并 shell/agent 样例；在 README 文档地图标注 `docs/guides/` 与 `docs/examples/` 的旧版本属性。
