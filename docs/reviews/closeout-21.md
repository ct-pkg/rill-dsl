# PH-21 收口：CT 集成与双实现对拍总账（P9）

> 阶段判定：**GO（工程面）/ 0.1.0 判据 NO-GO（`Opaque` 不可验收）**。
> 全层 0 差异；85 用例 CT 侧全过、pending=0。

## 1. 退出判据（E）

| ID | 条件 | 结果 | 证据 |
| --- | --- | --- | --- |
| E-1 | 85 用例全过；pending=0 或显式 xfail | **过** | §3.1：`compliance 83 passed` + `smoke 2 passed`，`pending 0 not run` |
| E-2 | 71 round-trip 全绿 | **过** | `corpus=71 diffs=0`（roundtrip） |
| E-3 | 宿主两 profile 全绿 | **过（口径偏差）** | `--layer host` 26 fixture（12 shell + 14 agent）0 差异；卡面写 24 → §4 偏差 2 |
| E-4 | 全层 0 未解释差异，逐条带归属 | **过** | `total diffs: 0`；归属表在 `docs/reviews/diff/PH-21.md` §2 |
| E-5 | `tools/check.sh all` 退出 0 | **过** | §3.5 |
| E-6 | Python 参考实现未改动 | **过** | `git diff --quiet 4dd303d -- src/rill` rc=0 |
| E-7 | fixture 与 golden 未改动 | **不过（按卡面锚点）** | 锚点 `4dd303d` 之后有合法的 `.rill`→`.ri` 迁移（`19b0467`）；按「本相不改 golden」本意重锚到开工 HEAD 为 0。见 §4 偏差 3 |
| E-8 | 每项可独立验收 | **过** | §3 逐项贴原始输出 |

## 2. 任务逐项 verify（原始输出）

### 2.1 T1：CLI 统一与 SUT 配置

卡面 verify 写的是 `tools/check-0.1.0.sh --sut './ct/bin/rill_ct' --all`，但
harness 拒绝 `--all` 与 `--sut` 同用（见 §4 偏差 1）。实际按「全用例 + 全样例门禁」
两条命令各跑一次：

```bash
$ bash tools/check-0.1.0.sh --sut "$PWD/ct/bin/rill"
...
summary
  compliance: 83 passed, 0 failed, 0 blocked, 0 draft
  smoke:     2 passed, 0 failed, 0 blocked, 0 draft
  pending:   0 not run (A 0, B 0)
VERDICT: PASS (exit 0)
```

```bash
$ bash tools/check-0.1.0.sh --all
... pending: 0 not run (A 0, B 0)
VERDICT: PASS（Python 侧）
```

`--sut` 必须给绝对路径：fixture 会把 cwd 换到临时目录（见 §4 偏差 4）。

`tools/diff/sut.ct.json`：

```json
{"schema":"rill-sut/0","command":["./ct/bin/rill"],"artifact":"ct/bin/rill","build":"bash ct/build.sh"}
```

入口名在 PH-20 之后被统一改成 `ct/bin/rill`（`5923bdc`）；`ct/build.sh` 额外留了
`ct/bin/rill_ct -> rill` 软链，PH-19/PH-20 的脚本与文档不用改。

### 2.2 T2：71 个 round-trip

```bash
$ python3 tools/diff/diff.py --layer fmt --mode roundtrip
   corpus=71 diffs=0
   directed=3 direct_diffs=0 headers=2 header_diffs=0
   RESULT: PASS
```

### 2.3 T3：宿主双 profile

```bash
$ bash tools/check-0.1.0.sh --sut "$PWD/ct/bin/rill" --bucket host
  compliance: 1 passed, 0 failed ...
VERDICT: PASS
```

harness 的 `host` 桶只有 1 个聚合用例（`smoke/dual-profile` 的 AST 相等），真正的
26 个宿主 fixture 由 `diff.py --layer host` 驱动：

```bash
$ python3 tools/diff/diff.py --layer host --profile shell
   fixtures=12 diffs=0 directed=5 directed_diffs=0   RESULT: PASS
$ python3 tools/diff/diff.py --layer host --profile agent
   fixtures=14 diffs=0 directed=1 directed_diffs=0   RESULT: PASS
```

### 2.4 T4：全层对拍

```bash
$ python3 tools/diff/diff.py --layer all
== total diffs: 0
```

（四层 + fmt 三模式 + 宿主两 profile，逐层数字见 `docs/reviews/diff/PH-21.md` §1。）

### 2.5 T5 / T6：parity 与收口文档

```bash
$ test -s docs/planning/rill-0.1.0-ct-parity.md ; echo $?
0
$ test -s docs/reviews/closeout-21.md ; echo $?
0
```

### 2.6 E-5：项目总门禁

```bash
$ bash tools/check.sh all
disabled: g2 g3 g5 g7（依赖实现或 ACC/测试资产，当前启用必然失败）
== overall: PASS ==
```

`g2/g3/g5/g7` 是**项目治理门禁**（ACC 条目、构建清单、红证、依赖锁）长期关闭项，
与 0.1.0 行为判据无关，且在 PH-21 之前就是这样；不是本相引入。

### 2.7 E-6 / E-7

```bash
$ git diff --quiet 4dd303d -- src/rill ; echo $?
0
$ git diff --quiet 4dd303d -- testdata/0.1.0 ; echo $?
1                      # ← 见 §4 偏差 3
$ git diff --quiet HEAD -- testdata/0.1.0 ; echo $?
0                      # ← 本相没碰 golden
```

## 3. 与卡面偏差

| # | 卡面 | 实际 |
| --- | --- | --- |
| 1 | `check-0.1.0.sh --sut ... --all` | harness 明确拒绝二者同用（`FAIL --all 不能与筛选、--sut 或查看选项同用`）；拆成两条命令 |
| 2 | 「24 个 host fixture」 | 实际 12（shell）+ 14（agent）= **26**；且 harness 的 `host` 桶只聚合 1 例，26 例由 `diff.py --layer host` 驱动 |
| 3 | E-7 锚点 `4dd303d` | 该锚点之后有合法的 `.rill`→`.ri` 扩展名迁移（`19b0467`）与样例树迁移，literal diff 非空。按「PH-21 不改 golden」本意重锚到开工 HEAD：0 |
| 4 | `--sut './ct/bin/rill_ct'` 相对路径 | 必须是绝对路径，否则 fixture 换 cwd 后启动失败（`[Errno 2]`） |
| 5 | 交付物无「入口名」 | PH-20 后入口统一为 `ct/bin/rill`；`rill_ct` 保留为软链 |
| 6 | 规范版本 `1.9.0` | 仓库规范已升到 `1.10.0`（`96fb71c`），卡面未跟进 |
| 7 | version-minor `21` / `0.21.0` | 与 0.1.0 交付版本号不同源；本相不产物版本号、不打 tag |

## 4. 提交

- `feat(ct): PH-21-T1 CT CLI 统一与全层 --all`
- `docs(diff): PH-21-T4 全层差异报告`
- `docs(ct): PH-21-T5 parity 报告`
- `docs(review): PH-21-T6 收口对照表`

## 5. 下一相

CT 重写轨道到此收口。发布判定见 `docs/reviews/0.1.0-verdict.md`。
