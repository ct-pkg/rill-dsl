# RILL 0.1.0 实现语言偏离评估：Python 参考实现 vs CT 目标实现

> 基线：`rill-dsl` @ `245292b`（产品 0.12.0 / 规范 0.1.1）；CT 侧只读参考快照：
> `ct-lang` @ `94556f29`。本文只读核对，不改实现、夹具与规范正文。
> 复跑命令：`find src -type f`、`git log --diff-filter=A`、`grep`、`bash tools/check-0.1.0.sh --all`、
> `bash tools/check.sh all`、`python3 -m rill parse --dump-ast`（探针均在 `/tmp`）。

## 0. 结论摘要

| 问题 | 结论 |
| --- | --- |
| 定性 | **偏离（未登记的选型替换）**，不是计划内的 bootstrap；但它产出的资产可复用，是否算“弯路”取决于是否补上 R-005 裁定与 CT 重写里程碑 |
| 为什么是 Python | 唯一书面理由是 `docs/planning/rill-0.1.0-lexer.md#L9`：先把语言定义与工具链不确定性解耦；该理由成立，但它从未被提升为决策，也未登记重写账 |
| 代码可搬/重设计/重写 | 按 4,461 行生产代码计：**19% 结构可平移 / 28% 必须重设计 / 52% 只能重写** |
| 资产复用 | 85 fixture、46 golden、24 host fixture、71 round-trip 输入、3,123 行 harness **可 100% 复用**（前提：CT CLI 保持同一 JSON/退出码协议）；39 个测试文件 0 个可原样复用 |
| 迁移分层 | P1 lexer → P2 parser/AST → P3 loader → P4 求值核心 → P5 控制流 → P6 formatter → P7 Shell 宿主 → P8 Agent 宿主 → P9 集成；**P1 是第一个可独立验收的层** |
| 生产代码规模 | CT 侧 **8,200–14,000 行**（不含测试；含 `.h.ct`/`.m.ct` 声明后约 **10,000–19,000 行**、约 **40–48 个文件**） |
| 最可能卡住 | **P3/P4（loader 表 + 动态 Value 所有权）**，直接撞 CT `Map` 条目按值进共享头的缺陷；第二卡点是 P7/P8 的指针接收者 `S**` |

---

## 1. 事实核对

### 1.1 `src/rill/` 是什么语言、多少行

`src/` 下 **22 个 `.py` 文件，4,461 行，全部 Python 3（仅标准库）**；没有任何 `setup.py`/`pyproject.toml`/构建系统。

| 层 | 文件（行数） | 小计 |
| --- | --- | --- |
| 前端 | `tokens.py` 71、`lexer.py` 420、`ast.py` 87、`parser.py` 638、`loader.py` 200、`errors.py` 74 | 1,490 |
| 求值 | `value.py` 110、`result.py` 78、`pipe.py` 122、`eval_simple.py` 393、`eval_control.py` 114、`eval_fn.py` 83、`eval_parallel.py` 80、`verbs.py` 52、`fakes.py` 31 | 1,063 |
| 格式化 | `formatter.py` 256 | 256 |
| 宿主 | `host/__init__.py` 33、`host/shell.py` 428、`host/agent.py` 809 | 1,270 |
| CLI/入口 | `cli.py` 373、`__init__.py` 3、`__main__.py` 6 | 382 |

### 1.2 全仓有没有 CT / C 侧实现

- `find . \( -name '*.ct' -o -name '*.h.ct' -o -name '*.m.ct' -o -name '*.c' -o -name '*.h' \)`：**0 个**。
- `git log --all -- '*.ct' '*.h.ct' '*.m.ct'`：**0 条提交**；仅 `main` 一个分支。
- `git log --all -- Makefile CMakeLists.txt build.sh`：**0 条提交**；仓库从未有过 CT 构建骨架、shim 或生成物。
- 唯一的“C/CT 侧”是同目录外的 `ct-lang` 仓库（语言与编译器本身），与本实现无代码往来。

### 1.3 文档对“实现语言”的原文

| 文档 | 原文（位置） | 口径 |
| --- | --- | --- |
| 需求 | “实现语言为 CT；但 CT 只作实现语言，不是 RILL 的运行时依赖”（`docs/requirements/README.md#L21`，R-005，状态 **pending**） | **要求 CT，未裁定** |
| 0.1.0 路线图 | “实现语言与仓库落点：**未定**；phase 1 记录选型”（`docs/planning/rill-0.1.0-roadmap.md#L30`） | 允许 phase 1 选，但必须记录 |
| 阶段计划 | 产出物应含 `rill-0.1.0-implementation-decisions.md`：实现语言、仓库落点、CLI 形态…（`docs/planning/rill-0.1.0-phase-plan.md#L15`）；`src/lexer`（语言按 phase 1 选型）（`#L51`） | 选型文档是硬产出物 |
| 实际选型 | “实现语言为 **Python 3（仅标准库）**。理由：仓库现有工具链全部是 Python 3…不引入第二套工具链”（`docs/planning/rill-0.1.0-lexer.md#L7-L9`） | **Python**；PH-1 声明它“替代计划中的 implementation-decisions”（`PH-1/card.md#L48`） |
| README | “RILL 0.1.x 的参考实现…带 lexer、parser、运行时…”（`README.md#L3`） | 只说“参考实现”，未说“先 Python 后 CT” |
| 规范正文 | `grep "CT|Python|实现语言" docs/RILL-0.1.0.md` → **无** | 规范不绑定实现语言 |
| 12 张卡 | 只有 `PH-2/card.md#L92` 把它写成“**偏差**：计划写 `src/lexer`，实际为 Python 包”；其余 11 张卡不复述语言 | 卡片把它当偏差，不当计划 |

补充：`docs/decisions/` 没有一条“实现语言”决策；D-004/D-015/D-020 只是默认读者熟悉 CT 术语（`grep "实现语言" docs/decisions` 只命中 D-015 的一般性表述）。**“后续用 CT 重写”这条账，全仓没有登记。**

### 1.4 验收判据绑定了什么

- fixture / golden 本身是语言中立的：`.rill` 源码 + JSON（85 个 fixture；46 个 golden = 23 AST + 12 token + 11 run）。
- 但执行面是 Python 绑定的：`testdata/0.1.0/sut.json#L3` 写死 `["python3","-m","rill"]`；harness 是 Python（`tools/check-0.1.0.sh#L15` 调 `python3 tools/rill_harness/cli.py`）；39 个测试文件全部 `import rill`/`sys.path.insert`，其中 8 个 `test_*.py` 通过 subprocess 调 CLI（另有 4 个 `support.py` 也用 subprocess）。
- 结论：**判据的语义与实现语言无关，判据的执行机制与 Python 强绑定**。换 CT 时不需要改 fixture/golden，只需换 SUT 命令与重写单测。

### 1.5 偏离从哪开始

- `2026-11-14 13:45` 之前只有旧 v0.1 文档与样例；0.1.1 全部规划材料在 `2026-11-15 00:40:00`（`d96806a`）一次性落库。
- **13 秒后**：`00:40:07` 立 12 张卡（`83f7409`）→ `00:40:13` 落 Python 词法器与 `tokenize` CLI（`86b7285`，6 个文件 597 行）。
- `PH-1/card.md#L3` 自述“**对照卡（事后补记）**…开卡、判据冻结与红证均未在开工前成立”；`#L88` 再次称“事后补记，非合规收口”；`#L96` 承认 `implementation-decisions.md` 未产出。
- 因此：不是“某一步本可分叉却没分”，而是**从来没有一个语言选型闸门**。卡、计划与代码同批落地，R-005 的 pending 从未被翻面。

---

## 2. 定性

**结论：这是偏离，不是计划内的 bootstrap。**

支持“偏离”的证据：

1. R-005 明确写 CT，状态 pending；按仓库自己的治理规则（R-009），pending 不得作为已接受前提使用，但实现直接选了 Python。
2. 没有 `implementation-decisions.md`；替代它的 `lexer.md` 只论证“Python 方便”，没有论证“先 Python、后 CT”的迁移承诺。
3. 没有 CT 分支、没有构建骨架、没有重写里程碑、没有重写账；12 张卡里只有 PH-2 把它称为“偏差”。
4. PH-1 是事后补记卡，自认“判据未在开工前冻结”；不存在“先选 CT、因工具链受阻而临时 Python”的时间窗。

支持“并非恶意替换、且资产可复用”的证据：

1. `README.md#L3` 称其为“参考实现”，不是最终产品。
2. `docs/planning/rill-0.1.0-host-contract.md#L73` 明确留了口子：“产品实现若换语言，按同一形状重写”。
3. fixture/golden/AST 形状/错误码/双宿主 profile 都是语言中立资产（§1.4）。
4. `docs/planning/rill-0.1.0-lexer.md#L9` 的动机（先把语言定义与工具链解耦）本身成立，是常见的 bootstrap 理由。

所以准确的定性是：**一次有书面理由、但未经裁定、未登记重写账的选型替换**。它可以被追认成 bootstrap，条件是补上两件事：R-005 正式裁定（CT 为目标实现）与 CT 重写里程碑；否则它就是目标替换，Python 会成为事实标准实现。

**对“这是不是一条要走完的弯路”的直接回答：**

- 已花掉的 Python 代码不是白费：它产出了规范、85 个 fixture、46 个 golden、24 个宿主夹具、71 个 round-trip 输入、55 个错误码契约与 30 种 AST 节点；这些正是 CT 重写最贵的部分（定义与判据），且**可 100% 复用**。
- 但“弯路”要成立，必须真的走完 CT 这一段。现状没有任何 CT 重写账，所以它**目前不是弯路，而是分叉**。

---

## 3. 差距：能搬 / 要重设计 / 只能重写

按 4,461 行生产代码归类（比例按行数）：

| 类别 | 内容 | 行数 | 占比 | 说明 |
| --- | --- | --- | --- | --- |
| **能直接搬** | `tokens.py`、`ast.py`、`errors.py`、`cli.py`、`formatter.py` | 861 | 19% | 结构可 1:1 平移：token 形状、AST 字段顺序、错误码表、CLI JSON/退出码、格式化规则；不是零成本，但不需要重新设计语义 |
| **必须重设计** | `loader.py`、`value.py`、`result.py`、`pipe.py`、`eval_*.py`、`verbs.py`、`fakes.py` | 1,263 | 28% | 语义不变，但容器、所有权、错误传播要按 CT 重做：`Map`→稳定键表、`Value`→带 retain/release 的 tagged union、`{value, ok}`→显式结果结构 |
| **只能重写** | `lexer.py`、`parser.py`、`host/*`、入口 9 行 | 2,337 | 52% | CT 自带 lexer 不能复用（换行是空白）；parser 是手写递归下降；宿主是 OS 进程/文件/stdio 适配，Python API 无对应物 |

资产侧（不属于上面 4,461 行，但决定迁移成本）：

| 资产 | 数量 | 迁移时 |
| --- | --- | --- |
| fixture | 85（56 正 / 26 负 / 1 host / 2 smoke） | 原样复用 |
| golden | 46（23 AST + 12 token + 11 run） | 原样复用 |
| host fixture | 24（Shell 12 + Agent 14） | 原样复用 |
| round-trip 输入 | 71 | 原样复用 |
| harness | 3,123 行 Python / 6 文件 | 原样复用（只换 SUT 命令） |
| 单测 | 39 个 `test_*.py` + 5 个 `support.py`，5,633 行 | **0 个可原样复用**；建议改成黑盒 subprocess，或随 CT 内部 API 重写 |
| 语法/语义规则 | 31 条 `:=` 产生式、27 种 token、30 种 AST 节点、10 个动词、55 个错误码 | 作为规格直接使用 |

---

## 4. 迁移方案

### 4.1 分层与验收锚点

| 层 | 内容 | 验收锚点（可复用） | 独立可验收 |
| --- | --- | --- | --- |
| P0 | CT 基础设施：`Str`/`Vec`/`Map` 包装、`Value`、JSON 编解码、进程/FS 封装 | CT 自己的单测；不设 RILL 门禁 | 否（被 P3/P4 消费） |
| **P1** | **lexer** | 12 个 token golden + 9 个 `negative/tokenize` | **是（第一个）** |
| P2 | parser + AST | 23 个 AST golden + 10 个 `negative/parse` | 是 |
| P3 | loader / 诊断 / W-01 | 7 个 `negative/load` + 1 个 warning + 错误码表 | 是（需 P0 的键表） |
| P4 | 求值核心：值、`{value, ok}`、管道、`$`、固有动词 | 19 个 `positive/run` + PH-6/PH-7 单测语义 | 是 |
| P5 | 控制流：`if`/`each`/`break`/`parallel`/`[results]`/`//fn` | PH-8/PH-9 单测语义 + 剩余 run fixture | 是 |
| P6 | formatter | 71 个 round-trip | 是（可在 P2 后先做） |
| P7 | Shell 宿主 | 12 个 shell fixture + e2e | 是 |
| P8 | Agent 宿主 | 14 个 agent fixture + 现有 `tool_server.py`（保持 Python 外部进程） | 是 |
| P9 | CLI/集成 | `check-0.1.0.sh --all` 85 个 + `check.sh all` | 最终 |

**为什么 P1 先**：token/AST 层不需要动态 `Value`、不需要 `Map`、不需要进程模型，只依赖字符串与树节点；35 个 golden（12 token + 23 AST）加 19 条负例足以独立判绿。这样可以把最危险的 `Map`/所有权问题推到 P3/P4，而不是第一周就撞上。

### 4.2 复用比例

- fixture/golden/host/round-trip：**226/226 个输入原样复用**（85 fixture + 46 golden + 24 host fixture + 71 round-trip 输入）。
- harness：**3,123/3,123 行复用**，只需把 `sut.json` 的 command 指向 CT 二进制。
- 单测：**0/39 个文件可原样复用**；8 个 subprocess 型 `test_*.py` 可改成黑盒，31 个内部 API 型需重写。
- 规范/卡片：**0 行改动**（`docs/RILL-0.1.0.md` 只读；卡片判据是命令，不绑语言）。

### 4.3 Python 版去留

建议保留为**冻结的对照实现**，直到 CT 版同时满足：

1. `check-0.1.0.sh --all` 85/85 与 `check.sh all` 全绿；
2. 71 个 round-trip 全绿；
3. 24 个 host fixture 全绿；
4. 对同一语料做差分流：两版 JSON 逐字节一致（除 `span` 归一化）。

之后把 Python 版移到 `reference/` 或打归档 tag，**不做双维护**。保留它的价值是差分 oracle 与错误信息对照；不保留它的价值是避免“事实标准在 Python”继续固化。

---

## 5. 代价

按可验证口径（行数/文件/规则/fixture），不给日历：

| 项 | 口径 | 区间 |
| --- | --- | --- |
| CT 生产代码 | 前端 1,490 + 求值 1,063 + 格式化 256 + CLI 382 = 3,191 行 Python，按 1.8–3.0× 估 | **5,700–9,600 行** |
| CT 宿主代码 | 1,270 行 Python，按 2.0–3.5× 估（syscall/字符串/进程） | **2,500–4,400 行** |
| CT 生产合计 | 上两项 | **8,200–14,000 行** |
| 含 `.h.ct`/`.m.ct` 声明 | +25–40% | **10,000–19,000 行** |
| 文件数 | 22 个 Python 模块按头/实现拆分 | **约 40–48 个 `.h.ct`/`.m.ct`** + 构建文件 |
| 需要落地的规则 | 31 产生式、27 token、30 AST 节点、10 动词、55 错误码 | 全部 1:1 落地 |
| 测试 | 8 个黑盒套件改 SUT；31 个内部套件重写 | **2,000–8,000 行**（取决于是否保留黑盒） |
| 可复用资产 | 157 个输入 + harness | **100%** |

说明：区间下界假设 CT 的 `Str`/`Vec`/`Map` 与 `errdefer`（Phase 40 已完成）能直接承载值模型，且 `Map` 缺陷用“存 `Value*`”绕过；上界假设需要自建 JSON、错误栈、字符串缓冲与宿主封装。**没有把“CT 编译器自身再修缺陷”的时间算进来**——那部分应记在 `ct-lang` 的账上。

---

## 6. 风险

### 6.1 输入事实与本地快照的冲突（先核，再动工）

- 本议题输入称“SH-74/75 已修”。但本机 `ct-lang` 快照 `94556f29` 的 `issues/README.md#L336` 仍标 **SH-74 open（P0）**；`SH-75` 在 `selfhost/ct-ast/backend/emit/Emitter.h.ct#L3707` 有修复注释。两者必须先以 `ct-lang` 当前 HEAD 复跑确认，否则 P7/P8 的接口返回会踩到 `&_self` 静默错值。
- 本议题输入称“A-1 后 `.m.ct` 可 import `.h.ct`”。本地 `selfhost/ct-ast/frontend/module/Module.h.ct#L557` 有 “SH-71 A-1” 实现注释，但 `issues/README.md#L1350` 仍写“A-1 延后”。这是**头/实现拆分的前提**，P0 第一件事就应复跑。
- 结论：这两条不是“已知可用”，而是**动工前的 P0 复核项**。

### 6.2 已知缺陷会卡在哪一层

| 缺陷 | 卡点 | 影响 | 绕法（有实测依据） |
| --- | --- | --- | --- |
| `Map` 条目按值进共享头（Phase 46 规划中） | **P3/P4** | 作用域表、`//map` 表、verb 表、profile 表都想要 `Map<Str, Value>`；`ct build` 下会因元素类型不完整而失败（`ct-lang/docs/proposals/ct-json-capability-blockers.md#L89-L109` 实测 `Map<char*, JsonRef>` 失败） | 存指针：`Map<char*, Value*>` / `Map<char*, void*>`；该文实测这两种在 `ct build` 下通过（`#L73-#L109`）。RILL 的 `Value` 本来就可以堆分配 + retain/release，改成存 `Value*` 不影响语义 |
| 指针接收者 `.` 调用发射 `S_f(&p)`（传 `struct S **`，Phase 51 规划中） | **P7/P8**（以及任何 trait 化 `Value` 方法） | 链式 `.get().get()` 与非空结果静默错值；宿主能力接口若用指针接收者，会在 vtable 调用点出错（`ct-lang/docs/reviews/2026-11-15-deepseek-ct-proposal-review.md#L19`、`#L117`、`#L134`） | 宿主能力用**函数指针表/自由函数**，不用指针接收者 trait；`Value` 方法用值接收者或显式 `(*p)`；禁止在 CT 侧写链式 `.get().get()` |
| 无 JSON 库（J-1..J-4） | **P8/P9** | Agent 宿主与 CLI 信封都要 JSON；CT std 没有 | 自写最小 JSON 编解码（约 500–800 行），或让 `tool_server.py` 继续做外部进程、CT 只处理 CLI 边界；不要把协议换成非 JSON（会破坏 100% fixture 复用） |
| CT lexer 不能复用（换行是空白） | P1 | 无 | 手写 RILL lexer；现有 Python 版就是手写的，规则表可平移 |
| 无 GC / 所有权 | P0/P4 | `Value` 生命周期 | 以“一次运行一个 arena + 显式 retain/release”实现；RILL 脚本生命周期短，arena 是合法简化 |

### 6.3 最可能卡住的一层

**P3/P4（loader 表 + 动态 `Value` 所有权）**。理由：

1. `Map` 缺陷正好命中 RILL 最核心的三张表（作用域、`//map`、verb/profile 表），而且它是 CT 侧**规划中未修**（Phase 46）。
2. 同一层还要自建 tagged union + `Str`/`Vec` 所有权；这是 Python 版最“免费”的部分（`value.py` 只有 110 行），在 CT 里会膨胀数倍。
3. P1/P2 有 35 个 golden 兜底，风险可见；P3/P4 只有 8 条负例 + 19 个 run fixture，且错误信息/所有权 bug 更隐蔽。

第二卡点是 **P7/P8 的指针接收者/接口返回**；但它有干净的绕法（函数表 + 值接收者），所以排第二。

---

## 7. 对用户质疑的直接回答

**“为什么变成了 Python？”**
唯一书面理由是 `docs/planning/rill-0.1.0-lexer.md#L9`：仓库现有工具链（harness、checks、stub）全是 Python，先用 Python 可以把语言定义跑起来，不引入第二套工具链。这个理由在工程上成立，但它只是“选型记录”，不是“授权偏离”，更没有写“以后用 CT 重写”。

**“这是不是一条要走完的弯路？”**
按现状：**不是弯路，是分叉**。R-005 仍是 pending，CT 侧 0 行、0 构建、0 重写里程碑；Python 版已经是事实标准实现。要把它变成“弯路”，只需要补两件事：正式裁定 CT 为目标实现（把 R-005 从 pending 翻面），以及按本文 §4 建立 P1–P9 里程碑并把 P1 的 35 个 golden 当作第一道 CT 门禁。

**“已经花掉的 Python 值不值？”**
值：它产出的是语言定义与 226 个可复用输入，不是一次性脚本。CT 重写最贵的是“知道要测什么”，这部分已经完成；剩下的是“用另一种语言再实现一遍”，规模见 §5。
