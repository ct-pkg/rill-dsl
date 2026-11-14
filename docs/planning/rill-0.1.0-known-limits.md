# RILL 0.1.0 已知限制（PH-12）

> 本清单只写“本轮明确不做/没做完”的边界，不冒充通过。缺口编号对应
> `docs/phases/PH-12/card.md` §7；验收结果见
> `docs/planning/rill-0.1.0-acceptance.md`。

## 1. 生产工具与权限

- Agent 侧的工具来自工具注册表与 fake fixture，**未接**生产工具、审批、
  白名单与密钥注入。
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

- PH-5 未交付：`src/rill/formatter.py` 是 PH-12 为 round-trip 门禁准备的
  最小实现（卡 §7 #1），只保证 `compress -> display -> compress` 的 AST
  等价，不保证展示风格与 golden。
- `round-trip` 覆盖 71 个可解析 fixture；tokens-only 用例不是合法 program，
  不纳入。
- 未实现 PH-5 的 `expected/fmt` golden、内层覆盖外层的完整反向映射、二进制
  值（`Bytes` / `Opaque`）的格式规则。
- 展示态展开值类长词时一律加引号；与相邻词元拼接时整体引成一个 `STRING`
  （卡 §7 #8）。压缩态再按长词前缀拆回短词引用。
- `fmt` 退出码：成功 0、词法/语法诊断 2、参数错误 2（stage=cli）；没有 3。

## 5. 文档门禁基线

`bash tools/check.sh all` 当前有 20 个 FAIL，全部是 PH-12 之前就存在的
文档门禁基线，不是本阶段新增：

| 类别 | 数量 | 例子 |
| --- | --- | --- |
| DOC-S2（单份 >300 行） | 8 | `docs/RILL-0.1.0.md`、`docs/spec/ai-coding-workflow.md` |
| 断链 | 9 | `docs/design/dsl-spec-v0.1.md` 已不存在 |
| 未定义版本 | 3 | 规范副本中的 `v0.20.0` / `v0.30.1` / `v0.33.0` |

- 本阶段新增的 `docs/planning/*.md` 与 `docs/reviews/phase12-red.md` 均 ≤300 行，
  且不使用相对链接；若基线数量变化，先判断是否本阶段新增。
- `bash tools/check.sh g1` 通过；`g8-phase-freeze` 在 T1 实现提交后按首个
  实现提交的父提交比对，复核卡之后不再改 §3 / §4。

## 6. 其他边界

- 不实现旧 `v0.1 rev.1` 兼容；`docs/examples/` 不作为 0.1.1 验收输入。
- 不新增语法、不改 `docs/RILL-0.1.0.md` 正文；任何规范改动必须先走 CR。
- CLI 只实现本地进程协议（0/2，3 保留给未实现）；不提供远端发布、权限
  管理或并发调度入口。
- 双宿主的差异只允许出现在能力层；六项 host-specific 差异均不影响语法/AST，
  明细见 `docs/planning/rill-0.1.0-host-matrix.md` §9.2。
