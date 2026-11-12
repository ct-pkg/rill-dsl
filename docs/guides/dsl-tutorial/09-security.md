# 09 安全

> 状态：`unverified`；依据 `docs/spec/dsl/06-security.md` 与 D-011..D-014。非规范性文档。

## 1. 三层白名单

| 层 | 时机 | 检查 | 失败 |
| --- | --- | --- | --- |
| 第一层 注册表 | 内核启动 + 加载 | 工具必须在可见 `ToolRegistry` 中 | `unknown_tool` |
| 第二层 脚本 header | 加载 | 调用工具 ∈ `# allow:`；事件 ∈ `# emit:` | `tool_not_allowed` / `event_not_declared` |
| 第三层 参数值 | 每次调用前 | 类型、路径等值约束全部通过 | `constraint`，handler 不执行 |

三层都通过才调用 handler；任一层失败都不产生副作用。固定 arity 工具的实参个数另在**加载期**静态校验：显式实参 + 管道值 + `$` 注入 ≠ 形参个数 → `arity`，不进入第三层。

## 2. 默认拒绝

`# allow:` 只有三种合法状态：

| 状态 | 有效工具集 | 处理 |
| --- | --- | --- |
| 无 `# allow:` | 空 | 加载拒绝 `no_allow_header` |
| `# allow: read, grep` | 列出的集合 | 正常 |
| `# allow: *` | 注册表全集 | 正常，但必须写审计记录 |

- `# allow:` 后列表为空，与不写 header 同义，拒绝。
- `# deny:` 单独出现（没有 `# allow:`）→ `deny_without_allow`，不得静默变成空集。
- `# deny:` 优先于 `# allow:`；deny 里的名字不必在 allow 中，冗余无副作用。
- header 每键最多出现一次；重复 → `dup_header`。
- `# dsl-version:` 不参与默认拒绝判定；没有 `# allow:` 仍然 `no_allow_header`。

```rill
# allow: read, grep, write

let text = read "notes.txt"
let hits = grep "TODO" text
write "todo.json" hits
```

反例与判据：

| 反例 | 结果 |
| --- | --- |
| 完全不写 `# allow:` | `no_allow_header`，任何工具都不执行 |
| `# allow:`（空列表） | 同 `no_allow_header` |
| 只写 `# deny: exec` | `deny_without_allow` |
| `# allow: read` 但调用 `write` | `tool_not_allowed`，错误列出 `Allowed tools: read` |

## 3. `# allow: *` 与 `# deny:`

```rill
# allow: *
# deny: exec
```

- `# allow: *` 表示「继承注册表全集」，加载成功，但必须产出一条审计记录：脚本路径、内容哈希、`policy_generation`、有效工具数、时间戳。
- `# deny: exec` 即使 `exec` 已注册也不可调用。
- `# allow: *` 把攻击面从「作者显式申请」扩大到「注册表里有什么就能用什么」；只在确有必要时使用，并优先写显式列表。

```rill
# allow: read, grep
# deny: grep
```

`grep` 不可调用；`read` 可调用。deny 是最终否决。

## 4. 参数约束在什么时候拒绝你

第三层约束在每次调用前执行，常见拒绝（`arity` 行是加载期例外，不在第三层）：

| 约束 | 例子 | `error_kind` |
| --- | --- | --- |
| 实参个数 ≠ 固定 arity | `read` 裸名、`x \|> read "p"`（2≠1） | `arity`（加载期，不是 `constraint`） |
| 实参类型不符 | `read 1`（path 不是 string） | `constraint` |
| 路径不在 root 界内 | `read "/workspace/../../etc/passwd"` | `constraint` |
| 路径经 symlink 逃出 root | `/workspace/link-to-etc/passwd` | `constraint` |
| 写不存在文件但父目录越界 | 父目录解析后不在 root | `constraint` |
| emit 超字节/深度 | payload 过大或过深 | `limit` |

路径规则（root 设为 `/workspace` 时）：

| 输入 | 结果 |
| --- | --- |
| `/workspace/a.txt` | 允许 |
| `/workspace/../../etc/passwd` | `constraint` |
| `/workspace/link-to-etc/passwd`（symlink → `/etc`） | `constraint` |
| `/workspace/link-to-sub/a.txt`（symlink → `/workspace/sub`） | 允许 |
| `/workspace-evil/x` | `constraint`（不能只做字符串前缀） |
| `/workspace/new.txt`（不存在，父目录存在） | 允许（写时解析父目录） |

相对路径以 workspace root 为基准，不以进程 cwd 为基准。判定对象是解析后的绝对路径；`..` 在打开前已消解；判定与打开同源，handler 不再解析原始字符串。

## 5. 约束错误不可被 `|?` 捕获

`constraint` 是第三层拒绝，属于不可捕获错误：

```rill
# allow: read

let text = read "/workspace/../../etc/passwd" |? "fallback"
```

`|?` 不会执行右侧；整个执行 `ok=0`、`error_kind=constraint`。这是安全要求：越权尝试不能被静默改写成正常结果。

## 6. 错误长什么样

```
src/run.rill:2:1: error: no '# allow:' header; tools are denied by default.
  Available: read, grep, write, json_parse, get
  Hint: add '# allow: read, grep' (or '# allow: *' with audit) at the top.
```

```
src/run.rill:5:10: error: tool 'write' is not allowed by script header.
  Allowed tools: read, grep
  Hint: add 'write' to '# allow:' or use an allowed tool.
```

```
src/run.rill:8:5: error: tool 'read' rejected path '/etc/passwd'.
  Constraint: path must resolve under '/workspace/'
  Hint: use a path under '/workspace/'.
```

格式固定：`path:line:col: error: message`，第二行详情，第三行 `Hint:`。行列 1 基，`col` 按 UTF-8 字节；同一次失败只报第一个错误。

## 7. 诚实边界

header 由脚本作者自书。默认拒绝阻止的是「无意识授权」和「静默扩大」，不阻止作者显式申请危险工具；外部授权主体不在本教程范围。
