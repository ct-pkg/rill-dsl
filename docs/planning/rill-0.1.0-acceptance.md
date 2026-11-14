# RILL 0.1.0 验收报告（PH-12）

> 输入：`testdata/0.1.0/`；被测命令：`python3 -m rill`；语言规范：
> `docs/RILL-0.1.0.md`（0.1.1，只读）。本报告只记录本轮可复跑的结果，
> 不改规范正文；缺口与裁定见 `docs/phases/PH-12/card.md` §7。

## 0. 口径

- 四类清单固定为：通过、失败、pending、host-specific。
- 通过率只由 `positive` / `negative` / `host` 三个桶计算；`smoke` 单独报告；
  `pending` 永远不进通过率。
- 正例端到端运行；负例只跑 `tokenize` / `parse` / `check`，不执行。
- 同一 fixture 在 shell / agent 两个 profile 的 AST 逐节点相等；运行结果只在
  能力可等价时比较，不等价处进 host-specific 清单。
- 本轮 fixture 总数 85；`--all` 退出 0 是 E-5 的唯一判据。

## 1. 通过（85）

| 桶 | 用例数 | 通过 | 说明 |
| --- | --- | --- | --- |
| positive | 56 | 56 | ast 23、tokens 12、run 19、check 1、warning 1 |
| negative | 26 | 26 | tokenize 9、parse 10、load 7，全部按预期错误码失败 |
| host | 1 | 1 | `host/shared/read-send`，shell/agent AST 相等 |
| smoke | 2 | 2 | 占位链路自证，单独报告 |
| 合计 | 85 | 85 | compliance 83 + smoke 2 |

- 全部正例通过；`negative/*` 全部按声明的 stage / code / line / col 失败，
  没有“失败但错误码不对”的用例。
- `smoke/echo-ast` 与 `smoke/dual-profile` 仍走 `tools/rill_stub`，只证明
  harness 链路，不计入合规通过率。

## 2. 失败（0）

| 项 | 数量 | 证据 |
| --- | --- | --- |
| harness FAIL | 0 | `summary.compliance.FAIL = 0`、`summary.smoke.FAIL = 0` |
| harness BLOCK | 0 | 没有退出码 3 的被测调用 |
| harness DRAFT | 0 | 35 个 ast/tokens golden 全部存在 |
| 负例错误码不符 | 0 | 26 个 negative 全部 PASS |

本轮没有验收失败项。`tools/check.sh all` 的既有失败属于文档门禁基线，
不是本报告的用例失败，单列在 `rill-0.1.0-known-limits.md`。

## 3. pending（0）

| 项 | 数量 | 说明 |
| --- | --- | --- |
| harness pending | 0 | `pending: 0 not run (A 0, B 0)` |
| retired 痕迹目录 | 4 | `retired: true`，harness 不发现、不执行 |

4 个 retired 目录只保留 A2/B1 的转正痕迹，不冒充 pending：

- `pending/bareword-value/break-bareword`
- `pending/bareword-value/call-arg-bareword`
- `pending/bareword-value/each-in-bareword`
- `pending/map-verb-marker/value-and-verb`

E-2 以 harness 的 pending 计数 0 为准；数量同时写在 `--all` 的
`gate: all buckets; pending=0, retired=4` 行。

## 4. host-specific（6）

| # | 差异 | Shell | Agent | 影响 |
| --- | --- | --- | --- | --- |
| 1 | `run` / `exec` | 真实进程 | 工具调用 | 不影响语法/AST |
| 2 | `read` / `write` | OS 文件 | 工具读写 | 不影响语法/AST |
| 3 | `env` | `os.environ` | manifest `context` | 不影响语法/AST |
| 4 | `send` | stderr | `send` / `emit` 工具 | 不影响语法/AST |
| 5 | 未处理失败退出码 | 非 0 | 0（payload `ok=false`） | 不影响语法/AST |
| 6 | 角色/类型/limits | 只有进程 timeout | `roles` / `types` / `limits` | 不影响语法/AST |

六项差异全部落在能力层，没有一条写进语法或 AST。完整形态见
`docs/planning/rill-0.1.0-host-matrix.md` §9。

## 5. 复现

```console
$ bash tools/check-0.1.0.sh --all
gate     : all buckets; pending=0, retired=4, problems=无
fixtures : 85 (positive 56, negative 26, host 1, smoke 2)
...
compliance: 83 passed, 0 failed, 0 blocked, 0 draft
smoke:     2 passed, 0 failed, 0 blocked, 0 draft
pending:   0 not run (A 0, B 0)
VERDICT: PASS (exit 0)
```

```console
$ bash tools/check-fmt.sh --roundtrip
PASS phase12 roundtrip: compress→display→compress AST 等价（71 个 fixture）

$ python3 tests/phase11/test_agent_fixtures.py
PASS phase11 fixtures: agent 五类能力 + role/limits/type + AST 一致
```

## 6. 退出判据对照

| ID | 条件 | 本轮结果 |
| --- | --- | --- |
| E-1 | 全部正例通过；负例按预期错误码失败 | 56 正例 + 26 负例全过 |
| E-2 | pending 数量为 0 | `pending: 0 not run`；4 个 retired 痕迹不计 |
| E-3 | round-trip 全绿 | 71 个 fixture，`--roundtrip` 退出 0 |
| E-4 | 同源 AST 相等，host-specific 差异有记录 | `host/shared/read-send` PASS；差异 6 条入表 |
| E-5 | `--all` 退出 0 | 85 例 PASS，exit 0 |
| E-6 | 不修改 0.1.1 正文 | 本轮无 `docs/RILL-0.1.0.md` 改动 |
| E-7 | 任务清单每项可独立验收 | 逐项 `verify` 见 `docs/reviews/phase12-red.md` |
