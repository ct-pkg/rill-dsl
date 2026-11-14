# Shell profile：能力清单与 CLI 形态（PH-10）

> 规范正文见 `docs/RILL-0.1.0.md`（只读）。本文件只记录实现侧的映射与裁定，
> 缺口编号对应 `docs/phases/PH-10/card.md` §8。

## 1. 动词映射边界

真实宿主只认下表；表外动词一律 `E-RUN-VERB-UNREGISTERED`（stage=run），
不静默当作空操作。

| 动词 | 能力槽位.操作 | 输入 → 输出 | 需要 `allow` |
| --- | --- | --- | --- |
| `read` | `fs.read` | 路径 → 文本；非法 UTF-8 → `Bytes` | 是 |
| `write` | `fs.write` | 路径 + 内容（subject，缺省 `$`）→ 路径 | 是 |
| `run` | `process.run` | 命令字符串 → stdout；`host_meta.process` 带 code/stdout/stderr | 是 |
| `env` | `env.get` | 变量名 → 字符串 | 是 |
| `send` | `stdio.write` | 文本 → 写 stderr，值 = 文本 | 是 |
| `search` | — | 无真实映射 | 否 |
| `parse` / `replace` / `contains` / `review` | — | 无真实映射 | 否 |

`run` / `env` 从 PH-11 起两种宿主共用（`loader.SHELL_VERBS` / `loader.AGENT_VERBS`）；
差异回到能力实现，见 `docs/planning/rill-0.1.0-host-matrix.md`。parser 不感知宿主。

## 2. 能力清单（外部 manifest）

`--host-profile <path>` 指向一个 JSON：

```json
{
  "schema": "rill.shell-profile/0",
  "name": "shell-full",
  "allow": {
    "process": ["run"],
    "fs": ["read", "write"],
    "env": ["get"],
    "stdio": ["write"]
  },
  "exit_codes": {"ok": 0, "unhandled": 1}
}
```

- 缺省（不传 `--host-profile`）等于只读：`fs.read` + `env.get` + `stdio.write`，
  不起进程、不写文件。
- 未声明的操作直接拒绝：`E-HOST-CAPABILITY-DENIED` 诊断，消息里写明
  `slot.operation` 与声明位置，退出码 2。
- `exit_codes` 是退出码映射；`ok` 段成功、`unhandled` 段未处理失败。
  DSL 里不出现数字。
- 脚本无权声明授权（§五.1）：清单只能从 CLI 传入。

## 3. 值、stdio 与退出码

- 进程：`value` = stdout（UTF-8 文本；非法字节为 `Bytes`），
  `host_meta.process = {argv, code, stdout, stderr, timed_out}`；默认 10s timeout。
- `send`：写 stderr（`host_meta.stdio.channel = "stderr"`），避免污染
  `run` 的 JSON stdout 协议。
- `Bytes` 输出：CLI 序列化为 `{"$bytes": "<base64>"}`，不做有损替换。
- 未处理失败：DSL 层错误串仍是 `RILL DSL ERROR`（§4.10），
  但 `host_meta` 继续透传，进程 code/stderr 仍可观察。
- `--fakes`：假宿主优先，能力清单不参与，退出码保持 harness 协议（0/2/3）。

## 4. 与 Agent profile 的对照

| 维度 | Shell（PH-10） | Agent（PH-11） |
| --- | --- | --- |
| 主语/权限 | OS 用户 | 角色 + 权限 |
| 进程 | `process.run`，argv 由宿主切分 | 工具/任务调度 |
| 文件 | `fs.read/write`，cwd 相对解析 | 由工具决定 |
| env | 进程级快照，只读 | 由工具决定 |
| stdio | stderr 文本 | 会话/消息通道 |
| 退出码 | `exit_codes` 表 | 由引擎策略给出 |
| 真实宿主 | 已接（本 phase） | 已接（PH-11，工具注册表） |

两个 profile 的 AST 必须相同（`test_host_fixtures.py` 与
`tests/phase11/test_agent_fixtures.py` 逐 fixture 比对）。Agent 细节见
`docs/planning/rill-0.1.0-host-matrix.md`。

## 5. fixture 形态

`testdata/0.1.0/host/shell/<name>/` 下是 `script.rill` + `expect.json`，
故意不用 harness 的 `source.rill` / `case.json`：harness 的 run 用例总是注入
`--fakes`，无法覆盖真实宿主。fixture 由 `tests/phase10/test_host_fixtures.py`
在临时 cwd 里执行，不污染工作树。
