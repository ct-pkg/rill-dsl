# rill-dsl

RILL 0.1.x 的实现：一个把工具调用写成句子的小语言，带 lexer、parser、加载期校验、
运行时、最小格式化器（两端往返），以及 Shell / Agent 两个宿主 profile。

产品实现位于 `ct/`（自举实现，构建产物 `ct/bin/rill_ct`）。`src/rill/` 是 Python
参考实现，**只用于内部对拍与测试**，不是对外入口，也不在文档里作为语法或用法示例。

当前产品版本 **0.22.0**（`src/rill/__init__.py#__version__`；2026-11-15 重编号点）。语言规范正文在
[docs/RILL-0.1.0.md](docs/RILL-0.1.0.md)（0.1.1，只读）。

> 完成度口径：0.1.0 **不是 12 张卡全绿**。PH-5 的 `E-3`（fmt golden，三类长词）与
> `E-5`（`Bytes`/`Opaque` 格式化断言）已于 2026-11-15 裁定移出 0.1.0，转入
> [0.1.1 backlog](docs/planning/rill-0.1.1-backlog.md)，**不计通过**；PH-5 记 4/6。

## 1. 环境

- macOS 或 Linux；需要 ct 工具链（`ct` 在 `PATH`）与 C 编译器（`cc`）。
- 构建：`bash ct/build.sh`，产物是 `ct/bin/rill_ct`。运行脚本不需要 Python。
- 只有内部对拍与测试才需要 Python 3.8+（`src/rill`、`tools/rill_harness`）；
  没有 `pyproject.toml` / `setup.py`。
- 两个 profile 的 manifest 都是普通 JSON，路径由 `--host-profile` 给出。

## 2. 第一个脚本（Shell 宿主）

```console
$ cd <repo>
$ bash ct/build.sh          # 需要 ct 工具链与 cc；已构建可跳过
$ ./ct/bin/rill_ct run examples/quickstart/shell.ri \
    --profile shell --host-profile examples/quickstart/profiles/shell.json
region=cn
env=prod

{"ok":true,"value":"region=cn\nenv=prod\n","error":null,"host_meta":{"stdio":{"channel":"stderr","text":"region=cn\nenv=prod\n"}},"host":{"profile":"shell","principal":{"kind":"os-user","name":"<你的用户名>"}}}
$ echo $?
0
```

`send` 在 Shell 宿主下落 stderr，所以先看到文件内容、再看到 JSON；JSON 始终在
stdout，退出码 0 表示脚本成功。上面的 JSON 是实测输出，只有 `principal.name`
换成了占位符（它取本机 OS 用户名）。

## 3. 第一个脚本（Agent 宿主）

```console
$ ./ct/bin/rill_ct run examples/quickstart/agent.ri \
    --profile agent --host-profile examples/quickstart/profiles/agent.json
{"ok":true,"value":"region=cn\nenv=prod\n","error":null,"host_meta":{"stdio":{"tool":"send","channel":"tool","text":"region=cn\nenv=prod\n"},"tool_meta":{"transport":{"kind":"process","tool":"send","pid":<子进程 pid>,"argv":["python3","../../testdata/0.1.0/host/agent/tools/tool_server.py"],"code":0}}},"host":{"profile":"agent","principal":{"kind":"role","name":"engineer"}}}
$ echo $?
0
```

Agent 的 `read` / `send` 是真实子进程（`tool_meta.transport.pid` 可观察），不是
队列桩；`argv` 里的 `python3` 是**工具服务的实现进程**，与 RILL 语言本身无关。
manifest 的 `workspace` 相对**当前工作目录**解析：`examples/quickstart/profiles/
agent.json` 写的是 `examples/quickstart`，所以请从仓库根目录运行。

## 4. 样例在哪

| 位置 | 内容 | 怎么跑 |
| --- | --- | --- |
| [examples/tour/](examples/tour/) | 16 个按能力编号的样例：`send`/管道/`[into]`/`[map]`、`if`/`each`/`break`/`parallel`/`//fn`、错误路径、`fmt`、宿主能力与 `host_meta` | `cd examples/tour` 后按 [索引](examples/README.md) 里的命令逐条跑 |
| [examples/quickstart/](examples/quickstart/) | Shell / Agent 各一个最小脚本 + profile | 见本文 §2、§3 |

每个样例都配有同名 `.md`，写明演示什么、需要哪条语法，并贴了实测输出。索引见
[examples/README.md](examples/README.md)。

## 5. 文件怎么分工

| 路径 | 作用 |
| --- | --- |
| `ct/` | 产品实现（自举）；`ct/bin/rill_ct` 是 CLI |
| `src/rill/` | Python 参考实现，仅供内部对拍/测试，不对外 |
| `examples/tour/` | 16 个可跑样例与说明 |
| `examples/quickstart/shell.ri` | Shell 版：`<read> … |> <send> $ [to] user` |
| `examples/quickstart/agent.ri` | Agent 版：`engineer <read> file:config.txt …` |
| `examples/quickstart/profiles/shell.json` | Shell 能力清单：只读文件、读 env、写 stdio |
| `examples/quickstart/profiles/agent.json` | Agent manifest：role/roles/types/workspace/tools/limits |
| `examples/quickstart/profiles/tools.json` | 三个 `command` 工具，指向真实工具服务 |
| `examples/quickstart/config.txt` | 被读的配置 |

`file:` 是 Agent 的类型槽（`types.file = path`）；Shell 不拆类型，所以 Shell 版
直接写路径。

## 6. 其他命令

```console
$ ./ct/bin/rill_ct tokenize examples/quickstart/shell.ri
$ ./ct/bin/rill_ct parse --dump-ast examples/quickstart/agent.ri
$ ./ct/bin/rill_ct check examples/quickstart/agent.ri --profile agent
$ ./ct/bin/rill_ct fmt --display examples/quickstart/agent.ri
```

`parse` / `check` / `run` 成功退出 0；诊断退出 2（stdout 是
`{"error": {stage, code, line, col, message}}`）；`run` 的未处理失败退出 1
（payload 仍是 `{"ok": false, ...}`，但 Agent 真实传输固定退出 0，要读 `payload.ok`）；
`fmt` 成功 0、诊断 2。

## 7. 内部对拍（仅维护者）

对拍把 Python 参考实现与 `ct/bin/rill_ct` 放在同一批 fixture 上比结果，
用于验证两种实现没有漂移；它不是用户入口，也不产生对外示例：

```console
$ python3 tools/diff/diff.py --layer eval
$ bash tools/check-0.1.0.sh --all      # 85 个 fixture；83 compliance + 2 smoke
$ bash tools/check-fmt.sh --roundtrip  # 压缩/展示往返
$ bash tools/check.sh all              # 文档/phase 卡/版本落点门禁
```

已裁定的预期差异（如 PD-2 的两侧分歧）在
[解析期缺陷登记](docs/planning/rill-0.1.0-parser-defects.md) 里单独记账，不作为失败。

## 8. 已知边界

- 生产工具网关、审批、白名单、密钥注入未接；Agent 的 `run` 只在本机起子进程。
- Agent 不读真实 OS 环境变量，只读 manifest `context`；未处理失败固定退出 0，
  调用方要读 `payload.ok`。
- `parallel` 分支数与搜索深度未限流；独立 `[ok] $x {}` / `[error] $x {}` 未支持，
  用挂在前一条语句后的尾随块。
- 相邻拼接当前只支持「变量 / 映射引用在前」；引号串在前的写法与 `$"…"` 的
  已知问题见 [解析期缺陷登记](docs/planning/rill-0.1.0-parser-defects.md)。
- 文档门禁有 7 份冻结正文/生成副本/历史档案按
  [DOC-S2 豁免登记表](docs/DOC-S2-waivers.md) 显式豁免，逐份打印理由。
- 完整清单见 [已知限制](docs/planning/rill-0.1.0-known-limits.md)。

## 9. 文档地图

| 层 | 位置 | 内容 |
| --- | --- | --- |
| 语言规范 | [docs/RILL-0.1.0.md](docs/RILL-0.1.0.md) | 0.1.1 正文（只读） |
| 样例 | [examples/README.md](examples/README.md) | 16 个可跑样例的索引与实测输出 |
| 阶段账 | [docs/phases/README.md](docs/phases/README.md) | PH-1…PH-21 卡与收口体系 |
| 能力矩阵 | [host-matrix](docs/planning/rill-0.1.0-host-matrix.md) | Shell / Agent 五槽差异 |
| 验收 | [acceptance](docs/planning/rill-0.1.0-acceptance.md) | 通过/失败/pending/host-specific |
| 完成度对账 | [completion-audit](docs/reviews/rill-0.1.0-completion-audit.md) | 12 张卡判据、替代锚点与 PH-5 移出项 |
| 0.1.1 backlog | [backlog](docs/planning/rill-0.1.1-backlog.md) | 已裁定移出 0.1.0 的 `BL-001`/`BL-002` |
| 收口 | [closeout-12](docs/reviews/closeout-12.md) | PH-12 收口与复测 |
| CT 收口 | [closeout-13](docs/reviews/closeout-13.md) | PH-13 P1 收口（GO） |

历史档案（只作沿革参考，**不是当前语法依据**）：[docs/examples/](docs/examples/README.md)
与 [docs/guides/dsl-tutorial/](docs/guides/dsl-tutorial/README.md) 已迁移到
[examples/tour/](examples/tour/)；`docs/design/`、`docs/spec/`、`docs/review/` 是
v0.1 讨论稿与历史评审，按 DOC-S2 冻结。
