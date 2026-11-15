# RILL 0.1.0 已知限制（PH-12）

> 本清单只写“本轮明确不做/没做完”的边界，不冒充通过。缺口编号对应
> `docs/phases/PH-12/card.md` §7；验收结果见
> `docs/planning/rill-0.1.0-acceptance.md`。

## 1. 生产工具与权限

- Agent 侧 canonical 工具是真实子进程（`command` 工具 + `tools/tool_server.py`），
  但**未接**生产工具网关、审批、白名单与密钥注入；单测 fixture 仍可用
  `queue/default` 桩，桩只证明映射与取值，不证明真实副作用。
- 角色/权限只按 manifest 的 `roles` / `types` 表做加载期校验，不做真实
  授权与审计；动态主语（`$var` 角色）按默认角色处理（PH-11 卡 §7 #1）。
- Shell 侧是真实 OS 能力，但不验证生产安全策略；workspace root 约束只
  对 Agent 生效。
- `[error]` 仍只拿字符串；结构化工具错误走 `host_meta` / 工具值，不塞进 `$`。

## 2. 并发与调度

- `parallel` 是逻辑并行、顺序可观察，**未调度**真实并发、取消、进程池或
  限流；`[results]` 只按源序汇合。
- Agent 的 `limits` 只有 `steps` / `time_ms` / `bytes`；parallel 分支数与
  搜索深度尚未限流（PH-11 卡 §7 #3）。
- Shell 的进程 timeout 只覆盖单个进程，不是全局预算。
- Agent 的未处理失败不产生 OS 退出码（固定 0），调用方必须读 payload 的
  `ok`，不能用 `$?` 判断脚本成败。
- Shell 的 `--fakes` 已与真实宿主统一：未处理失败退出 1，harness 的 SUT
  接受“退出 1 + `{"ok": false}`”；Agent + `--fakes` 同样退出 1，因为 fakes
  是测试传输，不继承 agent 的固定 0 策略。

## 3. pending

- harness 的 pending=0：`pending: 0 not run (A 0, B 0)`；E-2 以此为准。
- `pending/` 下另有 4 个 `retired: true` 的转正痕迹目录，harness 不发现、
  不执行、不计入 pending：
  - `pending/bareword-value/break-bareword`
  - `pending/bareword-value/call-arg-bareword`
  - `pending/bareword-value/each-in-bareword`
  - `pending/map-verb-marker/value-and-verb`
- 不把 retired 目录从通过率里静默剔除，也不把它们改写成 pending。

## 4. 格式化器

- PH-5 **部分交付**：`src/rill/formatter.py` 是 PH-12 为 round-trip 门禁准备的
  最小实现（卡 §7 #1），只保证 `compress -> display -> compress` 的 AST
  等价，不保证展示风格与 golden。
- `round-trip` 覆盖 71 个可解析 fixture；tokens-only 用例不是合法 program，
  不纳入。
- PH-5 的 `expected/fmt` golden（三类长词）与二进制值（`Bytes` / `Opaque`）
  的格式规则**已于 2026-11-15 裁定移出 0.1.0**，转入 0.1.1 backlog
  `BL-001`/`BL-002`；不计为 0.1.0 通过。内层覆盖外层的完整反向映射仍未实现。
- 展示态展开值类长词时一律加引号；与相邻词元拼接时整体引成一个 `STRING`
  （卡 §7 #8）。压缩态再按长词前缀拆回短词引用。
- `fmt` 退出码：成功 0、词法/语法诊断 2、参数错误 2（stage=cli）；没有 3。

## 5. 文档门禁基线

`bash tools/check.sh all` 当前 **0 FAIL**，`== overall: PASS ==`：

| 类别 | 数量 | 处理 |
| --- | --- | --- |
| DOC-S2（单份 >300 行） | 0 FAIL / 7 份显式豁免 | 拆分 `phase-plan` 与 `phase12-red`；冻结正文/生成副本/历史档案按 [DOC-S2 豁免登记表](../DOC-S2-waivers.md) 逐份 `WARN`，写明理由 |
| 断链 | 0 | 恢复 `docs/design/dsl-spec-v0.1.md`（历史原文，docs/design 豁免），9 条引用重新可解析 |
| 未定义版本 | 0 | `version_wording.py` 允许 `v0.1` / `v0.12.0` / `v1.7.0` / `v1.9.0`；跳过 sha256 锁定的主规范副本 |

- 7 份豁免不是“通过”：门禁逐份打印 `WARN 豁免 <路径>：<理由>`，登记表在
  [DOC-S2 豁免登记表](../DOC-S2-waivers.md)，新增文档不得走豁免。
- `docs/planning/*.md` 均 ≤300 行；`phase12-red.md` 已拆为 166 行 + 证据附录 273 行。
- 若基线数量变化，先判断是否本阶段新增；PH-11 的 `phase11-red.md` 仍 ≤300 行。
- `bash tools/check.sh g1` 通过；`g8-phase-freeze` 在 T1 实现提交后按首个
  实现提交的父提交比对，复核卡之后不再改 §3 / §4。

## 6. 其他边界

- `E-RUN-HOST-UNAVAILABLE` 已退役：Agent 永远有宿主（manifest 或 builtin），
  缺/坏 manifest 报 `E-RUN-HOST-PROFILE`（退出 2）。
- 独立 `[ok] $x {}` / `[error] $x {}` 本版仍不支持；把块挂到产生 `$` 的语句后
  用尾随块，报错消息会提示这条绕法（PH-11 卡 §7 #13）。
- 不实现旧 `v0.1 rev.1` 兼容；`docs/examples/` 不作为 0.1.1 验收输入。
- 不新增语法、不改 `docs/RILL-0.1.0.md` 正文；任何规范改动必须先走 CR。
- CLI 只实现本地进程协议（0/2，3 保留给未实现）；不提供远端发布、权限
  管理或并发调度入口。
- 双宿主的差异只允许出现在能力层；六项 host-specific 差异均不影响语法/AST，
  明细见 `docs/planning/rill-0.1.0-host-matrix.md` §9.2。

## 7. 门禁缺陷（PH-22 收口记录）

### GD-001：单条 fixture schema 错误会中止整个门禁

| 项 | 内容 |
| --- | --- |
| 现象 | 一个 `case.json` 写错，`tools/check-0.1.0.sh --all` 打印 `fixtures 不合法，未执行任何用例。`，合法用例一条也不跑 |
| 触发实例 | PH-22 新增的 `positive/run/call/fn-bind-repeat`、`fn-optional-prep` 把 `phase` 写成 `p22`（不在 `cases.py#PHASES` 白名单），两条坏数据让 90 个 fixture 全部停摆 |
| 根因 | `tools/rill_harness/cli.py` 先把 `discover()` 的 schema 错误汇总，再在 `if errors:` 分支直接 `return EXIT_FAIL`（L420–L425），运行阶段根本不会进入 |
| 为什么算缺陷 | 单条数据错误抹掉了其余用例的信号：门禁从“报告 N 条失败”退化为“0 条执行”，无法区分“夹具写坏”与“实现回归”；且 `--all` 的 `pending=0` 等汇总也只在此后才有 |
| 现状 | PH-22 只修数据（`p22` → `r1`），未改共享门禁；本相不动门禁行为，避免与 0.1.0 判据混在一起 |
| 建议修法 | schema 错误定位到单个 case 记 `FAIL`，其余 case 继续执行，最终整体非 0；`--all` 仍要求 `pending=0` 且非法 case 数 = 0 |
| 归属 | 0.1.1 门禁修复，另开 issue / phase；不占 PH-22 的 PATCH |
