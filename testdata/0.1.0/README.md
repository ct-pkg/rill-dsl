# RILL 0.1.0 测试数据与用例约定

状态：Phase 0 基座。规范正文是 `docs/RILL-0.1.0.md`（0.1.1 定稿）；本目录只存验收输入，不改规范。

`docs/examples/` 面向旧 `v0.1 rev.1`（`let` / `fn` / `|?` / `# allow:`），**不是** 0.1.0 的
验收输入，也不得拿来当 golden。需要借用场景时，先按 0.1.0 语法重写并落到本目录。

## 1. 目录结构

```text
testdata/0.1.0/
├── README.md                 本文件：约定与加用例步骤
├── sut.json                  被测命令清单（当前指向 `python3 -m rill`，P1）
├── positive/                 合法输入
├── negative/                 必须报错的输入，按报错阶段分子目录
│   ├── tokenize/
│   ├── parse/
│   └── load/
├── pending/                  保留为空（A2/B1 已转正；退役痕迹用 retired 标记）
├── host/                     双宿主 fixture（同源、AST 必须相等）
│   └── shared/
├── smoke/                    占位链路自证（stub-only，parse 落地后删除）
├── expected/                 golden 与格式说明
│   ├── ast/
│   └── tokens/
├── profiles/                 HostProfile 形状骨架（shell / agent）
└── fakes/                    fake 工具与外部能力桩
```

## 2. 一个用例包含什么

一个用例 = 一个目录，目录内**恰好两个必需文件**：

| 文件 | 作用 |
| --- | --- |
| `source.rill` | 输入脚本，UTF-8 + LF，按字节原样使用（压缩态与展示态都允许） |
| `case.json` | 期望声明：kind、phase、expect；详见 §4 |

用例 id = 目录相对 `testdata/0.1.0/` 的路径，例如
`positive/simple/read-write`。桶（`positive` / `negative` / `pending` / `host` / `smoke`）
决定统计口径，`kind` 决定怎么执行与比对。

**命名规则**：桶以下的每一级目录名必须匹配 `^[a-z0-9][a-z0-9-]*$`（小写 kebab），
同一桶内不得重名。`_` 开头的目录会被 harness 忽略，可用于本地草稿，不提交。

**桶与 kind 的对应**（由 `tools/rill_harness/cases.py` 强制）：

| 桶 | 允许的 kind | 用途 |
| --- | --- | --- |
| `positive/` | `ast` / `tokens` / `warning` / `run` | 合法输入，应通过（含不阻断的警告） |
| `negative/` | `error` | 必须报错，断言阶段与位置 |
| `pending/` | `pending` | 0.1.1 起应为空；保留格式供未来 CR 登记 |
| `host/` | `host-ast-equal` / `run` | 双宿主同源 fixture |
| `smoke/` | `ast` / `host-ast-equal`，且 `stub_only: true` | 占位链路自证 |

`pending/` 下的 `case.json` 若写 `{"retired": true, "superseded_by": "..."}`，harness 会
跳过该目录（不发现、不统计、不执行），用于保留“已转正”的痕迹；确认不再需要时可删除目录。

## 3. 期望产物怎么表达（决定与理由）

| 观察对象 | 表达方式 | 理由 |
| --- | --- | --- |
| AST | 归一化 JSON 快照（`expected/ast/<id>.json`） | 规范 §4.17 的等价判据就是“忽略 span 后节点类型与 value 逐一相等”，整树快照与判据同构；审阅时能看到节点的增删改，不用逐条猜断言覆盖 |
| token | JSON 快照（`expected/tokens/<id>.json`） | 位置信息是 P1 的错误定位契约，快照能同时盯住边界与行列 |
| 解析/加载错误 | 结构化断言（stage / code / line / col / message_contains） | 错误文案允许改进，阶段、错误码与位置才是契约；整段文案快照会把措辞修订误报成回归 |
| 警告（如 `W-01`） | 结构化断言（`check` 退出 0 + `warnings[]` 中匹配 code / message） | 警告明确不阻断 `check`，放进错误桶会要求实现把警告变成失败，违背 0.1.1 |
| 运行结果 | 结构化子集断言（ok / value / error / host_meta） | 求值轨迹会随实现成熟而增删，只断言可观察结果，避免把内部轨迹焊死 |
| 双 profile | 两次 `parse` 的 AST 相等断言 | 双宿主硬约束只要求“同一 AST”，不要求两次运行结果等价 |

**归一化规则**：AST 比较前递归删除 `span` 键；token 不删。比较解析后的结构，不比较文本
（键顺序、缩进不影响）。golden 信封与生成步骤见 `expected/README.md`。

**为什么不用“AST 只写几条路径断言”**：0.1.0 §三 有 7 类语句、4 类尾随块和 3 种 `]` 归约，
片段断言很容易漏掉兄弟节点；整树快照配合 `first_diff` 能直接指出第一处偏差。代价是修改
节点结构时要重生成 golden，这个代价由 P2 冻结节点词汇表时一次性承担。

## 4. `case.json` 字段

公共字段：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `kind` | 是 | `ast` / `tokens` / `error` / `warning` / `run` / `host-ast-equal` / `pending` |
| `phase` | 是 | 首次必须通过的阶段：`p0`–`p4` / `r1`–`r4` / `h1` / `h2` / `i1` |
| `expect` | 是 | kind 相关，见下 |
| `note` | 否 | 一句话说明该用例守规范哪一条或哪条评审 |
| `stub_only` | 否 | 只允许 `smoke/` 桶为 `true` |
| `sut_env` | 否 | 传给被测命令的环境变量覆盖，如 `{"RILL_STUB_MODE": "echo"}` |
| `sut` | 否 | 只允许 `smoke/` 用例覆盖被测命令，如 `["python3", "tools/rill_stub/rill.py"]` |
| `fakes` | 否 | 运行用例使用的 fake 清单，默认 `fakes/tools.json` |

各 kind 的 `expect`：

```jsonc
// ast：profiles 缺省 ["shell"]；不写 ast 时读 expected/ast/<id>.json
{"kind": "ast", "phase": "p2", "expect": {"profiles": ["shell"]}}

// tokens：不写 tokens 时读 expected/tokens/<id>.json
{"kind": "tokens", "phase": "p1", "expect": {}}

// error：stage ∈ tokenize|parse|load|any；command ∈ tokenize|parse|check
{"kind": "error", "phase": "p2",
 "expect": {"stage": "parse", "command": "parse", "code": "E_...", "line": 1, "col": 5}}

// warning：check 必须退出 0，且 warnings[] 中出现指定警告码（如 W-01）
{"kind": "warning", "phase": "p3",
 "expect": {"command": "check", "code": "W-01", "message_contains": "按字符串处理"}}

// run：ok 必填；value/error/host_meta 按需断言（host_meta 是子集匹配）
{"kind": "run", "phase": "r2",
 "expect": {"profile": "shell", "ok": true, "value": null}}

// host-ast-equal：至少两个 profile
{"kind": "host-ast-equal", "phase": "p2", "expect": {"profiles": ["shell", "agent"]}}

// pending：A2/B1 已结案，目录应保持为空；格式仅为未来 CR 保留
{"kind": "pending", "phase": "p2",
 "expect": {"blocked_by": "A", "reason": "某项未裁定", "unblocks_to": "ast"}}
```

`code` / `line` / `col` 是**可选**断言：Phase 0 只冻结阶段，不让实现为了过门禁提前发明
错误码表；P1/P2 冻结错误码后再逐条补上。

## 5. 统计口径

| 状态 | 含义 | 计入通过率 |
| --- | --- | --- |
| `PASS` | 期望满足 | 是 |
| `FAIL` | 期望不满足，或被测命令违反适配协议 | 是（失败） |
| `BLOCK` | 被测命令明确返回未实现（退出码 3） | 否，单列 |
| `DRAFT` | ast/tokens 用例已声明，但 golden 尚未产出 | 否，单列 |
| `PENDING` | 已登记的不确定项，默认不执行；0.1.1 起应为 0 | **否，单独统计** |

`compliance` = `positive` + `negative` + `host`；`smoke` 是占位链路自证，单独报告；
`pending` 永远不进通过率，I1 报告必须同时给出通过数与 pending 数。

门禁退出码：

- `0`：compliance 与 smoke 全部 PASS；
- `1`：有 FAIL，或用例/资产声明不合法；
- `3`：有 BLOCK 或 DRAFT（实现或 golden 还没到位）。

## 6. 被测命令适配契约（测试设施）

默认被测命令由 `sut.json` 指定，当前是 `python3 -m rill`（`PYTHONPATH=src`）。
P1 现状：`tokenize` 已实现；`parse` / `check` / `run` / `fmt` 仍返回退出码 3。
harness 只认“命令 + 退出码 + stdout JSON”；产品 CLI 的最终形态仍可能调整，
若与下列形状不同，只改 `tools/rill_harness/sut.py`，不动用例。

```text
<SUT> tokenize <source>                          -> 0  {"tokens": [...]}
<SUT> parse --dump-ast <source> --profile <p>    -> 0  {"ast": {...}}
<SUT> check <source> --profile <p>               -> 0  {"warnings": [...]}；错误 -> 2
<SUT> run <source> --profile <p> --fakes <path>  -> 0  {"ok": bool, "value": ..., "host_meta": {...}}
<SUT> fmt --compress|--display <source>          -> 0（P4 启用）
```

诊断（退出码 2）：

```json
{"error": {"stage": "parse", "code": "E_...", "line": 1, "col": 5, "message": "..."}}
```

警告（退出码 0，与正常结果同在一个对象里）：

```json
{"warnings": [{"code": "W-01", "line": 1, "col": 14, "message": "裸词按字符串处理，若意图是变量请写 $xs"}]}
```

退出码 3 = 未实现，harness 记为 `BLOCK`，不会静默当作通过。被测命令清单在 `sut.json`；
`--sut` 可临时覆盖。

## 7. 真实实现与占位层

- 默认被测命令已是真实 P1 CLI：`python3 -m rill`（见 `sut.json`），不是占位实现。
- `tools/rill_stub/rill.py` 只在 `smoke/` 桶里显式启用（用例用 `sut` 覆盖命令）：
  默认所有子命令返回退出码 3；`RILL_STUB_MODE=echo` 时 `parse --dump-ast` 回显 `StubProgram`。
- `smoke/` 桶只验证 harness 的调用、比对与双 profile 一致性，**不代表任何 0.1.0 语义**；
  真实 `parse` 落地后删除 `smoke/` 桶、占位文件与本节。

## 8. 怎么加用例（照着做）

1. **选桶与 id**：合法输入放 `positive/`，必须报错放 `negative/<阶段>/`，不阻断的警告也放
   `positive/`（`kind: warning`），双宿主同源放 `host/shared/`。目录名用小写 kebab。
2. **写 `source.rill`**：只写 0.1.0 正文允许的语法；不要从 `docs/examples/` 复制旧语法。
   压缩态与展示态都可以，但字节必须是你想测的那一版。
3. **写 `case.json`**：按 §4 选 kind；`note` 写清守的是规范哪一节或哪条评审。
4. **ast / tokens 补 golden**：
   - 先跑 `tools/check-0.1.0.sh --show <id>`，看被测命令的真实输出；
   - 把输出里的 `ast` / `tokens` 原样放进 `expected/{ast,tokens}/<id>.json` 的信封；
   - 逐节点对照规范人工核对，确认后不要再手改。
5. **负例**：在 `expect` 里写 `stage` 与 `command`；错误码已冻结的（如 `E-01` / `E-02`）补
   `code` / `line` / `col`。
6. **警告**：用 `kind: warning`，断言 `check` 退出 0 且 `warnings[]` 含指定码；不要把警告
   写进 `negative/`，否则等于要求实现把警告变成失败。
7. **pending**：A2 / B1 已结案，`pending/` 必须保持 0。未来出现新的不确定项时先开 CR，
   再按 `blocked_by` 登记；不要用 pending 逃掉已经能判定的用例。
8. **本地验证**：
   ```bash
   bash tools/check-0.1.0.sh --list                    # 结构、命名、资产
   bash tools/check-0.1.0.sh --show <id>               # 看实际输出
   bash tools/check-0.1.0.sh --kind ast --phase p2     # 只跑相关一组
   bash tools/check-0.1.0.sh                           # 全量
   ```
   （入口若已具备可执行位，可直接省略 `bash`；仓库当前的文件系统策略不允许改 mode。）
9. **自查清单**：用例有且只有两个必需文件；`case.json` 没有未知字段；没有把未裁定项
   硬写成期望；没有为了变绿改 golden；样例进了真实门禁而不是只留在 `/tmp`。

## 9. 维护边界

- 改用例约定：本文件 + `tools/rill_harness/cases.py` 的校验必须同一次改完，否则下一个人
  会按文档写出 `--list` 直接拒绝的用例。
- 改被测命令形状：只改 `sut.py` 与 `sut.json`。
- 改宿主形状：`profiles/` 与 `docs/planning/rill-0.1.0-host-contract.md` 同步；能力语义不在
  Phase 0 定义。
- 0.1.1 正文冻结：实现中发现歧义先开 CR，不在用例或 harness 里私自解释。
