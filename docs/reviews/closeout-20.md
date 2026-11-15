# PH-20 收口：CT Agent 宿主（P8）

> 阶段判定：**GO**。host 层 agent 子集 14/14、0 差异；四层与 fmt / shell 宿主未回退。
> 差异报告：`docs/reviews/diff/PH-20.md`。

## 1. 结论

Agent profile 的工具/角色/limits 全部走 PH-19 的 `HostOps` 函数指针表，能力本体
不直接碰 OS：`read`/`write` 经 `read`/`write` 工具，`run` 经 `run`/`exec` 工具，
`send` 经 `send`/`emit` 工具，`env` 读 manifest 的 `context`。角色预校验在 eval
之前按 AST 字面主语做；limits 是 steps/time_ms/bytes 三项。

本相唯一的新阻塞是工具链的「已解析调用点」全局 1024 上限（PH-19 收口时已用 927），
处置为两段 `ct build`：语言核心出静态库，宿主层消费。**不改工具链、不改判据。**

## 2. 退出判据（E）

| ID | 条件 | 结果 | 证据 |
| --- | --- | --- | --- |
| E-1 | 14 个 Agent fixture 全过 | **过** | `--layer host --profile agent`：`fixtures=14 diffs=0`；`phase11 --sut` PASS |
| E-2 | 同源 fixture AST 与 Shell 相等 | **过** | `phase11` 的 `check_ast()` 逐例比两 profile 的 AST |
| E-3 | `[error]` 的 `$` 仍是字符串 | **过** | `fs-outside`：`"error": "RILL DSL ERROR"`，结构化错误在 `host_meta.fs` |
| E-4 | JSON 可被标准解析器接受 | **过** | `rill_ct run ... \| python3 -m json.tool` rc=0 |
| E-5 | 没有 parser/lexer 改动 | **过** | `git diff --stat HEAD -- ct/src/lexer ct/src/parser` 输出为空 |
| E-6 | host 层 14/14，0 未解释差异 | **过** | `docs/reviews/diff/PH-20.md` §1、§5 |
| E-7 | 任务项各自可验收 | **过** | 本文 §3 |

## 3. 任务逐项 verify（原始输出）

### T1 / T4：Agent 能力映射与 fixture 对齐

```bash
$ python3 tools/diff/diff.py --layer host --profile agent
== layer=host profile=agent
   python: python3 -m rill
   ct    : /Users/samxx/trae-ws/rill-dsl/./ct/bin/rill_ct
   fixtures=14 diffs=0 directed=1 directed_diffs=0
   RESULT: PASS
```

```bash
$ python3 tests/phase11/test_agent_fixtures.py
PASS phase11 fixtures: agent 五类能力 + role/limits/type + AST 一致

$ python3 tests/phase11/test_agent_fixtures.py --sut './ct/bin/rill_ct'
PASS phase11 fixtures: agent 五类能力 + role/limits/type + AST 一致
```

### T2：角色与 limits

```bash
$ cat testdata/0.1.0/host/agent/role-denied/expect.json | head -8
  "capability": "role", "outcome": "failure", "expect": {"exit": 2, ...}
```

`role-denied` 走 `ag_validate_program` 的角色预校验 → `run` 诊断 exit 2；
`limit-steps` 走 `ag_limits_before` → `ok=false` + `host_meta.limits`。两例都在
上面的 14 例对拍里，0 差异。

### T3：最小 JSON

卡面写的 `--layer json` 不存在（见 §4 偏差 3），可解析性由 E-4 覆盖：

```bash
$ ./ct/bin/rill_ct run testdata/0.1.0/host/agent/fs-outside/script.rill \
    --profile agent --host-profile testdata/0.1.0/host/agent/profiles/agent.json \
    | python3 -m json.tool > /dev/null
$ echo $?
0
```

`ct/src/json/json.h.ct` 提供两条写出路径：`json_compact`（CLI 信封，`,`/`:` 无空格）
与 `json_text`（Python `json.dumps(ensure_ascii=False, sort_keys=True)` 风格，
工具请求与 bytes 观测用）。

### T5：差异报告与 workarounds

```bash
$ python3 tools/diff/diff.py --layer host --profile agent | tail -2
   fixtures=14 diffs=0 directed=1 directed_diffs=0
   RESULT: PASS
```

`docs/planning/rill-0.1.0-ct-defect-workarounds.md` §8 记录了 1024 调用点的实测与
两段构建的取舍。

## 4. 与卡面偏差

| # | 卡面 | 实际 |
| --- | --- | --- |
| 1 | `agent.m.ct` / `json.m.ct` | `.m.ct` 不能定义函数；落成 `agent*.h.ct` + `json/json.h.ct` |
| 2 | `ct/src/json.h.ct` | 在 `ct/src/json/json.h.ct`（多单元按目录分） |
| 3 | T3 verify `--layer json` | `diff.py` 无此层；用 E-4 的 `json.tool` + host 层全量字段比对 |
| 4 | E-5 `v0.14.0` tag | 该 tag 不存在（PH-19 已登记）；改用 `HEAD` |
| 5 | 交付物无构建层 | 新增 `ct/src/host/bridge.h`、两段 `ct/build.sh`、`ct/build/gen-lib/` |
| 6 | driver 固定 `python3 -m rill` | 给 `tests/phase11/test_agent_fixtures.py` 加 `--sut`（期望不动） |
| 7 | `--bucket host` | 不存在；用 `--layer host --profile agent` + phase11 脚本 |

第 5 条是「1024 调用点」阻塞的必要处置，不是判据变更：调用点总量不变、lexer/parser
不改、对拍口径不变，只是把一次编译拆成两次。

## 5. 新增/修改的值形态

- `J_FLOAT` / `J_BYTES` 已在 PH-19 引入；本相补 `json_text` 的 `{"$bytes": ...}` 与
  工具响应的 `$bytes` 解码（`ag_decode`）。
- Agent 工具响应必须是 `{"ok": bool, "value"?, "error"?}`；缺失/非布尔 `ok` 报
  `E-HOST-TOOL-TRANSPORT`，未注册工具报 `E-HOST-TOOL-UNREGISTERED`。
- `host_meta.tool_meta.transport.pid` 是真实进程号，对拍时按 `span` 同类处理剔除
  （保留在输出里）。

## 6. 提交

- `feat(ct): PH-20-T1..T4 Agent 宿主与最小 JSON`
- `docs(diff): PH-20-T5 Agent 差异报告`

## 7. 门禁末行

```
ct/test.sh: PASS
== overall: PASS ==
```

## 8. 下一相

PH-21（0.1.0 完工判定）可开工。
