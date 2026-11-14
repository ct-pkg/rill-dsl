# rill-dsl

RILL 0.1.x 的参考实现：一个把工具调用写成空格句子的小语言，带 lexer、parser、
加载期校验、运行时、格式化器，以及 Shell / Agent 两个宿主 profile。

当前产品版本 **0.12.0**（`src/rill/__init__.py#__version__`）。语言规范正文在
[docs/RILL-0.1.0.md](docs/RILL-0.1.0.md)（0.1.1，只读）。

## 1. 环境

- macOS 或 Linux；不需要虚拟环境、不需要 `pip install`，只用 Python 标准库。
- Python 3.8+（`python3 --version` 可查）。
- 仓库根目录运行；没有 `pyproject.toml` / `setup.py`，用 `PYTHONPATH=src` 直接调
  `python3 -m rill`。
- 两个 profile 的 manifest 都是普通 JSON，路径由 `--host-profile` 给出。

## 2. 第一个脚本（Shell 宿主）

```console
$ cd <repo>
$ PYTHONPATH=src python3 -m rill run examples/quickstart/shell.rill \
    --profile shell --host-profile examples/quickstart/profiles/shell.json
{"ok": true, "value": "region=cn\nenv=prod\n", "error": null,
 "host_meta": {"stdio": {"channel": "stderr", "text": "region=cn\nenv=prod\n"}},
 "host": {"profile": "shell", "principal": {"kind": "os-user", "name": "<你的用户名>"}}}
$ echo $?
0
```

`send` 在 Shell 宿主下落 stderr，所以上面会先看到文件内容、再看到 JSON；JSON
始终在 stdout，退出码 0 表示脚本成功。

## 3. 第一个脚本（Agent 宿主）

```console
$ cd <repo>
$ PYTHONPATH=src python3 -m rill run examples/quickstart/agent.rill \
    --profile agent --host-profile examples/quickstart/profiles/agent.json
{"ok": true, "value": "region=cn\nenv=prod\n", "error": null,
 "host_meta": {"stdio": {"tool": "send", "channel": "tool", "text": "region=cn\nenv=prod\n"},
               "tool_meta": {"transport": {"kind": "process", "tool": "send",
                                           "pid": <子进程 pid>,
                                           "argv": ["python3", "../../testdata/0.1.0/host/agent/tools/tool_server.py"],
                                           "code": 0}}},
 "host": {"profile": "agent", "principal": {"kind": "role", "name": "engineer"}}}
$ echo $?
0
```

Agent 的 `read` / `send` 是真实子进程（`tool_meta.transport.pid` 可观察），不是
队列桩。manifest 的 `workspace` 相对**当前工作目录**解析：`examples/quickstart/
profiles/agent.json` 写的是 `examples/quickstart`，所以请从仓库根目录运行；
换目录时同步改 `workspace` 或改用绝对路径。

## 4. 文件怎么分工

| 路径 | 作用 |
| --- | --- |
| `examples/quickstart/shell.rill` | Shell 版：`<read> … |> <send> $ [to] user` |
| `examples/quickstart/agent.rill` | Agent 版：`engineer <read> file:config.txt …` |
| `examples/quickstart/profiles/shell.json` | Shell 能力清单：只读文件、读 env、写 stdio |
| `examples/quickstart/profiles/agent.json` | Agent manifest：role/roles/types/workspace/tools/limits |
| `examples/quickstart/profiles/tools.json` | 三个 `command` 工具，指向真实 `tool_server.py` |
| `examples/quickstart/config.txt` | 被读的配置 |

`file:` 是 Agent 的类型槽（`types.file = path`）；Shell 不拆类型，所以 Shell 版
直接写路径。

## 5. 其他命令

```console
$ PYTHONPATH=src python3 -m rill parse --dump-ast examples/quickstart/agent.rill
$ PYTHONPATH=src python3 -m rill check examples/quickstart/agent.rill --profile agent
$ PYTHONPATH=src python3 -m rill fmt examples/quickstart/agent.rill --display
```

`parse` / `check` / `run` 成功退出 0；诊断退出 2（stdout 是
`{"error": {stage, code, line, col, message}}`）；`run` 的未处理失败退出 1
（payload 仍是 `{"ok": false, ...}`）；`fmt` 成功 0、诊断 2。

## 6. 测试与门禁

```console
$ bash tools/check-0.1.0.sh --all      # 85 个 fixture；83 compliance + 2 smoke
$ bash tools/check-fmt.sh --roundtrip  # 压缩/展示往返
$ bash tools/check.sh all              # 文档/phase 卡/版本落点门禁
$ for f in tests/phase*/test_*.py; do python3 "$f" || exit 1; done
```

## 7. 已知边界

- 生产工具网关、审批、白名单、密钥注入未接；Agent 的 `run` 只在本机起子进程。
- Agent 不读真实 OS 环境变量，只读 manifest `context`；未处理失败固定退出 0，
  调用方要读 `payload.ok`。
- `parallel` 分支数与搜索深度未限流；独立 `[ok] $x {}` / `[error] $x {}` 未支持，
  用挂在前一条语句后的尾随块。
- 文档门禁有 7 份冻结正文/生成副本/历史档案按
  [DOC-S2 豁免登记表](docs/DOC-S2-waivers.md) 显式豁免，逐份打印理由。
- 完整清单见 [已知限制](docs/planning/rill-0.1.0-known-limits.md)。

## 8. 文档地图

| 层 | 位置 | 内容 |
| --- | --- | --- |
| 语言规范 | [docs/RILL-0.1.0.md](docs/RILL-0.1.0.md) | 0.1.1 正文（只读） |
| 阶段账 | [docs/phases/README.md](docs/phases/README.md) | PH-1…PH-12 卡与收口体系 |
| 能力矩阵 | [host-matrix](docs/planning/rill-0.1.0-host-matrix.md) | Shell / Agent 五槽差异 |
| 验收 | [acceptance](docs/planning/rill-0.1.0-acceptance.md) | 通过/失败/pending/host-specific |
| 完成度对账 | [completion-audit](docs/reviews/rill-0.1.0-completion-audit.md) | 12 张卡判据与替代锚点 |
| 收口 | [closeout-12](docs/reviews/closeout-12.md) | PH-12 收口与复测 |
