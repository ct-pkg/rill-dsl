# RILL 0.1.0 CT 重写路线图（PH-13…PH-21）

> 状态：规划稿（2026-11-15）。上游依据：`docs/design/rill-0.1.0-implementation-language-gap.md`。
> 本文件只排 CT 重写与双实现对拍，不改 `docs/RILL-0.1.0.md`，不改 Python 参考实现，
> 也不改 `docs/planning/rill-0.1.0-roadmap.md`（PH-1…PH-12）的既有结论。

## 0. 双实现定位（长期规矩，不是过渡安排）

| 实现 | 定位 | 目录 | 状态 | 去留 |
| --- | --- | --- | --- | --- |
| Python | **参考实现 / 对拍基准** | `src/rill/` | 0.12.0，12 个 phase 已收口 | **永久保留**，不随 CT 版淘汰 |
| CT | **正式实现** | `ct/` | PH-17 收口：token/parse/check/run 全链路，7 个多单元（`ct/src/**`，`ct build`） | 对外默认实现 |

- CT 的编译产物是**纯 C**（`ctc` 生成 C，再用 `cc -std=c99` 编译），运行时不依赖 CT 工具链。
- 两版共用同一份 `testdata/0.1.0/` fixture 与 golden；golden 是**第三方基准**，
  不得因为 CT 实现方便而修改，也不得因为 Python 已经通过就默认 CT 必须一致。
- Python 版不再新增语义能力；它的职责是 oracle、错误信息对照与回归基线。
- 本路线图**不取代** PH-1…PH-12：那 12 张卡记录 Python 参考实现的历史与判据；
  PH-13 起记录 CT 正式实现。产品版本从 `0.13.0` 续号（`version-minor = n`）。

## 1. 覆盖与不覆盖

**覆盖**：gap 评估的 P1…P9 九层，按“一层或半层一张卡”切分；每层有独立可跑的退出判据；
每阶段收口附 Python↔CT 差分报告。

**不覆盖**：

1. 规范正文变更。语义有歧义时先走 CR，不在实现里各自解释。
2. 下掉 Python 版。双实现是长期状态，不做“切换后删除”。
3. 真实工具、权限/审批/白名单、生产安全策略。
4. `ct-lang` 自身缺陷修复（PH-46、PH-51 等）。这些记在 `ct-lang` 账上；
   本路线图只登记绕法与代价。
5. 性能、并发调度、流式/PTY、Windows 宿主。
6. 旧 `v0.1 rev.1` 语法兼容。

**为什么这样切**：P1 只依赖字符串与树节点，35 个 golden（12 token + 23 AST）加 19 条负例
就能独立判绿；把 `Map` 与动态 `Value` 所有权推到 P3/P4，避免第一周就撞 CT 缺陷。
P6 可在 P2 后与 P3/P4 并行，P7/P8 在同一 `HostCapabilities` 上顺序推进，P9 汇合。

## 2. 阶段总览

| 阶段 | 层 | 目标一句话 | 依赖 | 可并行 | 退出锚点 |
| --- | --- | --- | --- | --- | --- |
| PH-13 | P1 | 接管在途 lexer，CT 构建可跑，12 token golden + 9 负例全绿 | 在途 `ct/rill_ct.ct` | 无（P2 依赖它） | token 对拍 0 差异；首次建立对拍目录 |
| PH-14 | P2 | parser/AST 收口，23 AST golden + 10 parse 负例全绿 | PH-13 | 与 PH-18 可后半程并行 | AST 对拍 0 差异（span 归一化后） |
| PH-15 | P3 | loader/诊断/W-01，`Map` 缺陷用指针表绕过 | PH-14 | 与 PH-18 | 7 负例 + W-01；error 层对拍 0 差异 |
| PH-16 | P4 | 值模型、`{value, ok}`、`$`、管道、固有动词 | PH-14、PH-15 | 与 PH-18 | 19 个 run fixture；eval 对拍 0 差异 |
| PH-17 | P5 | `if`/`each`/`break`/`parallel`/`[results]`/`//fn` | PH-16、PH-15 | 与 PH-18 | 剩余 run fixture 全绿 |
| PH-18 | P6 | 压缩↔展示与 round-trip | PH-14 | 与 PH-15/16/17 | 71 个 round-trip 全绿 |
| PH-19 | P7 | Shell 宿主五类能力，函数指针表避开 `S**` | PH-16、PH-17 | 与 PH-20 前半程 | 12 个 Shell fixture |
| PH-20 | P8 | Agent 宿主 + 最小 JSON，能力映射到同一接口 | PH-15、PH-16、PH-19 | 与 PH-19 后半程 | 14 个 Agent fixture |
| PH-21 | P9 | CLI 集成、全样例、双实现对拍总账 | PH-17、PH-18、PH-19、PH-20 | 无 | 85 fixture + 71 round-trip + 24 host；全层对拍 0 未解释差异 |

## 3. 依赖链与在途项

```
在途 ct/rill_ct.ct ── PH-13(P1) ── PH-14(P2) ──┬─ PH-15(P3) ── PH-16(P4) ── PH-17(P5) ──┬─ PH-19(P7) ── PH-20(P8) ── PH-21(P9)
                                                │                                  │
                                                └─ PH-18(P6) ───────────────────────┘
```

- **在途项不重复立项**：`ct/rill_ct.ct` 已覆盖 tokenize → parse → JSON 的 first layer，
  由另一会话所有。PH-13/PH-14 的角色是**接管验收**：补构建、补协议、补 golden、
  做对拍与收口；已交付部分只验收与补差，不重写。
- 硬边：PH-13 → PH-14；PH-14 → PH-15/PH-16/PH-18；PH-15 → PH-16；PH-16 → PH-17；
  PH-17 → PH-19；PH-19 → PH-20；PH-17/18/19/20 → PH-21。
- 软边：PH-18 只依赖 PH-14，可在 PH-15/16/17 进行时先做；PH-19/PH-20 共用
  `HostCapabilities`，接口先定，壳与工具适配可分头写。
- 每个 phase 的卡片在 `docs/phases/PH-<n>/card.md`，体例与 PH-1…PH-12 相同；
  `tools/check.sh g1` / `g8` 对它们同样生效。

## 4. 被 ct-lang 缺陷卡住的层（实测绕法 + 代价）

| 缺陷 | 卡住的 phase | 为什么命中 | 实测绕法 | 代价 |
| --- | --- | --- | --- | --- |
| PH-46：`Map<K, 用户 struct>` 条目按值进共享头（规划中，未实现） | **PH-15**、PH-16、PH-20 | 作用域表、`//map` 表、verb/profile/工具表都想用 `Map<Str, Value>`；`ct build` 会因元素类型不完整失败 | 存指针：`Map<char*, Value*>`（写真值语义用 retain/release）或 `Map<char*, void*>`；`ct-lang/docs/proposals/ct-json-capability-blockers.md` 实测 `Map<char*, JsonRef>` 失败、`Map<char*, Value*>` 与 `void*` 通过 | 每次查表多一次解引用；键与值都要显式分配/释放，约 +150–300 行与一轮生命周期审计；不能用值语义的 `Map` 糖 |
| PH-51：指针接收者 `.` 调用发射 `S_f(&p)`（传 `S**`，规划中，未修） | **PH-19**、PH-20（以及任何 trait 化 `Value` 方法） | 宿主能力接口若用指针接收者，vtable 调用点静默错值；链式 `.get().get()` 尤甚 | 宿主能力改用**函数指针表/自由函数**；`Value` 方法用**值接收者**或显式 `(*p)`；禁止链式 `.get().get()`；见 `ct-lang/docs/reviews/2026-11-15-deepseek-ct-proposal-review.md` 的实测记录 | 每个能力槽位手写函数指针与派发，约 +100–200 行；失去方法链语法，错误更早暴露但要人工审 |
| 无 JSON 库（J-1…J-4） | PH-20、PH-21 | Agent 宿主与 CLI 信封都要 JSON | 自写最小 JSON 编解码（约 500–800 行）；或让 `tool_server.py` 继续做外部进程，CT 只处理 CLI 边界 | 自写要覆盖字符串转义/UTF-8/数字；外部进程方案保持 100% fixture 复用，但多一层进程边界 |
| CT 内置 lexer 不能复用（换行是空白） | PH-13 | RILL 的换行/缩进有语义 | 手写 lexer（在途实现已是手写） | 无额外代价；规则表从 Python 版平移 |
| 无 GC / 所有权 | PH-16 | `Value` 生命周期与 `{value, ok}` | 一次运行一个 arena + 显式 retain/release | 长脚本内存不回收；RILL 单次执行生命周期短，可接受 |
| CT 头/实现拆分与 `.m.ct` import 状态待复核 | PH-13 起 | 40–48 个 `.h.ct`/`.m.ct` 的拆分前提 | P0 复核：以 `ct-lang` 当前 HEAD 复跑 A-1 与 SH-74/75；未过则先单文件 | 未过时保持单文件，后续拆分成本上升 |

## 5. 对拍机制（每阶段收口的固定一环）

**目录（PH-13 首次建立）**：

| 路径 | 内容 |
| --- | --- |
| `tools/diff/diff.py` | 对拍入口：同一 `.ri` 输入分别调 Python SUT 与 CT SUT，逐层比较 |
| `tools/diff/sut.ct.json` | CT SUT 命令/参数/构建产物路径（与 `testdata/0.1.0/sut.json` 并列，不改后者） |
| `docs/reviews/diff/PH-<n>.md` | 每个 phase 收口的差异报告 |
| `docs/reviews/diff/registry.md` | 已裁定差异登记（host-specific、规范歧义、golden 修订） |

**比较项（逐层取最小可比较面）**：

1. token 序列：`kind,text,line,col`，顺序敏感；
2. AST：忽略 `span` 后的节点/字段/顺序；
3. 错误：`stage`、`code`、`line`、`col`、退出码；
4. 求值：标准输出 JSON、`value/ok` 轨迹、退出码；
5. 宿主：同源 fixture 的 AST 相等；能力差异只允许出现在结果层并登记。

**报告最少字段**：phase、两侧版本/提交、比较层、用例数、差异数、
`first_seen_phase`、归属（Python 修 / CT 修 / 规范 CR / 登记豁免）、原始命令。

**收口硬约束**：`docs/reviews/diff/PH-<n>.md` 不存在或有未解释差异 → 不得收口；
差异不能只写“看起来一样”，必须贴命令与逐项输出。

## 6. 双轨门禁与防漂移

- `testdata/0.1.0/` 的 fixture 与 golden 是**第三方基准**。任何一方实现不通过，
  先判性质，不得直接改 golden 迁就实现。
- 判定顺序：
  1. 规范有明文 → 偏离方修（CT 或 Python），另一方保持；
  2. 规范无明文/有歧义 → 先提 CR 修规范，规范定稿后两边同步，再重定 golden；
  3. 规范允许的宿主差异 → 写入 `registry.md` 的 `host-specific`，不计为实现差异；
  4. golden 本身有错 → 需用户签字，修 golden 并在 `registry.md` 记录旧/新值与原因。
- 防漂移：规范每次变更，要么同一 phase 内两边同步并重跑对拍，要么以 golden 为准
  并在 `registry.md` 登记差异；禁止“只改 Python”或“只改 CT”后不记账。
- `tools/check.sh all` 仍守文档与卡片；CT 构建与对拍由 `tools/check-0.1.0.sh`（`--sut ct`）
  与 `tools/diff/diff.py` 守。golden 改动必须在提交正文写明 `golden-change: <registry 条目>`。

## 7. 每阶段固定流程

1. **实现**：按卡片 §3 逐任务提交；先 `test(...) 红`，再 `feat(...)` 实现（T-7）。
2. **复核**：跑本层 golden + 对拍；差异逐项归因到具体 phase。
3. **收口**：填 `docs/reviews/closeout-<n>.md`（体例同 2/3 号模板），
   附 `docs/reviews/diff/PH-<n>.md`；issues 三去向、`lessons` 每条落 `gate:`/`spec:`/`rejected:`。
4. **收口后**：只推本地提交；tag/分支/远端发布按 `docs/phases/README.md` §4 与用户指令，
   本路线图不自动打 tag。
5. 任一环节缺证据即停在当前 phase，不得进入下一层。

## 8. 资产复用与规模

- 可复用：85 fixture、46 golden、24 host fixture、71 round-trip 输入、3,123 行 harness
  （只需把 SUT 指向 CT）；39 个 Python 单测文件 0 个可原样复用，8 个黑盒型改 SUT。
- CT 生产代码估计 8,200–14,000 行；含 `.h.ct`/`.m.ct` 声明 10,000–19,000 行、约 40–48 个文件；
  测试另计 2,000–8,000 行。
- 单文件 `ct/rill_ct.ct`（2,030 行）是 PH-13/PH-14 的起点；PH-17 起改为
  `ct/src/**` 多单元（7 个单元，`ct build`），详见 `docs/phases/pending/ct-multiunit.md`。

## 9. 风险与开放项

| 风险 | 信号 | 处置 |
| --- | --- | --- |
| 在途实现与 golden 逐条不一致 | PH-13 对拍出现 token 差异 | 先在 PH-13 内补差；不改 golden |
| `Map` 绕法造成生命周期 bug | 表项释放后仍被引用 | arena 统一释放 + retain/release 断言 |
| 指针接收者缺陷误用 | 宿主返回非空结果却读到错值 | 只用函数指针表/值接收者；禁用链式 `.get().get()` |
| 双实现漂移 | 同一 fixture 两边长期不一致且无登记 | 每 phase 对拍；`registry.md` 无条目即不得收口 |
| 规范歧义被两边各自解释 | 对拍差异无法归因 | 先 CR；未定稿不进实现 |
| 在途会话与规划冲突 | `ct/` 出现未跟踪改动 | 只读引用；不修改、不提交 `ct/` |
