# PH-19 收口：CT Shell 宿主（P7）

> 卡面 `docs/phases/PH-19/card.md`；差异报告 `docs/reviews/diff/PH-19.md`；
> 绕法登记 `docs/planning/rill-0.1.0-ct-defect-workarounds.md` §5–§7。
> 只本地提交，未 push、未打 tag。

## 1. 结论

阶段 GO。CT 版在 Shell profile 上跑通进程 / 文件 / env / stdio / 退出码五类能力，
12 个 Shell fixture 与 e2e 真脚本在**同一份期望断言**下两侧全绿；host 层新增对拍
`fixtures=12 diffs=0 directed=5 directed_diffs=0`；token/ast/error/eval 四层与
fmt 三层回归 0 差异。

沿用多单元架构，新增两个单元：

| 单元 | 内容 |
| --- | --- |
| `ct/src/host/host.h.ct` | `HRes`、`HostOps` 函数指针表、动词分派与参数校验 |
| `ct/src/host/shell.h.ct` | 策略加载、进程 / 文件 / env / stdio、退出码映射 |

没有为省槽做宏化或合并；每个能力是独立 `static` 函数。

**PH-16 E-5 只取得部分结论**：Bytes 已通过运行期用例验收；Opaque 在 Shell 宿主
没有任何入口，仍不通过（§5）。这会让 0.1.0 的最终判定不是全绿，见
`docs/reviews/closeout-21.md` 的完工判定。

## 2. 退出判据（E）

| ID | 条件 | 结果 | 证据 |
| --- | --- | --- | --- |
| E-1 | 12 个 Shell fixture 全部通过 | 通过 | `test_host_fixtures.py --sut ./ct/bin/rill_ct` PASS；host 层 `fixtures=12 diffs=0` |
| E-2 | `ProcessResult` 的 code/stdout/stderr 可观察；stdin 文本与二进制各 1 例 | 通过 | §4 的 12 例 + `process-stderr` / `text-run` / `bytes-run` 定向用例 |
| E-3 | 顶层未处理失败非 0；`[error]` 后按 profile 策略 | 通过 | `exit-fail` exit 1、两例能力拒绝 exit 2、其余 exit 0；逐例断言 |
| E-4 | 同一 fixture 在 shell/agent 的 AST 相等 | 通过 | `test_host_fixtures.py` 的 `check_ast`，12 例两侧相等 |
| E-5 | 没有 parser/lexer 改动 | 通过 | `git diff --quiet 89dcc3d -- ct/src/lexer ct/src/parser` → 0 |
| E-6 | 能力派发只用函数指针表，无指针接收者方法链 | 通过 | `grep -nE '\.get\(\)\.get\(' ct/src/host/*.ct` 为空；`ops->x(ops->ctx, …)` |
| E-7 | 任务清单每项可独立验收 | 通过 | §3 逐项贴原始输出 |
| PH-16 E-5 | `Bytes`/`Opaque` 可透传，不被 truthy 误判 | **部分通过** | Bytes：3 个 run 用例 + 5 个定向用例；Opaque：无入口，仍不通过（§5） |

## 3. 任务逐项 verify（原始输出）

卡面的 verify 命令有两处与仓库现状不符（`--bucket host` 只覆盖 1 个 smoke 例；
`--show host/...` 找不到用例），偏差见 §4；下表是该任务**等价且更强**的实际判据。

| 任务 | 实际 verify | 原始输出 |
| --- | --- | --- |
| T1 宿主接口 | `test -s ct/src/host/host.h.ct` | `rc=0` |
| T2 Shell 进程 | `test_host_fixtures.py --sut ./ct/bin/rill_ct`（process 两例） | `PASS`；host 层 `fixtures=12 diffs=0` |
| T3 文件与 env | 同上（fs/env 六例） | `PASS`；`fixtures=12 diffs=0` |
| T4 stdio 与退出码 | 同上（stdio/exit 四例） | `PASS`；两例 exit 2、一例 exit 1 逐例断言 |
| T5 host 对拍与报告 | `python3 tools/diff/diff.py --layer host --profile shell` | `fixtures=12 diffs=0 directed=5 directed_diffs=0` / `RESULT: PASS` |

四层与门禁（同一构建产物 `ct/bin/rill_ct`）：

```
token : sources=82 diffs=0  RESULT: PASS
ast   : sources=82 diffs=0  RESULT: PASS
error : sources=26 diffs=0  RESULT: PASS
eval  : sources=19 diffs=0  RESULT: PASS
fmt   : compress / display / roundtrip 均 corpus=71 diffs=0
ct/test.sh: PASS
== overall: PASS ==
```

## 4. 与卡面偏差

| # | 卡面 | 实际 | 影响 |
| --- | --- | --- | --- |
| 1 | `shell.m.ct` 放实现 | `.m.ct` 不能定义函数、不产生产物 | 实现与声明同在 `shell.h.ct`；判据不变 |
| 2 | T2/T3/T4 verify 用 `check-0.1.0.sh --bucket host` / `--show host/...` | harness 的 host 桶只有 1 个 smoke 例；12 例不在 harness 发现规则里 | 给 `test_host_fixtures.py` 加 `--sut`（不改期望），并新增 host 层对拍 |
| 3 | E-5 锚点 `v0.14.0` | 仓库 0 个 tag | 锚 `89dcc3d` |
| 4 | 依赖 PH-16 的 `Value` | CT 无 `Value` 类 | `J_BYTES` + `HRes.meta`；语义对齐，命名不同 |
| 5 | `run` 的 `--fakes` 只走伪宿主 | 旧 `cmd_run` 强制 `--fakes` | 本相去掉强制，接 `--host-profile` 与默认策略；fake 仍优先 |
| 6 | 二进制 stdin 有 fixture | fixture 语料没有 | host 层加定向用例，不改 fixture |
| 7 | T1–T4 各一次实现提交 | 四类能力共用一个 `shell.h.ct`，无法按文件边界拆成可编译的中间态 | 合并为一次实现提交（先例：PH-18-T1/T2/T3、PH-16-T1..T4），T5 单独 |
| 8 | 文本值即 UTF-8 文本 | 含 NUL 的合法 UTF-8 被判为 Bytes（C 串承载） | 语料未覆盖；登记为已知偏差，进 0.1.1 backlog |

## 5. PH-16 E-5 的诚实结论

- **Bytes**：宿主给了三条真实入口——`fs.read` 的非法 UTF-8、进程 stdout/stderr、
  进程 stdin。host 层用 `bytes-read`（原样 `{"$bytes": …}`）、`bytes-run`（二进制
  stdin 管道）、`bytes-truthy`（if 条件）覆盖；两侧 0 差异。CT 的 truthy 与 Python
  的对象语义一致（Bytes 默认 truthy），不是空串语义。
- **Opaque**：Shell 五类能力的返回值只有文本、Bytes、路径，没有任何宿主句柄。
  构造不出触发条件，按规则**不记通过、不挪判据**。要验收它必须等一个会返回句柄的
  宿主能力（agent 句柄 / 流 / PTY），不在本相范围。

所以 0.1.0 的准确性表述是：**Bytes 已验收，Opaque 未验收**；不能把 E-5 写成整条通过。

## 6. 新增值形态与兼容性

| 项 | 处理 |
| --- | --- |
| `J_BYTES` | `common.h.ct` 新增 tag；写出为 `{"$bytes": <base64>}`；truthy 恒真（对齐 Python 对象语义） |
| `json_parse` | 从 eval 上移到 common：能力清单与 fakes 共用一份实现 |
| `Eval.host` | 非空即走真实宿主；空则保持原来的 fake 队列路径，eval 层 19 例不变 |
| `read`/`write`/`run`/`env`/`send` | 参数校验顺序与 Python `ShellVerbRegistry._dispatch` 一致（先类型、后能力） |

## 7. 提交

```
feat(ct): PH-19-T1..T4 Shell 宿主五类能力
docs(diff): PH-19-T5 host 差异报告
docs(review): PH-19 收口
```

回滚：`git revert <实现提交>` 即回到 PH-18 收口状态；host 单元不被其他单元引用，
回滚不牵连 lexer/parser/loader/formatter。

## 8. 门禁末行

```
== overall: PASS ==
```

## 9. 下一相

PH-20（CT Agent 宿主）可以直接开工：`HostOps` 表已固定，agent 只需换一套
`ctx + 函数指针` 实现；PH-21 等待 PH-20。
